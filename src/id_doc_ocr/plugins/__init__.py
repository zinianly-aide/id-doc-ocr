from id_doc_ocr.core.registry import registry
from id_doc_ocr.plugins.china_id import plugin as china_id_plugin
from id_doc_ocr.plugins.passport import plugin as passport_plugin
from id_doc_ocr.plugins.boarding_pass import plugin as boarding_pass_plugin
from id_doc_ocr.plugins.medical_record import plugin as medical_record_plugin
from id_doc_ocr.plugins.diagnosis_proof import plugin as diagnosis_proof_plugin
from id_doc_ocr.plugins.train_ticket import plugin as train_ticket_plugin
from id_doc_ocr.plugins.hukou_booklet import plugin as hukou_booklet_plugin
from id_doc_ocr.plugins.birth_certificate import plugin as birth_certificate_plugin
from id_doc_ocr.plugins.only_child_certificate import plugin as only_child_certificate_plugin
from id_doc_ocr.plugins.custody_relationship_certificate import plugin as custody_relationship_certificate_plugin

for plugin in [
    china_id_plugin,
    passport_plugin,
    boarding_pass_plugin,
    medical_record_plugin,
    diagnosis_proof_plugin,
    train_ticket_plugin,
    hukou_booklet_plugin,
    birth_certificate_plugin,
    only_child_certificate_plugin,
    custody_relationship_certificate_plugin,
]:
    registry.register(plugin)

__all__ = ["registry"]
