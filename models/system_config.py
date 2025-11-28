from sqlmodel import SQLModel, Field
from datetime import datetime

class SystemConfig(SQLModel, table=True):
    """系统配置表"""
    __tablename__ = "system_config"
    
    key: str = Field(
        primary_key=True,
        max_length=255
    )
    value: str
    updated_at: datetime = Field(
        default_factory=datetime.now,
        nullable=False
    )
