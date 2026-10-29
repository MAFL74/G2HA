# G2HA Relay Home Assistant add-on

The G2HA Relay add-on runs the relay service on Home Assistant OS. It is one hosting option for the relay; the G2HA custom integration still needs to be installed and configured in Home Assistant.

## What the add-on does

The relay accepts Google Home cloud-to-cloud HTTPS requests and maintains the connection to the Home Assistant integration. Home Assistant initiates an outbound WebSocket connection to the relay. The add-on exposes the relay's configured HTTP port and provides an ingress web interface.

## Configuration

Configure the add-on options in Home Assistant before starting it:

- `environment`: runtime environment name.
- `oauth_username`: OAuth account-linking username expected by this relay configuration.
- `oauth_password`: OAuth account-linking password. Use a strong, unique value.
- `oauth_client_id`: OAuth client identifier used by the relay's token exchange configuration.

Keep credentials private. Do not paste the add-on options, secrets, or tokens into public issues or repository files.

After starting the add-on, configure the G2HA Home Assistant integration with the relay's WebSocket URL and a stable instance ID. For Google Home, the relay must also be reachable at a public HTTPS URL with valid TLS; a local add-on port alone is not sufficient for Google's cloud service.

See the repository's [Google Home setup guide](../../docs/google-setup.md) and [architecture overview](../../docs/architecture.md).

