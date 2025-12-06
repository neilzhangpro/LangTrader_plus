from decision_engine.state import DecisionState
from services.market.api_client import APIClient
from utils.logger import logger
from typing import Optional
from services.market.monitor import MarketMonitor
import asyncio
import threading

# 前向引用，避免循环导入
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from services.ExchangeService import ExchangeService

class DataCollector:
    """数据收集节点 - 收集市场数据（K线、价格等）"""
    
    # K线数据配置
    KLINE_LIMIT = 200  # K线数据获取数量
    
    # WebSocket订阅配置
    WS_SUBSCRIBE_TIMEOUT_SECONDS = 5  # WebSocket订阅超时时间（秒）
    def __init__(
        self, 
        exchange_config: dict, 
        market_monitor: Optional[MarketMonitor] = None,
        exchange_service: Optional['ExchangeService'] = None
    ):
        self.api_client = APIClient(exchange_config)
        self.market_monitor = market_monitor
        self.exchange_service = exchange_service

    def run(self, state: DecisionState) -> DecisionState:
        """收集市场数据（批量模式：为所有需要的币种收集数据）"""
        # 1. 获取持仓币种（如果state中没有，则从交易所获取）
        positions = state.get('positions', [])
        if not positions and self.exchange_service:
            try:
                positions = self.exchange_service.get_positions()
                state['positions'] = positions
                logger.debug(f"从交易所获取持仓信息: {len(positions)}个持仓")
            except Exception as e:
                logger.warning(f"获取持仓信息失败: {e}")
                positions = []
        
        position_symbols = {pos.get('symbol') for pos in positions if pos.get('symbol')}
        
        # 2. 获取候选币种（用于开仓决策）
        candidate_symbols = state.get('candidate_symbols', [])
        
        # 3. 合并去重，确保所有需要的币种都有数据
        all_symbols = list(set(position_symbols) | set(candidate_symbols))
        
        if not all_symbols:
            logger.warning("没有需要收集数据的币种，跳过数据收集")
            return state
        
        logger.info(f"开始收集市场数据: 持仓币种={len(position_symbols)}个, 候选币种={len(candidate_symbols)}个, 总计={len(all_symbols)}个")
        
        # 确保所有币种都已添加到监控器（动态订阅WebSocket）
        if self.market_monitor:
            self._ensure_symbols_monitored(all_symbols)
        
        market_data_map = {}
        
        for symbol in all_symbols:
            try:
                # 优先从监控器缓存获取数据
                if self.market_monitor and self.market_monitor.is_monitoring(symbol):
                    klines_3m = self.market_monitor.get_klines(symbol, "3m", limit=self.KLINE_LIMIT)
                    klines_4h = self.market_monitor.get_klines(symbol, "4h", limit=self.KLINE_LIMIT)
                    latest_price = self.market_monitor.get_latest_price(symbol)
                    
                    market_data_map[symbol] = {
                        'symbol': symbol,
                        'current_price': latest_price,
                        'klines_3m': klines_3m,
                        'klines_4h': klines_4h,
                        'source': 'websocket_cache',
                        'is_position': symbol in position_symbols,  # 标记是否为持仓币种
                        'is_candidate': symbol in candidate_symbols  # 标记是否为候选币种
                    }
                    logger.debug(f"{symbol}: 从监控器缓存获取数据")
                else:
                    # 回退到 REST API
                    klines_3m = self.api_client.get_Klines(symbol, "3m", limit=self.KLINE_LIMIT)
                    klines_4h = self.api_client.get_Klines(symbol, "4h", limit=self.KLINE_LIMIT)
                    
                    market_data_map[symbol] = {
                        'symbol': symbol,
                        'klines_3m': klines_3m or [],
                        'klines_4h': klines_4h or [],
                        'source': 'rest_api',
                        'is_position': symbol in position_symbols,
                        'is_candidate': symbol in candidate_symbols
                    }
                    logger.debug(f"{symbol}: 从REST API获取数据")
            except Exception as e:
                logger.error(f"收集{symbol}市场数据失败: {e}", exc_info=True)
                market_data_map[symbol] = {
                    'symbol': symbol,
                    'error': str(e)
                }
        
        state['market_data_map'] = market_data_map
        logger.info(f"完成数据收集，共{len(market_data_map)}个币种")
        return state
    
    def _ensure_symbols_monitored(self, symbols: list):
        """确保所有币种都已添加到监控器（动态订阅WebSocket）"""
        if not self.market_monitor:
            return
        
        # 检查哪些币种需要添加
        symbols_to_add = [s for s in symbols if not self.market_monitor.is_monitoring(s)]
        
        if not symbols_to_add:
            logger.debug("所有币种已在监控中")
            return
        
        logger.debug(f"需要添加{len(symbols_to_add)}个币种到监控器")
        
        # 在独立线程中运行异步操作（因为监控器的事件循环在另一个线程）
        def add_symbols_async():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                for symbol in symbols_to_add:
                    try:
                        loop.run_until_complete(
                            self.market_monitor.add_symbol(symbol, intervals=["3m", "4h"])
                        )
                        logger.debug(f"已添加{symbol}到监控器并订阅WebSocket")
                    except Exception as e:
                        logger.error(f"添加{symbol}到监控器失败: {e}", exc_info=True)
            except Exception as e:
                logger.error(f"添加币种到监控器失败: {e}", exc_info=True)
            finally:
                loop.close()
        
        # 在后台线程中执行（不阻塞主流程）
        thread = threading.Thread(target=add_symbols_async, daemon=True)
        thread.start()
        # 等待订阅完成
        thread.join(timeout=self.WS_SUBSCRIBE_TIMEOUT_SECONDS)
        
        if thread.is_alive():
            logger.warning("添加币种到监控器超时，将使用REST API回退")
        else:
            # 验证订阅状态
            failed_symbols = [s for s in symbols_to_add if not self.market_monitor.is_monitoring(s)]
            if failed_symbols:
                logger.warning(f"以下币种订阅失败，将使用REST API: {failed_symbols}")
    