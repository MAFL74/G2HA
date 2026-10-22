from typing import Any

from .models import Device


def _valid_traits(device: Device) -> list[str]:
    attributes = device.attributes or {}
    valid: list[str] = []
    for trait in device.traits:
        if trait == "action.devices.traits.SensorState":
            # Generic HA sensors do not carry Google's required
            # sensorStatesSupported metadata yet.
            continue
        if trait == "action.devices.traits.FanSpeed" and not attributes.get("availableFanSpeeds"):
            continue
        if trait == "action.devices.traits.Modes" and not attributes.get("availableModes"):
            continue
        if trait == "action.devices.traits.TransportControl" and not attributes.get("transportControlSupportedCommands"):
            continue
        if trait == "action.devices.traits.Volume" and not {
            "volumeMaxLevel",
            "volumeCanMuteAndUnmute",
        }.issubset(attributes):
            continue
        if trait == "action.devices.traits.CameraStream" and not {
            "cameraStreamSupportedProtocols",
            "cameraStreamNeedAuthToken",
        }.issubset(attributes):
            continue
        if trait == "action.devices.traits.ColorSetting" and not (
            attributes.get("colorModel") or attributes.get("colorTemperatureRange")
        ):
            continue
        if trait == "action.devices.traits.TemperatureSetting" and not attributes.get("availableThermostatModes"):
            continue
        valid.append(trait)
    return valid


def sync_response(request_id: str, instance_id: str, devices: list[Device]) -> dict[str, Any]:
    google_devices = []
    for device in devices:
        traits = _valid_traits(device)
        if not traits:
            continue
        google_devices.append(
            {
                "id": device.id,
                "type": device.type,
                "name": {"name": device.name},
                **({"roomHint": device.room_hint} if device.room_hint else {}),
                "traits": traits,
                **({"attributes": device.attributes} if device.attributes else {}),
                # Report State is not implemented by this relay yet; Google
                # must use QUERY for current state until it is added.
                "willReportState": False,
            }
        )
    return {
        "requestId": request_id,
        "payload": {
            "agentUserId": instance_id,
            "devices": google_devices,
        },
    }


def query_response(request_id: str, states: dict[str, dict[str, Any]]) -> dict[str, Any]:
    return {"requestId": request_id, "payload": {"devices": states}}

