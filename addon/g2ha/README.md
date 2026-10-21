# G2HA

G2HA is a minimal, self-hosted relay between Google Home Cloud-to-cloud and Home Assistant.

## Project structure

- `home_assistant/custom_components/g2ha/` — Home Assistant-integrasjonen
- `relay/g2ha/` — selvhostet HTTPS/OAuth/Google-relay
- `docs/` — arkitektur, installasjon, OAuth og feilsøking
- `deploy/` — systemd- og IIS-oppsett

## Current draft

- FastAPI HTTP service
- Google Smart Home `SYNC`, `QUERY`, `EXECUTE`, and `DISCONNECT` handlers
- WebSocket endpoint for Home Assistant clients
- In-memory device registry and connection manager
- OAuth endpoint placeholders with explicit setup errors
- No credentials or secrets in the repository

This is a protocol skeleton, not production-ready hosting. It is intended to validate the relay contract locally before adding persistent storage, real OAuth, TLS, and deployment.

## Run

```powershell
py -m venv .venv
.\.venv\Scripts\python -m pip install -e .
Copy-Item .env.example .env
\.venv\Scripts\python -m uvicorn g2ha.app:app --reload
```

Health check: `http://127.0.0.1:8000/health`

## Protocol draft

The Home Assistant side connects to `/api/v1/ha/ws?instance_id=...` and sends a `hello` message followed by device snapshots. Google requests are routed to the matching instance and returned as `query_result` or `execute_result` messages. The WebSocket adapter is intentionally small so it can later be implemented as a Home Assistant custom integration.

See `docs/protocol.md` for the message contract and `docs/google-setup.md` for the remaining Google Cloud configuration.
