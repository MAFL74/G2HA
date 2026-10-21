import asyncio
from dataclasses import dataclass, field

from fastapi import WebSocket

from .models import Device


@dataclass
class Instance:
    instance_id: str
    websocket: WebSocket | None = None
    devices: dict[str, Device] = field(default_factory=dict)
    pending: dict[str, asyncio.Future] = field(default_factory=dict)


class RelayState:
    def __init__(self) -> None:
        self.instances: dict[str, Instance] = {}

    def get(self, instance_id: str) -> Instance:
        return self.instances.setdefault(instance_id, Instance(instance_id))

    def set_devices(self, instance_id: str, devices: list[Device]) -> None:
        self.get(instance_id).devices = {device.id: device for device in devices}

    def disconnect(self, instance_id: str, websocket: WebSocket) -> None:
        instance = self.instances.get(instance_id)
        if instance and instance.websocket is websocket:
            instance.websocket = None


relay_state = RelayState()
