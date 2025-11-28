from sqlmodel import SQLModel, Field, Column, String
from typing import Optional
from models.base import BaseModel

class User(BaseModel, table=True):
    """用户模型"""
    __tablename__ = "users"

    email: str = Field(
        sa_column=Column(String(255), unique=True, index=True),
        max_length=255
    )
    password_hash: str = Field(max_length=255)
    otp_secret: Optional[str] = Field(default=None, max_length=32)
    otp_verified: bool = Field(default=False)