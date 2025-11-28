from sqlmodel import SQLModel, Field, Column, String
from models.base import BaseModel

class UserSignalSource(BaseModel, table=True):
    """用户信号源配置表"""
    __tablename__ = "user_signal_sources"
    
    user_id: str = Field(
        foreign_key="users.id",
        unique=True,
        index=True
    )
    coin_pool_url: str = Field(default="")
    oi_top_url: str = Field(default="")
