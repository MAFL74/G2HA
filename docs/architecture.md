# Architecture and data flow

G2HA has two main runtime components: a Home Assistant custom integration and a relay service. The relay can be hosted separately or through the Home Assistant add-on package.

## Components

1. **Home Assistant integration** runs in Home Assistant Core. It discovers and maps supported entities, applies exposure settings, sends inventory and state updates, and executes commands received from the relay.
2. **G2HA relay** exposes the Google Smart Home fulfillment and account-linking endpoints over HTTPS. It maintains active Home Assistant connections and routes Google requests to the matching instance.
3. **Google Home** links to the relay and sends device synchronization, query, execution, and disconnect requests.

## Request and state flow

```text
Home Assistant integration -- outbound WebSocket --> G2HA relay <-- HTTPS -- Google Home
Home Assistant integration <-- command/result messages --> G2HA relay
```

The integration initiates the WebSocket connection, so Home Assistant does not need an inbound port opened for G2HA. The relay must be reachable over HTTPS by Google's cloud service.

- At connection time, Home Assistant identifies its instance and publishes its synchronized device snapshot.
- State changes are sent to the relay so Google queries can be answered with current data.
- Google `SYNC` requests receive the relay's current device inventory.
- Google `QUERY` requests are routed to Home Assistant and answered using its current entity states.
- Google `EXECUTE` commands are forwarded over the WebSocket, converted to Home Assistant service calls, and returned with their execution result.
- Google `DISCONNECT` updates the linked account or instance state on the relay.

The WebSocket message shapes are documented in [protocol.md](protocol.md). Entity mapping and exposure rules are described in [integration.md](integration.md).

## Hosting choices

- **Home Assistant add-on:** run the relay as an add-on on a supported Home Assistant OS installation.
- **Standalone relay:** run the relay service on a separate host and expose it through a correctly configured HTTPS reverse proxy or web server.

In either setup, protect OAuth credentials and relay configuration, keep the endpoint available to Google, and avoid exposing administrative interfaces unnecessarily. See [google-setup.md](google-setup.md) for Google project configuration.

