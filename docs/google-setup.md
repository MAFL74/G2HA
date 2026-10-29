# Google Home setup

G2HA connects Google Home's cloud-to-cloud smart home service to a G2HA relay. The relay needs a stable public HTTPS address that Google can reach.

## Before you start

- Deploy the G2HA relay and verify its health endpoint.
- Configure a valid TLS certificate and public DNS for the relay.
- Set the OAuth values required by the relay using its supported deployment configuration. Keep client secrets and passwords out of Git and screenshots.
- Install and configure the G2HA integration in Home Assistant, and confirm that its relay connection is connected.
- Decide which entities or areas should be exposed to Google Home.

## Configure the Google Home project

Create or select a Cloud-to-cloud project in the Google Home Developer Console and configure its account-linking and fulfillment endpoints to point to your relay. The endpoint paths are:

- Authorization: `/auth/authorize`
- Token: `/auth/token`
- Fulfillment: `/api/google_assistant`

Use the public HTTPS base URL of your own relay, for example `https://your-relay.example.com`, followed by the relevant path. Configure the OAuth client and redirect URI exactly as required by the Google console and the relay deployment. Google console requirements can change; follow the current console validation and official Google documentation.

## Link an account

Enable or publish the integration in the Google Home Developer Console according to Google's current testing workflow. Open the Google Home app, add the G2HA test or production service, and complete account linking with the credentials configured for the relay. Select the Home Assistant instance represented by the relay account if prompted, then run a device sync.

## Verify the setup

1. Confirm that the G2HA integration reports `connected` in Home Assistant.
2. Review its `Found supported entities`, `Filtered entities`, and `Synced devices` diagnostics.
3. Request a device sync in Google Home and confirm that exposed devices appear.
4. Test a harmless query and an on/off or other supported command.
5. Inspect sanitized relay and Home Assistant logs if a request fails.

Do not share OAuth credentials, access tokens, Home Assistant URLs that include tokens, or raw diagnostics without reviewing them for private entity and room names.

