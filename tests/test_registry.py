from id_doc_ocr.core.registry import PluginRegistry
from id_doc_ocr.plugins.china_id.plugin import plugin as china_id_plugin


def test_registry_register_and_list():
    registry = PluginRegistry()
    registry.register(china_id_plugin)
    assert registry.list_plugins() == ["china_id"]
