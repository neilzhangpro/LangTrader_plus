from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime

@dataclass
class Kline:
    """K线数据"""
    open_time: int
    open: float
    high: float
    low: float
    close: float
    volume: float
    close_time: int
    quote_volume: float
    trades: int

@dataclass
class MarketData:
    """市场数据"""
    symbol: str
    current_price: float
    price_change_1h: float
    price_change_4h: float
    current_ema20: float
    current_macd: float
    current_rsi7: float
    open_interest: Optional[float] = None
    funding_rate: Optional[float] = None
    intraday_series: Optional['IntradayData'] = None
    longer_term_context: Optional['LongerTermData'] = None


@dataclass
class IntradayData:
    """日内数据(3分钟)"""
    mid_price: List[float]
    ema20_values: List[float]
    mace_values: List[float]
    rsi7_values: List[float]
    rsi14_values: List[float]

@dataclass
class LongerTermData:
    """长期数据(4小时)"""
    ema20: float
    ema50: float
    atr3: float
    atr14: float
    current_volume: float
    average_volume: float
    macd_value: List[float]
    rsi14_values: List[float]