import asyncio
import os
import uuid
import logging
from html import escape
from urllib.parse import urlencode
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Form, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, RedirectResponse

from .google import query_response, sync_response
from .models import HAEnvelope
from .state import relay_state
from .oauth import OAuthStore, valid_login

_LOGGER = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield


app = FastAPI(title="G2HA", version="0.1.0", lifespan=lifespan)
oauth = OAuthStore(os.getenv("G2HA_OAUTH_DB", "/var/lib/g2ha/oauth.sqlite3"))


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "environment": os.getenv("G2HA_ENV", "development"), "instances": str(len(relay_state.instances)), "devices": str(sum(len(item.devices) for item in relay_state.instances.values()))}


@app.get("/auth/authorize", response_class=HTMLResponse)
async def authorize(request: Request, response_type: str, client_id: str, redirect_uri: str, state: str = "", scope: str = "", login_hint: str = ""):
    if response_type != "code":
        raise HTTPException(400, "Only response_type=code is supported")
    html = f'''<html><body><h2>G2HA account linking</h2><form method="post" action="/auth/authorize/submit">
    <input type="hidden" name="client_id" value="{escape(client_id)}"><input type="hidden" name="redirect_uri" value="{escape(redirect_uri)}"><input type="hidden" name="state" value="{escape(state)}">
    <label>Username <input name="username" autocomplete="username"></label><br><label>Password <input type="password" name="password" autocomplete="current-password"></label><br><button>Allow Google Home</button></form></body></html>'''
    return HTMLResponse(html)

@app.post("/auth/authorize/submit")
async def authorize_submit(client_id: str = Form(...), redirect_uri: str = Form(...), state: str = Form(""), username: str = Form(...), password: str = Form(...)):
    if not valid_login(username, password):
        raise HTTPException(401, "Invalid G2HA credentials")
    # The current relay exposes one Home Assistant instance as "home".
    # OAuth must bind Google Home to that same instance, otherwise SYNC
    # authenticates successfully but returns an empty device list.
    params = {"code": oauth.create_code("home", client_id, redirect_uri)}
    if state:
        params["state"] = state
    return RedirectResponse(f"{redirect_uri}?{urlencode(params)}", status_code=303)


@app.post("/auth/token")
async def token(request: Request):
    form = await request.form()
    client_id = str(form.get("client_id", ""))
    if os.getenv("G2HA_OAUTH_CLIENT_ID") and client_id != os.getenv("G2HA_OAUTH_CLIENT_ID"):
        raise HTTPException(401, "Unknown OAuth client")
    if form.get("grant_type") == "authorization_code":
        result = oauth.exchange_code(str(form.get("code", "")), client_id, str(form.get("redirect_uri", "")))
        if not result:
            raise HTTPException(400, "Invalid or expired authorization code")
        access, refresh = result
        return {"token_type": "Bearer", "access_token": access, "refresh_token": refresh, "expires_in": 3600}
    if form.get("grant_type") == "refresh_token":
        access = oauth.refresh_access(str(form.get("refresh_token", "")), client_id)
        if not access:
            raise HTTPException(400, "Invalid refresh token")
        return {"token_type": "Bearer", "access_token": access, "expires_in": 3600}
    raise HTTPException(400, "Unsupported grant_type")


@app.post("/api/google_assistant")
async def google_assistant(request: Request) -> dict[str, Any]:
    body = await request.json()
    request_id = body.get("requestId", str(uuid.uuid4()))
    auth = request.headers.get("authorization", "")
    instance_id = oauth.validate_access(auth[7:]) if auth.lower().startswith("bearer ") else None
    if os.getenv("G2HA_ENV", "development") != "production":
        instance_id = instance_id or request.headers.get("x-g2ha-instance") or body.get("payload", {}).get("agentUserId")
    if not instance_id:
        raise HTTPException(401, "Missing linked G2HA instance")
    instance = relay_state.get(instance_id)

    intents = body.get("inputs", [])
    intent = intents[0].get("intent") if intents else None
    if intent == "action.devices.SYNC":
        return sync_response(request_id, instance_id, list(instance.devices.values()))
    if intent == "action.devices.QUERY":
        ids = body["inputs"][0]["payload"].get("devices", [])
        states = {item["id"]: instance.devices[item["id"]].state for item in ids if item["id"] in instance.devices}
        return query_response(request_id, states)
    if intent == "action.devices.EXECUTE":
        return await execute(request_id, instance_id, body["inputs"][0]["payload"])
    if intent == "action.devices.DISCONNECT":
        relay_state.instances.pop(instance_id, None)
        return {}
    raise HTTPException(400, f"Unsupported intent: {intent}")


async def execute(request_id: str, instance_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    instance = relay_state.get(instance_id)
    if instance.websocket is None:
        return {"requestId": request_id, "payload": {"commands": [{"ids": [], "status": "OFFLINE"}]}}
    future = asyncio.get_running_loop().create_future()
    instance.pending[request_id] = future
    try:
        await instance.websocket.send_json({"type": "execute", "request_id": request_id, "payload": payload})
    except Exception:
        instance.pending.pop(request_id, None)
        _LOGGER.exception("Could not send EXECUTE to HA instance %s", instance_id)
        return {"requestId": request_id, "payload": {"commands": [{"ids": [], "status": "OFFLINE"}]}}
    try:
        return {"requestId": request_id, "payload": {"commands": await asyncio.wait_for(future, timeout=15)}}
    except asyncio.TimeoutError:
        return {"requestId": request_id, "payload": {"commands": [{"ids": [], "status": "ERROR"}]}}
    finally:
        instance.pending.pop(request_id, None)


@app.websocket("/api/v1/ha/ws")
async def ha_ws(websocket: WebSocket, instance_id: str):
    await websocket.accept()
    instance = relay_state.get(instance_id)
    instance.websocket = websocket
    try:
        while True:
            raw_message = await websocket.receive_json()
            _LOGGER.info("G2HA HA message type=%s", raw_message.get("type"))
            envelope = HAEnvelope.model_validate(raw_message)
            if envelope.type == "hello":
                await websocket.send_json({"type": "hello_ack"})
            elif envelope.type == "devices" and envelope.devices is not None:
                relay_state.set_devices(instance_id, envelope.devices)
            elif envelope.type == "state" and envelope.device_id in instance.devices:
                instance.devices[envelope.device_id].state = envelope.payload
            elif envelope.type == "result" and envelope.request_id in instance.pending:
                if not instance.pending[envelope.request_id].done():
                    instance.pending[envelope.request_id].set_result(envelope.payload.get("commands", []))
    except WebSocketDisconnect:
        relay_state.disconnect(instance_id, websocket)
    except Exception:
        _LOGGER.exception("G2HA HA WebSocket failed for instance %s", instance_id)
        relay_state.disconnect(instance_id, websocket)

