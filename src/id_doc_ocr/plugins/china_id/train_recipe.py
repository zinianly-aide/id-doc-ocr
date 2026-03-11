from id_doc_ocr.training.recipe import TrainingRecipe


recipe = TrainingRecipe(
    name='china_id-baseline',
    plugin_name='china_id',
    backbone='paddleocr',
    task_type='document_extraction',
    hyperparameters={},
)
