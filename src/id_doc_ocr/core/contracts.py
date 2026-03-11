from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


@dataclass
class PluginMetadata:
    name: str
    version: str = "0.1.0"
    description: str = ""
    supported_backbones: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)


class DocumentPlugin(Protocol):
    metadata: PluginMetadata

    def get_schema_name(self) -> str: ...

    def get_default_config(self) -> dict: ...

    def validate_fields(self, fields: dict) -> dict: ...
