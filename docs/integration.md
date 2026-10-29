# Home Assistant integration

The G2HA integration runs inside Home Assistant. It discovers entities that it can map to Google Smart Home device types, converts their state and supported capabilities, and keeps the relay up to date.

## Connection and synchronization

During setup, G2HA opens an outbound WebSocket connection to the configured relay URL. The integration sends an initial device snapshot, then sends state changes as they happen. It also periodically checks for inventory changes and republishes the device list when needed. Commands received from Google are translated into Home Assistant service calls and returned to Google through the relay.

The Home Assistant instance ID identifies this connection to the relay. Keep it stable for the same Home Assistant installation. It is not a password, but avoid posting it publicly with diagnostic data.

## Entity support

G2HA maps supported Home Assistant domains to Google device types and traits. Support depends on the domain and, for some features, on attributes reported by the entity. An entity is counted as supported when G2HA can map it and determine at least one Google trait for it. Unsupported domains and entities without usable traits are skipped.

Support is not identical to full feature parity: Google capabilities vary by device type, and an entity may expose only a subset of its Home Assistant controls. Check the entity's reported traits and the project's issue tracker for current limitations.

## Choosing what to expose

Depending on the integration version and configuration, G2HA can expose all supported entities, selected entities, or supported entities assigned to selected Home Assistant areas. Explicit entity and area selections are included. The option to include unavailable entities determines whether entities whose state is `unknown` or `unavailable` are considered during inventory construction.

Entities that are supported but not exposed remain in the integration's discovered inventory but are not sent to Google as synchronized devices.

## Diagnostic sensors

Diagnostic sensor names may vary slightly by integration release. The main values mean:

| Sensor | Meaning |
| --- | --- |
| Connection | Current relay WebSocket state. `connected` means the integration has an open connection to the relay. |
| Relay address | Host and port parsed from the configured relay URL. |
| Found supported entities | Number of entities G2HA mapped successfully before exposure filtering. |
| Filtered entities | Supported entities omitted from the synchronized device list by exposure choices. This is calculated as found minus synchronized. |
| Synced devices | Number of entities currently sent to the relay for Google Home. |
| Last sync | Time of the most recent device snapshot synchronization. |
| Sync status / progress | Current or most recently completed synchronization status and progress. |

These counts describe G2HA's inventory and exposure decision. They do not indicate whether Google Home has refreshed its own device cache or whether a particular device is currently reachable by Google.

The `Found supported entities` count does not mean every such entity is exposed to Google. For example, if 80 entities are supported, 50 are exposed, and 30 are excluded by the current selection, the values are `Found = 80`, `Filtered = 30`, and `Synced = 50`.

## Troubleshooting

- If Connection is disconnected, check that the relay URL is correct and reachable from Home Assistant, and inspect the Home Assistant log for WebSocket errors.
- If Found is zero, check that Home Assistant has entities in domains supported by the installed integration version and that those entities expose usable traits.
- If Filtered is high, review the selected entities and areas in the integration options.
- If Synced is correct but Google Home does not show the changes, trigger a Google Home device sync and check the relay logs.
- Downloaded Home Assistant diagnostics can contain device names, entity IDs, room names, and connection metadata. Review and sanitize them before sharing publicly.

