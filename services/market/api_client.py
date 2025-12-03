import ccxt
from utils.logger import logger
from services.market.type import MarketData
from services.market.type import Kline

class APIClient:
    """REST API 客户端（CCXT）"""
    #固定使用binance的API
    def __init__(self, exchange_config: dict):
        self.exchange = ccxt.binance()
        logger.info(f"APIClient initialized")
        # 初始化时加载市场数据
        try:
            self.exchange.load_markets()
            logger.info(f"APIClient initialized, markets loaded")
        except Exception as e:
            logger.error(f"❌ 加载市场数据失败: {e}", exc_info=True)
            raise

    def get_market_data(self, symbol: str):
        """获取市场数据"""
        try:
            market_data = self.exchange.market(symbol)
            logger.info(f"获取到市场数据: {market_data}")
            
        except Exception as e:
            logger.error(f"❌ 获取市场数据失败: {e}", exc_info=True)
            return None
        
    def get_Klines(self, symbol: str, timeframe: str, limit: int=100):
        """获取K线数据"""
        try:
            symbol = self._normalize_symbol(symbol)
            #使用CCXT获取K线数据
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            logger.info(f"获取到K线数据: {len(ohlcv)} 根")
            
            kline_list = []
            for ohlcv_item in ohlcv:
                # CCXT 返回格式: [timestamp, open, high, low, close, volume]
                open_time = int(ohlcv_item[0])
                open_price = float(ohlcv_item[1])
                high = float(ohlcv_item[2])
                low = float(ohlcv_item[3])
                close = float(ohlcv_item[4])
                volume = float(ohlcv_item[5]) if len(ohlcv_item) > 5 else 0.0
                
                # 计算缺失的字段
                # close_time: 根据 timeframe 计算（近似值）
                close_time = self._calculate_close_time(open_time, timeframe)
                
                # quote_volume: 使用 close 价格估算（volume * close）
                quote_volume = volume * close if volume > 0 else 0.0
                
                # trades: CCXT 不提供，设为 0
                trades = 0
                
                kline = Kline(
                    open_time=open_time,
                    open=open_price,
                    high=high,
                    low=low,
                    close=close,
                    volume=volume,
                    close_time=close_time,
                    quote_volume=quote_volume,
                    trades=trades
                )
                kline_list.append(kline)
            
            logger.info(f"✅ 成功转换 {len(kline_list)} 根K线数据")
            return kline_list
        except Exception as e:
            logger.error(f"❌ 获取K线数据失败: {e}", exc_info=True)
            return None
    
    def _calculate_close_time(self, open_time: int, timeframe: str) -> int:
        """根据开盘时间和时间周期计算收盘时间（毫秒）"""
        # 将时间周期转换为秒数
        timeframe_seconds = {
            '1m': 60,
            '3m': 180,
            '5m': 300,
            '15m': 900,
            '30m': 1800,
            '1h': 3600,
            '2h': 7200,
            '4h': 14400,
            '6h': 21600,
            '8h': 28800,
            '12h': 43200,
            '1d': 86400,
            '3d': 259200,
            '1w': 604800,
            '1M': 2592000,  # 近似值
        }
        
        seconds = timeframe_seconds.get(timeframe, 3600)  # 默认1小时
        close_time = open_time + (seconds * 1000) - 1  # 减去1毫秒，因为收盘时间是周期结束前1ms
        return close_time
        
    def _normalize_symbol(self, symbol: str) -> str:
        """规范化交易对"""
        symbol = symbol.upper()
        if not symbol.endswith('USDT'):
            symbol = symbol + 'USDT'
        return symbol