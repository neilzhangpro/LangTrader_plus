from sqlmodel import SQLModel, Field, Column, String
from typing import Optional
from models.base import BaseModel

class PromptTemplate(BaseModel, table=True):
    """提示词模板表"""
    __tablename__ = "prompt_templates"
    
    name: str = Field(
        default="default",
        sa_column=Column(String(255), index=True),
        max_length=255
    )
    content: str
    description: str = Field(default="")
    # created_at 和 updated_at 继承自 BaseModel