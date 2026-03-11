from __future__ import annotations

from id_doc_ocr.core.contracts import DocumentPlugin


class PluginRegistry:
    def __init__(self) -> None:
        self._plugins: dict[str, DocumentPlugin] = {}

    def register(self, plugin: DocumentPlugin) -> None:
        self._plugins[plugin.metadata.name] = plugin

    def get(self, name: str) -> DocumentPlugin:
        return self._plugins[name]

    def list_plugins(self) -> list[str]:
        return sorted(self._plugins.keys())


registry = PluginRegistry()
