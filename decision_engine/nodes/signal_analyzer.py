from decision_engine.state import DecisionState
from utils.logger import logger
from services.market.indicators import IndicatorCalculator
from services.market.api_client import APIClient

class SignalAnalyzer:
    """信号分析节点 - 计算技术指标和流动性过滤"""
    
    # 数据质量要求
    MIN_KLINES_REQUIRED = 20  # 最小K线数量
    
    # 技术指标周期
    EMA_SHORT_PERIOD = 20
    EMA_LONG_PERIOD = 50
    RSI_SHORT_PERIOD = 7
    RSI_LONG_PERIOD = 14
    ATR_PERIOD = 14
    
    # 价格变化计算
    PRICE_CHANGE_1H_KLINES = 20  # 1小时价格变化需要20根3分钟K线
    PRICE_CHANGE_4H_KLINES = 2  # 4小时价格变化需要2根4小时K线
    
    # 流动性阈值（USD）
    LIQUIDITY_THRESHOLD_EXISTING = 5_000_000  # 持仓币种：5M USD
    LIQUIDITY_THRESHOLD_NEW = 15_000_000  # 新币种：15M USD
    def __init__(self, exchange_config: dict):
        self.api_client = APIClient(exchange_config)

    def run(self, state: DecisionState) -> DecisionState:
        """分析信号并计算技术指标"""
        market_data_map = state.get('market_data_map', {})
        existing_positions = state.get('positions', [])
        signal_data_map = {}

        for symbol, raw_data in market_data_map.items():
            try:
                # 验证数据质量
                klines_3m = raw_data.get('klines_3m', [])
                klines_4h = raw_data.get('klines_4h', [])
                
                # 检查是否有错误标记
                if 'error' in raw_data:
                    logger.warning(f"{symbol}数据收集失败: {raw_data.get('error')}，跳过")
                    continue
                
                # 检查数据是否足够
                if not klines_3m or len(klines_3m) < self.MIN_KLINES_REQUIRED:
                    logger.warning(f"{symbol} 3分钟K线数据不足（需要至少{self.MIN_KLINES_REQUIRED}根），跳过")
                    continue
                if not klines_4h or len(klines_4h) < self.MIN_KLINES_REQUIRED:
                    logger.warning(f"{symbol} 4小时K线数据不足（需要至少{self.MIN_KLINES_REQUIRED}根），跳过")
                    continue
                
                # 计算技术指标
                ema20_3m = IndicatorCalculator.calculate_ema(klines_3m, self.EMA_SHORT_PERIOD)
                ema20_4h = IndicatorCalculator.calculate_ema(klines_4h, self.EMA_SHORT_PERIOD)
                ema50_4h = IndicatorCalculator.calculate_ema(klines_4h, self.EMA_LONG_PERIOD)
                macd_3m = IndicatorCalculator.calculate_macd(klines_3m)
                macd_4h = IndicatorCalculator.calculate_macd(klines_4h)
                rsi7_3m = IndicatorCalculator.calculate_rsi(klines_3m, self.RSI_SHORT_PERIOD)
                rsi7_4h = IndicatorCalculator.calculate_rsi(klines_4h, self.RSI_SHORT_PERIOD)
                rsi14_3m = IndicatorCalculator.calculate_rsi(klines_3m, self.RSI_LONG_PERIOD)
                rsi14_4h = IndicatorCalculator.calculate_rsi(klines_4h, self.RSI_LONG_PERIOD)
                atr_4h = IndicatorCalculator.calculate_atr(klines_4h, self.ATR_PERIOD)
                
                #3.计算价格变化
                # 获取当前价格（优先使用3分钟K线，如果没有则使用4小时K线）
                if len(klines_3m) > 0:
                    current_price = klines_3m[-1].close
                elif len(klines_4h) > 0:
                    current_price = klines_4h[-1].close
                else:
                    logger.warning(f"{symbol}没有K线数据，跳过")
                    continue
                
                # 计算价格变化
                if len(klines_3m) >= self.PRICE_CHANGE_1H_KLINES:
                    price_1h_ago = klines_3m[-self.PRICE_CHANGE_1H_KLINES].close
                    price_change_1h = (current_price - price_1h_ago) / price_1h_ago * 100
                else:
                    price_change_1h = 0.0
                
                if len(klines_4h) >= self.PRICE_CHANGE_4H_KLINES:
                    price_4h_ago = klines_4h[-self.PRICE_CHANGE_4H_KLINES].close
                    price_change_4h = (current_price - price_4h_ago) / price_4h_ago * 100 if price_4h_ago > 0 else 0.0
                else:
                    price_change_4h = 0.0
                
                # 流动性过滤（对持仓币种使用更宽松的阈值）
                existing_symbols = {pos.get('symbol') for pos in existing_positions if pos.get('symbol')}
                is_existing_position = symbol in existing_symbols
                
                liquidity_threshold = self.LIQUIDITY_THRESHOLD_EXISTING if is_existing_position else self.LIQUIDITY_THRESHOLD_NEW
                
                logger.debug(f"计算{symbol}的流动性（{'持仓币种' if is_existing_position else '新币种'}，阈值: {liquidity_threshold/1_000_000:.0f}M USD）")
                
                # 获取持仓量（合约数量）
                open_interest = self.api_client.get_open_interest(symbol)
                
                if open_interest is None or open_interest <= 0:
                    logger.warning(f"{symbol} 无法获取持仓量")
                    # 对于持仓币种，即使无法获取也继续处理（避免误平仓）
                    if not is_existing_position:
                        logger.warning(f"{symbol} 新币种无法获取持仓量，跳过")
                        continue
                else:
                    # 计算持仓价值（USD）= 持仓量（合约数量）× 当前价格
                    oi_value_usd = open_interest * current_price
                    
                    logger.debug(f"{symbol} 持仓量: {open_interest:.2f}, 持仓价值: {oi_value_usd/1_000_000:.2f}M USD")
                    
                    if oi_value_usd < liquidity_threshold:
                        threshold_str = f"{self.LIQUIDITY_THRESHOLD_EXISTING/1_000_000:.0f}M" if is_existing_position else f"{self.LIQUIDITY_THRESHOLD_NEW/1_000_000:.0f}M"
                        logger.warning(
                            f"{symbol} 流动性不足 "
                            f"(持仓价值: {oi_value_usd/1_000_000:.2f}M USD < {threshold_str})"
                        )
                        if not is_existing_position:
                            logger.warning(f"{symbol} 新币种流动性不足，跳过")
                            continue
                        # 持仓币种流动性不足时记录警告但继续处理
                #6 计算序列指标(用于AI分析历史趋势)
                intraday_series = IndicatorCalculator.calculate_series_indicators(klines_3m)
                longer_term_series = IndicatorCalculator.calculate_series_indicators(klines_4h)
                # 7. 格式化数据（准备给AI使用）
                signal_data_map[symbol] = {
                    'current_price': current_price,
                    'price_change_1h': price_change_1h,
                    'price_change_4h': price_change_4h,
                    
                    # 3分钟指标
                    'ema20_3m': ema20_3m,
                    'macd_3m': macd_3m,
                    'rsi7_3m': rsi7_3m,
                    'rsi7_4h': rsi7_4h,
                    'rsi14_3m': rsi14_3m,
                    
                    # 4小时指标
                    'ema20_4h': ema20_4h,
                    'ema50_4h': ema50_4h,
                    'macd_4h': macd_4h,
                    'rsi14_4h': rsi14_4h,
                    'atr_4h': atr_4h,
                    
                    # 序列数据（用于AI分析）
                    'intraday_series': intraday_series,
                    'longer_term_series': longer_term_series,
                }
                
                logger.debug(f"{symbol}信号分析完成")
                
            except Exception as e:
                logger.error(f"{symbol}信号分析失败: {e}", exc_info=True)
                continue
        
        state['signal_data_map'] = signal_data_map
        logger.info(f"完成信号分析，共{len(signal_data_map)}个币种")
        return state



            