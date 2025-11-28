from sqlmodel import SQLModel, Field, Column, String
from models.base import BaseModel

class AIModel(BaseModel, table=True):
    """AI模型配置表"""
    __tablename__ = "ai_models"
    
    user_id: str = Field(foreign_key="users.id", index=True)
    name: str = Field(max_length=255)
    provider: str = Field(max_length=50)  # 'openai', 'anthropic', 'custom' 等
    enabled: bool = Field(default=False)
    api_key: str = Field(default="")
    base_url: str = Field(default="")  # 自定义API地址
    model_name: str = Field(default="")  # 自定义模型名称
