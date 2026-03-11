from id_doc_ocr.training.recipe import TrainingRecipe


recipe = TrainingRecipe(
    name='boarding_pass-baseline',
    plugin_name='boarding_pass',
    backbone='paddleocr',
    task_type='document_extraction',
    hyperparameters={},
)
