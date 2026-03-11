from __future__ import annotations
from pydantic import BaseModel, Field


class TrainingRecipe(BaseModel):
    name: str
    plugin_name: str
    backbone: str
    task_type: str
    hyperparameters: dict = Field(default_factory=dict)
