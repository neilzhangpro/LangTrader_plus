from sqlmodel import SQLModel, Field, Column, String
from sqlalchemy import JSON
from typing import Optional
from decimal import Decimal
from models.base import BaseModel

class DecisionLog(BaseModel, table=True):
    """决策日志表"""
    __tablename__ = "decision_logs"
    
    trader_id: str = Field(foreign_key="traders.id", index=True)
    symbol: str = Field(max_length=50, index=True)
    decision_state: str = Field(sa_column=Column(JSON))  # JSONB，存储为 JSON 字符串
    decision_result: Optional[str] = Field(default=None, max_length=50)  # 'buy', 'sell', 'hold'
    reasoning: Optional[str] = None
    confidence: Optional[Decimal] = Field(
        default=None,
        max_digits=5,
        decimal_places=4
    )
    
    # 注意：created_at 继承自 BaseModel
