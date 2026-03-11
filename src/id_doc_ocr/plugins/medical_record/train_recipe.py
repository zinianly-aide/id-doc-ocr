from id_doc_ocr.training.recipe import TrainingRecipe


recipe = TrainingRecipe(
    name='medical_record-baseline',
    plugin_name='medical_record',
    backbone='paddleocr',
    task_type='document_extraction',
    hyperparameters={},
)
