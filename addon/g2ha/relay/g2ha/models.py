from typing import Any, Literal

from pydantic import BaseModel, Field


class Device(BaseModel):
    id: str
    type: str
    name: str
    room_hint: str | None = None
    traits: list[str] = Field(default_factory=list)
    state: dict[str, Any] = Field(default_factory=dict)
    attributes: dict[str, Any] = Field(default_factory=dict)


class HAEnvelope(BaseModel):
    type: Literal["hello", "devices", "state", "result", "error"]
    request_id: str | None = None
    devices: list[Device] | None = None
    device_id: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None
