from typing import Any

from .models import Device


def sync_response(request_id: str, instance_id: str, devices: list[Device]) -> dict[str, Any]:
    return {
        "requestId": request_id,
        "payload": {
            "agentUserId": instance_id,
            "devices": [
                {
                    "id": device.id,
                    "type": device.type,
                    "name": {"name": device.name},
                    **({"roomHint": device.room_hint} if device.room_hint else {}),
                    "traits": device.traits,
                    **({"attributes": device.attributes} if device.attributes else {}),
                    "willReportState": True,
                }
                for device in devices
            ],
        },
    }


def query_response(request_id: str, states: dict[str, dict[str, Any]]) -> dict[str, Any]:
    return {"requestId": request_id, "payload": {"devices": states}}

