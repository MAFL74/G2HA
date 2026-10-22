import asyncio
import base64
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


@app.get("/", response_class=HTMLResponse)
async def home() -> HTMLResponse:
    """Open the useful G2HA dashboard from the add-on sidebar/Web UI."""
    return HTMLResponse(
        "<!doctype html><html><head><meta charset='utf-8'><title>G2HA Relay</title>"
        "<style>body{font-family:system-ui,sans-serif;margin:3rem;background:#111;color:#eee}"
        "a{color:#4fc3f7}</style></head><body><h1>G2HA Relay</h1>"
        "<p>Opening the G2HA dashboard…</p>"
        "<p><a id='dashboard' href='/g2ha-dashboard/g2ha'>Open G2HA dashboard</a></p>"
        "<script>"
        "const dashboard=location.port==='8000'"
        "?location.protocol+'//'+location.hostname+':8123/g2ha-dashboard/g2ha'"
        ":location.origin+'/g2ha-dashboard/g2ha';"
        "document.getElementById('dashboard').href=dashboard;"
        "window.top.location.replace(dashboard);"
        "</script></body></html>"
    )


@app.get("/status", response_class=HTMLResponse)
async def status_page() -> HTMLResponse:
    """Provide the direct relay status page without redirecting to the dashboard."""
    return HTMLResponse(
        "<!doctype html><html><head><meta charset='utf-8'><title>G2HA Relay status</title>"
        "<style>body{font-family:system-ui,sans-serif;margin:3rem;background:#111;color:#eee}"
        "a{color:#4fc3f7}</style></head><body><h1>G2HA Relay</h1>"
        "<p>Relay is running.</p><p>Health: <a href='/health'>/health</a></p>"
        "<p><a href='/g2ha-dashboard/g2ha'>Open G2HA dashboard</a></p></body></html>"
    )


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "environment": os.getenv("G2HA_ENV", "development"), "instances": str(len(relay_state.instances)), "devices": str(sum(len(item.devices) for item in relay_state.instances.values()))}


@app.get("/auth/authorize", response_class=HTMLResponse)
async def authorize(request: Request, response_type: str, client_id: str, redirect_uri: str, state: str = "", scope: str = "", login_hint: str = ""):
    if response_type != "code":
        raise HTTPException(400, "Only response_type=code is supported")
    html = f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
  <title>Connect Google Home to G2HA</title>
  <style>
    :root {{ color-scheme: dark; font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; min-height: 100svh; display: grid; place-items: center; padding: 24px 16px; background: #101216; color: #f4f5f7; }}
    main {{ width: min(100%, 520px); padding: clamp(24px, 6vw, 44px); border: 1px solid #30343d; border-radius: 24px; background: #1b1e24; box-shadow: 0 18px 60px #0006; }}
    .brand {{ display: flex; align-items: center; gap: 12px; margin-bottom: 28px; color: #8ecbff; font-size: 1.05rem; font-weight: 700; letter-spacing: .02em; }}
    .brand-mark {{ display: grid; place-items: center; width: 42px; height: 42px; border-radius: 12px; background: #087db4; color: white; font-size: 1.2rem; }}
    h1 {{ margin: 0 0 10px; font-size: clamp(1.65rem, 5vw, 2.2rem); line-height: 1.15; }}
    .intro {{ margin: 0 0 28px; color: #c4c9d2; font-size: 1rem; line-height: 1.5; }}
    form {{ display: grid; gap: 18px; }}
    label {{ display: grid; gap: 8px; color: #e5e8ee; font-size: 1rem; font-weight: 650; }}
    input {{ width: 100%; min-height: 54px; padding: 13px 15px; border: 1px solid #5b6472; border-radius: 12px; background: #111318; color: #fff; font: inherit; font-size: 16px; }}
    input:focus {{ outline: 3px solid #55b9f5; outline-offset: 2px; border-color: #9bdcff; }}
    button {{ min-height: 56px; margin-top: 4px; border: 0; border-radius: 14px; background: #0aa4d8; color: #fff; font: inherit; font-size: 1.05rem; font-weight: 750; cursor: pointer; }}
    button:active {{ transform: translateY(1px); }}
    .privacy {{ margin: 24px 0 0; color: #aab1bc; font-size: .9rem; line-height: 1.45; }}
    @media (max-width: 420px) {{ body {{ padding: 12px; }} main {{ border-radius: 18px; }} }}
  </style>
</head>
<body>
  <main>
    <div class="brand"><span class="brand-mark" aria-hidden="true">⌂</span><span>G2HA Relay</span></div>
    <h1>Connect Google Home</h1>
    <p class="intro">Sign in with your G2HA account to allow Google Home to access your selected devices.</p>
    <form method="post" action="/auth/authorize/submit">
      <input type="hidden" name="client_id" value="{escape(client_id)}">
      <input type="hidden" name="redirect_uri" value="{escape(redirect_uri)}">
      <input type="hidden" name="state" value="{escape(state)}">
      <label for="username">Username<input id="username" name="username" autocomplete="username" autocapitalize="none" spellcheck="false" required></label>
      <label for="password">Password<input id="password" name="password" type="password" autocomplete="current-password" required></label>
      <button type="submit">Allow Google Home</button>
    </form>
    <p class="privacy">You can change which devices are exposed later in Home Assistant.</p>
  </main>
</body>
</html>'''
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
    client_id = str(form.get("client_id", "") or request.query_params.get("client_id", ""))
    if not client_id:
        authorization = request.headers.get("authorization", "")
        if authorization.lower().startswith("basic "):
            try:
                credentials = base64.b64decode(authorization[6:].strip()).decode("utf-8")
                client_id = credentials.split(":", 1)[0]
            except (ValueError, UnicodeDecodeError):
                client_id = ""
    configured_client_id = os.getenv("G2HA_OAUTH_CLIENT_ID", "")
    if configured_client_id and not client_id:
        _LOGGER.warning("OAuth token request did not include a client_id")
        raise HTTPException(401, "Unknown OAuth client")
    # Google Home's assigned OAuth client ID is separate from a Google Cloud
    # OAuth credential ID. Keep accepting the latter for existing add-ons while
    # binding every code/token exchange to the client ID in the authorization code.
    if configured_client_id and client_id != configured_client_id and not configured_client_id.endswith(".apps.googleusercontent.com"):
        _LOGGER.warning("OAuth token request used an unregistered client_id")
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

