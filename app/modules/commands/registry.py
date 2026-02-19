from __future__ import annotations
from typing import Any, Type
from pydantic import BaseModel

class CommandSpec:
    def __init__(self, type_: str, payload_model: Type[BaseModel]):
        self.type = type_
        self.payload_model = payload_model

    def validate_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        # pydantic v2
        model = self.payload_model.model_validate(payload)
        return model.model_dump()

class CommandRegistry:
    def __init__(self):
        self._specs: dict[str, CommandSpec] = {}

    def register(self, spec: CommandSpec) -> None:
        self._specs[spec.type] = spec

    def get(self, type_: str) -> CommandSpec:
        if type_ not in self._specs:
            raise ValueError(f"Unknown command type: {type_}")
        return self._specs[type_]

registry = CommandRegistry()
