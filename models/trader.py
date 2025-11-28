from sqlmodel import SQLModel, Field, Column, String
from sqlalchemy import JSON
from typing import Optional
from decimal import Decimal
from models.base import BaseModel

class Trader(BaseModel, table=True):
    """交易员配置表"""
    __tablename__ = "traders"
    
    user_id: str = Field(foreign_key="users.id", index=True)
    name: str = Field(max_length=255)
    ai_model_id: str = Field(foreign_key="ai_models.id", index=True)
    exchange_id: str = Field(foreign_key="exchanges.id", index=True)
    
    initial_balance: Decimal = Field(max_digits=20, decimal_places=8)
    scan_interval_minutes: int = Field(default=3)
    is_running: bool = Field(default=False, index=True)
    
    # 杠杆配置
    btc_eth_leverage: int = Field(default=5)
    altcoin_leverage: int = Field(default=5)
    
    # 币种配置
    trading_symbols: str = Field(default="")  # 逗号分隔
    use_default_coins: bool = Field(default=True)
    custom_coins: str = Field(default="")  # JSON格式
    
    # 信号源配置
    use_coin_pool: bool = Field(default=False)
    use_oi_top: bool = Field(default=False)
    use_inside_coins: bool = Field(default=False)
    
    # 提示词配置
    system_prompt_template: str = Field(default="default", max_length=255)
    custom_prompt: Optional[str] = Field(default=None)
    override_base_prompt: bool = Field(default=False)
    
    # 保证金模式
    is_cross_margin: bool = Field(default=True)
    
    # LangGraph 决策引擎配置（JSONB 存储为 JSON 类型）
    decision_graph_config: Optional[str] = Field(
        default=None,
        sa_column=Column(JSON)
    )
