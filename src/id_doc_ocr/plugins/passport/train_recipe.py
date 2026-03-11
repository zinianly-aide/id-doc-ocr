from id_doc_ocr.training.recipe import TrainingRecipe


recipe = TrainingRecipe(
    name='passport-baseline',
    plugin_name='passport',
    backbone='paddleocr',
    task_type='document_extraction',
    hyperparameters={},
)
