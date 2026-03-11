from id_doc_ocr.core.registry import registry
from id_doc_ocr.plugins.china_id import plugin as china_id_plugin
from id_doc_ocr.plugins.passport import plugin as passport_plugin
from id_doc_ocr.plugins.boarding_pass import plugin as boarding_pass_plugin
from id_doc_ocr.plugins.medical_record import plugin as medical_record_plugin
from id_doc_ocr.plugins.train_ticket import plugin as train_ticket_plugin
from id_doc_ocr.plugins.hukou_booklet import plugin as hukou_booklet_plugin

for plugin in [
    china_id_plugin,
    passport_plugin,
    boarding_pass_plugin,
    medical_record_plugin,
    train_ticket_plugin,
    hukou_booklet_plugin,
]:
    registry.register(plugin)

__all__ = ["registry"]
