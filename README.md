# G2HA

G2HA is an independent, self-hosted bridge between Google Home and Home Assistant. It consists of a Home Assistant custom integration and a relay service that handles Google Home's cloud-to-cloud requests.

G2HA is a community project. It is not affiliated with, endorsed by, or supported by Nabu Casa or the Open Home Foundation. Home Assistant is a trademark of the Open Home Foundation.

## How it works

```text
Google Home / Google Assistant
          | HTTPS: account linking and smart home intents
          v
     G2HA relay
          ^
          | Outbound WebSocket from Home Assistant
          |
 Home Assistant + G2HA integration
```

The Home Assistant integration opens an outbound WebSocket to the configured relay. This lets the relay send device commands back over the same connection without requiring an inbound connection to Home Assistant. The integration discovers supported entities, applies the configured exposure choices, and sends device snapshots and state updates to the relay. The relay answers Google Home requests by querying Home Assistant or forwarding commands through that WebSocket.

## Repository layout

- `home_assistant/custom_components/g2ha/` — Home Assistant integration.
- `addon/g2ha/` — Home Assistant add-on packaging for running the relay on Home Assistant OS.
- `relay/` — relay service source used for standalone hosting.
- `docs/` — architecture, setup, and protocol documentation.
- `tests/` — relay and capability tests.

## Features

- Google Smart Home `SYNC`, `QUERY`, `EXECUTE`, and `DISCONNECT` request handling.
- OAuth account-linking endpoints for connecting Google Home accounts.
- A relay-side device and connection registry, with OAuth codes and token hashes stored by the relay.
- Home Assistant entity discovery and state updates over WebSocket.
- Entity, area, and all-supported-entity exposure choices, depending on integration version and configuration.
- Diagnostic sensors for connection, relay address, synchronization, supported entities, and device counts.
- A Home Assistant add-on option for self-hosting the relay.

Supported entity domains and Google traits depend on the integration version and the entity's attributes. See [integration behavior and diagnostics](docs/integration.md) for details.

## Installation overview

1. Deploy the relay with a publicly reachable HTTPS endpoint and configure its OAuth credentials.
2. Add the G2HA integration to Home Assistant and enter the relay WebSocket URL and a stable instance ID.
3. Choose which supported entities or areas to expose.
4. Configure the Google Home Developer Console project to use the relay's authorization, token, and fulfillment endpoints.
5. Link the service in the Google Home app.

Detailed guides:

- [Architecture and data flow](docs/architecture.md)
- [Home Assistant integration, exposure, and diagnostics](docs/integration.md)
- [Google Home setup](docs/google-setup.md)
- [WebSocket protocol](docs/protocol.md)

## Security and privacy

The relay must be reachable by Google over HTTPS for cloud-to-cloud fulfillment. Protect the relay and its OAuth configuration, use strong unique credentials, and do not commit secrets, tokens, private keys, or live instance credentials. Home Assistant initiates the WebSocket connection to the relay. Review the relay hosting and network configuration before exposing it to the internet.

## Project status

G2HA is independently maintained. Google Home, Home Assistant, and hosting environments can change, so compatibility may vary. Report issues with relevant versions and sanitized logs; remove access tokens, passwords, instance identifiers, and other private data before sharing diagnostics.

## License

This repository does not currently include a license file. Unless and until one is added, do not assume that the source is available for reuse, modification, or redistribution.

