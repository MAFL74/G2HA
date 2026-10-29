# G2HA WebSocket protocol

The Home Assistant integration connects to the relay at:

`/api/v1/ha/ws?instance_id=<stable-instance-id>`

The connection is initiated by Home Assistant and carries JSON messages. The exact supported fields may evolve with the integration and relay versions.

## Home Assistant to relay

The client identifies itself after connecting:

```json
{"type":"hello","payload":{"source":"home_assistant"}}
```

It then publishes the synchronized device inventory:

```json
{
  "type":"devices",
  "devices":[
    {
      "id":"light.kitchen",
      "type":"action.devices.types.LIGHT",
      "name":"Kitchen light",
      "traits":["action.devices.traits.OnOff"],
      "state":{"on":true},
      "exposed":true,
      "available":true
    }
  ]
}
```

State changes are sent as they occur:

```json
{"type":"state","device_id":"light.kitchen","payload":{"on":false}}
```

## Relay to Home Assistant

The relay can send an execution request with a request ID. The integration runs the requested Home Assistant services and returns a `result` message with the same request ID and a Google-compatible command result:

```json
{
  "type":"execute",
  "request_id":"request-123",
  "payload":{"commands":[{"devices":{"ids":["light.kitchen"]},"execution":[{"command":"action.devices.commands.OnOff","params":{"on":true}}]}]}
}
```

The corresponding response uses `type: "result"`. Device identifiers are Home Assistant entity IDs. Device types, traits, state fields, and supported commands depend on the mapping implemented by the integration.

## Sync behavior

The integration sends a full snapshot on connection and when a forced sync is requested. It periodically rebuilds its inventory and sends an updated snapshot when the synchronized entity IDs change. State events are sent separately, so a state change does not require a full inventory upload.

