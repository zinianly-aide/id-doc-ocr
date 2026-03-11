from id_doc_ocr.training.recipe import TrainingRecipe


recipe = TrainingRecipe(
    name='hukou_booklet-baseline',
    plugin_name='hukou_booklet',
    backbone='paddleocr',
    task_type='document_extraction',
    hyperparameters={},
)
