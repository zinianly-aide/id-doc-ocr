from id_doc_ocr.training.recipe import TrainingRecipe


recipe = TrainingRecipe(
    name='train_ticket-baseline',
    plugin_name='train_ticket',
    backbone='paddleocr',
    task_type='document_extraction',
    hyperparameters={},
)
