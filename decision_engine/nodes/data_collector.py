from decision_engine.state import DecisionState
from services.market.api_client import APIClient
from utils.logger import logger
from typing import Optional
from services.market.monitor import MarketMonitor
import asyncio
import threading

class DataCollector:
    def __init__(self, exchange_config: dict, market_monitor: Optional[MarketMonitor] = None):
        logger.info(f"DataCollector initialized")
        self.api_client = APIClient(exchange_config)
        self.market_monitor = market_monitor

    def run(self, state: DecisionState) -> DecisionState:
        """收集市场数据（批量模式：为所有候选币种收集数据）"""
        logger.info(f"DataCollector run")
        
        candidate_symbols = state.get('candidate_symbols', [])
        logger.info(f"📝 candidate_symbols: {candidate_symbols}")
        
        if not candidate_symbols:
            logger.warning("⚠️  没有候选币种，跳过数据收集")
            return state
        
        logger.info(f"📊 开始为 {len(candidate_symbols)} 个候选币种收集市场数据...")
        
        # 确保所有候选币种都已添加到监控器（动态订阅WebSocket）
        if self.market_monitor:
            self._ensure_symbols_monitored(candidate_symbols)
        
        market_data_map = {}
        
        for symbol in candidate_symbols:
            try:
                # 优先从监控器缓存获取数据
                if self.market_monitor and self.market_monitor.is_monitoring(symbol):
                    klines_3m = self.market_monitor.get_klines(symbol, "3m", limit=200)
                    klines_4h = self.market_monitor.get_klines(symbol, "4h", limit=200)
                    latest_price = self.market_monitor.get_latest_price(symbol)
                    
                    market_data_map[symbol] = {
                        'symbol': symbol,
                        'current_price': latest_price,
                        'klines_3m': klines_3m,
                        'klines_4h': klines_4h,
                        'source': 'websocket_cache'
                    }
                    logger.debug(f"✅ {symbol}: 从监控器缓存获取数据")
                else:
                    # 回退到 REST API
                    klines_3m = self.api_client.get_Klines(symbol, "3m", limit=200)
                    klines_4h = self.api_client.get_Klines(symbol, "4h", limit=200)
                    
                    market_data_map[symbol] = {
                        'symbol': symbol,
                        'klines_3m': klines_3m or [],
                        'klines_4h': klines_4h or [],
                        'source': 'rest_api'
                    }
                    logger.debug(f"✅ {symbol}: 从 REST API 获取数据")
            except Exception as e:
                logger.error(f"❌ 收集 {symbol} 市场数据失败: {e}")
                market_data_map[symbol] = {
                    'symbol': symbol,
                    'error': str(e)
                }
        
        state['market_data_map'] = market_data_map
        logger.info(f"✅ 完成数据收集，共 {len(market_data_map)} 个币种")
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
        
        logger.info(f"📡 需要添加 {len(symbols_to_add)} 个币种到监控器: {symbols_to_add}")
        
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
                        logger.info(f"✅ 已添加 {symbol} 到监控器并订阅WebSocket")
                    except Exception as e:
                        logger.error(f"❌ 添加 {symbol} 到监控器失败: {e}", exc_info=True)
            except Exception as e:
                logger.error(f"❌ 添加币种到监控器失败: {e}", exc_info=True)
            finally:
                loop.close()
        
        # 在后台线程中执行（不阻塞主流程）
        thread = threading.Thread(target=add_symbols_async, daemon=True)
        thread.start()
        # 等待一小段时间让订阅完成（最多等待3秒）
        thread.join(timeout=3)
        
        if thread.is_alive():
            logger.warning("⚠️  添加币种到监控器超时，但会在后台继续执行")
    
    def _run_with_api(self, state: DecisionState, symbol: str) -> DecisionState:
        """使用REST API获取数据"""
        try:
            klines_3m = self.api_client.get_Klines(symbol, "3m", limit=200)
            klines_4h = self.api_client.get_Klines(symbol, "4h", limit=200)
            
            state['market_data_map'] = {
                'symbol': symbol,
                'klines_3m': klines_3m or [],
                'klines_4h': klines_4h or [],
                'source': 'rest_api'
            }
            
            logger.info(f"✅ 已从 REST API 收集 {symbol} 的市场数据")
        except Exception as e:
            logger.error(f"❌ 收集市场数据失败: {e}", exc_info=True)
            state['market_data_map'] = {
                'symbol': symbol,
                'error': str(e)
            }
        
        return state