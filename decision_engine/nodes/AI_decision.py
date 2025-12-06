from decision_engine.state import DecisionState
from utils.logger import logger
from utils.llm_factory import LLMFactory
from langchain_core.messages import HumanMessage, SystemMessage
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class DecisionItem(BaseModel):
    """单个交易决策项"""
    symbol: str = Field(description="币种符号（如BTC/USDT）")
    action: str = Field(description="操作类型：open_long/open_short/close_long/close_short/hold/wait")
    leverage: Optional[int] = Field(None, description="杠杆倍数（开仓时必填）")
    position_size_usd: Optional[float] = Field(None, description="仓位大小（USD，开仓时必填）")
    stop_loss: Optional[float] = Field(None, description="止损价格（开仓时必填，必须>0）")
    take_profit: Optional[float] = Field(None, description="止盈价格（开仓时必填，必须>0）")
    confidence: int = Field(description="信心度（0-100）")
    risk_usd: Optional[float] = Field(None, description="最大美元风险（开仓时必填）")
    reasoning: str = Field(description="决策理由（需引用具体的K线形态、指标信号、OI Top数据等）")


class DecisionOutput(BaseModel):
    """AI决策输出（包含决策列表）"""
    decisions: List[DecisionItem] = Field(description="交易决策列表")


class AIDecision:
    def __init__(self, exchange_config: dict, trader_cfg: dict, exchange_service: Optional):
        self.exchange_config = exchange_config
        self.trader_cfg = trader_cfg
        self.exchange_service = exchange_service
        self.llm = None  # 初始化为 None
        self.system_prompt = None
        
        if not self.trader_cfg.get('ai_model', {}).get('enabled', False):
            logger.debug("AI模型未启用，跳过AI决策")
            return
        
        # 初始化 LLM
        try:
            provider = self.trader_cfg.get('ai_model', {}).get('provider', 'openai')
            logger.debug(f"初始化LLM，Provider: {provider}")
            
            base_llm = self._get_llm(provider)
            if not base_llm:
                logger.error("LLM创建失败")
                self.llm = None
                return
            
            # 使用结构化输出
            try:
                self.llm = base_llm.with_structured_output(DecisionOutput)
                logger.debug("已启用结构化输出")
            except Exception as e:
                logger.warning(f"启用结构化输出失败，将使用普通模式: {e}")
                self.llm = base_llm
            
            self.system_prompt = self.trader_cfg.get('prompt', '')
            logger.info(f"AI Decision节点初始化完成 (prompt长度: {len(self.system_prompt)}字符)")
        except KeyError as e:
            logger.error(f"初始化LLM失败 - KeyError: {e}", exc_info=True)
            self.llm = None
        except Exception as e:
            logger.error(f"初始化LLM失败: {e}", exc_info=True)
            self.llm = None


    def _get_llm(self, llm_provider: str) -> Optional[object]:
        """获取LLM实例（使用工厂类）"""
        ai_model_config = self.trader_cfg.get('ai_model', {})
        return LLMFactory.create_llm(ai_model_config)
       
    def _format_market_data(self, market_data_map: dict) -> str:
        """格式化市场数据，保留K线但结构化展示"""
        if not market_data_map:
            return "无市场数据"
        
        formatted_lines = []
        for symbol, data in market_data_map.items():
            current_price = data.get('current_price')
            klines_3m = data.get('klines_3m', [])
            klines_4h = data.get('klines_4h', [])
            source = data.get('source', 'unknown')
            
            # 修复：先格式化价格，避免在格式说明符中使用三元表达式
            price_str = f"{current_price:.2f}" if current_price is not None else "N/A"
            
            # 格式化3分钟K线（显示最近20根的关键信息）
            klines_3m_str = ""
            if klines_3m:
                recent_3m = klines_3m[-20:] if len(klines_3m) > 20 else klines_3m
                klines_3m_str = "\n".join([
                    f"        [{i+1}] 时间: {kline.open_time if hasattr(kline, 'open_time') else 'N/A'}, "
                    f"开: {kline.open:.2f}, 高: {kline.high:.2f}, 低: {kline.low:.2f}, "
                    f"收: {kline.close:.2f}, 量: {kline.volume:.2f}"
                    for i, kline in enumerate(recent_3m)
                ])
                if len(klines_3m) > 20:
                    klines_3m_str += f"\n        ... (共 {len(klines_3m)} 根K线，仅显示最近20根)"
            
            # 格式化4小时K线（显示最近10根的关键信息）
            klines_4h_str = ""
            if klines_4h:
                recent_4h = klines_4h[-10:] if len(klines_4h) > 10 else klines_4h
                klines_4h_str = "\n".join([
                    f"        [{i+1}] 时间: {kline.open_time if hasattr(kline, 'open_time') else 'N/A'}, "
                    f"开: {kline.open:.2f}, 高: {kline.high:.2f}, 低: {kline.low:.2f}, "
                    f"收: {kline.close:.2f}, 量: {kline.volume:.2f}"
                    for i, kline in enumerate(recent_4h)
                ])
                if len(klines_4h) > 10:
                    klines_4h_str += f"\n        ... (共 {len(klines_4h)} 根K线，仅显示最近10根)"
            
            formatted_lines.append(
                f"  {symbol}:\n"
                f"    - 当前价格: {price_str}\n"  # 使用预先格式化的字符串
                f"    - 数据来源: {source}\n"
                f"    - 3分钟K线数据 ({len(klines_3m)} 根):\n{klines_3m_str if klines_3m_str else '        无数据'}\n"
                f"    - 4小时K线数据 ({len(klines_4h)} 根):\n{klines_4h_str if klines_4h_str else '        无数据'}"
            )
        
        return "\n".join(formatted_lines) if formatted_lines else "无市场数据"

    def _format_signal_data(self, signal_data_map: dict) -> str:
        """格式化信号数据，提取关键指标并保留序列数据"""
        if not signal_data_map:
            return "无信号数据"
        
        formatted_lines = []
        for symbol, signals in signal_data_map.items():
            # 价格信息
            current_price = signals.get('current_price', 0)
            price_change_1h = signals.get('price_change_1h', 0)
            price_change_4h = signals.get('price_change_4h', 0)
            
            # 3分钟指标
            ema20_3m = signals.get('ema20_3m', 0)
            macd_3m = signals.get('macd_3m', 0)
            rsi7_3m = signals.get('rsi7_3m', 0)
            rsi14_3m = signals.get('rsi14_3m', 0)
            
            # 4小时指标
            ema20_4h = signals.get('ema20_4h', 0)
            ema50_4h = signals.get('ema50_4h', 0)
            macd_4h = signals.get('macd_4h', 0)
            rsi7_4h = signals.get('rsi7_4h', 0)
            rsi14_4h = signals.get('rsi14_4h', 0)
            atr_4h = signals.get('atr_4h', 0)
            
            # 趋势判断
            price_vs_ema20_3m = "高于" if current_price > ema20_3m else "低于" if current_price < ema20_3m else "等于"
            price_vs_ema20_4h = "高于" if current_price > ema20_4h else "低于" if current_price < ema20_4h else "等于"
            macd_signal_3m = "看涨" if macd_3m > 0 else "看跌" if macd_3m < 0 else "中性"
            macd_signal_4h = "看涨" if macd_4h > 0 else "看跌" if macd_4h < 0 else "中性"
            rsi_status_3m = "超买" if rsi14_3m > 70 else "超卖" if rsi14_3m < 30 else "正常"
            rsi_status_4h = "超买" if rsi14_4h > 70 else "超卖" if rsi14_4h < 30 else "正常"
            
            # 序列数据摘要（保留关键趋势信息）
            intraday_series = signals.get('intraday_series', {})
            longer_term_series = signals.get('longer_term_series', {})
            
            intraday_summary = self._format_series_summary(intraday_series, "3分钟")
            longer_term_summary = self._format_series_summary(longer_term_series, "4小时")
            
            formatted_lines.append(
                f"  {symbol}:\n"
                f"    【价格信息】\n"
                f"      - 当前价格: {current_price:.2f}\n"
                f"      - 1小时涨跌: {price_change_1h:+.2f}%\n"
                f"      - 4小时涨跌: {price_change_4h:+.2f}%\n"
                f"    【3分钟指标】\n"
                f"      - EMA20: {ema20_3m:.2f} (价格{price_vs_ema20_3m}EMA20)\n"
                f"      - MACD: {macd_3m:.2f} ({macd_signal_3m})\n"
                f"      - RSI7: {rsi7_3m:.2f}\n"
                f"      - RSI14: {rsi14_3m:.2f} ({rsi_status_3m})\n"
                f"    【4小时指标】\n"
                f"      - EMA20: {ema20_4h:.2f} (价格{price_vs_ema20_4h}EMA20)\n"
                f"      - EMA50: {ema50_4h:.2f}\n"
                f"      - MACD: {macd_4h:.2f} ({macd_signal_4h})\n"
                f"      - RSI7: {rsi7_4h:.2f}\n"
                f"      - RSI14: {rsi14_4h:.2f} ({rsi_status_4h})\n"
                f"      - ATR: {atr_4h:.2f} (波动率)\n"
                f"    【3分钟序列数据摘要】\n{intraday_summary if intraday_summary else '        无数据'}\n"
                f"    【4小时序列数据摘要】\n{longer_term_summary if longer_term_summary else '        无数据'}"
            )
        
        return "\n".join(formatted_lines) if formatted_lines else "无信号数据"

    def _format_series_summary(self, series_data: dict, label: str) -> str:
        """格式化序列数据摘要"""
        if not series_data:
            return ""
        
        mid_prices = series_data.get('mid_prices', [])
        ema20_values = series_data.get('ema20_values', [])
        macd_values = series_data.get('macd_values', [])
        rsi7_values = series_data.get('rsi7_values', [])
        
        if not mid_prices:
            return ""
        
        recent_prices = mid_prices[-10:] if len(mid_prices) > 10 else mid_prices
        
        def format_value(val: Any) -> str:
            """格式化单个值，处理NaN和None"""
            if val is None:
                return 'N/A'
            if isinstance(val, float) and (val != val):  # NaN check
                return 'N/A'
            return f'{val:.2f}'
        
        ema20_recent = [format_value(e) for e in (ema20_values[-10:] if ema20_values else [])]
        macd_recent = [format_value(m) for m in (macd_values[-10:] if macd_values else [])]
        rsi7_recent = [format_value(r) for r in (rsi7_values[-10:] if rsi7_values else [])]
        
        return (
            f"        最近价格序列: {[f'{p:.2f}' for p in recent_prices]}\n"
            f"        最近EMA20序列: {ema20_recent}\n"
            f"        最近MACD序列: {macd_recent}\n"
            f"        最近RSI7序列: {rsi7_recent}"
        )

    def _format_account_info(self, account_info: dict) -> str:
        """格式化账户信息"""
        if not account_info:
            return "无账户信息"
        
        total_equity = account_info.get('total_equity')
        available_balance = account_info.get('available_balance')
        total_pnl = account_info.get('total_pnl')
        total_pnl_pct = account_info.get('total_pnl_pct')
        margin_used = account_info.get('margin_used')
        margin_used_pct = account_info.get('margin_used_pct')
        
        lines = []
        if total_equity is not None:
            lines.append(f"- 账户净值: {total_equity:.2f} USDT")
        if available_balance is not None:
            lines.append(f"- 可用余额: {available_balance:.2f} USDT")
        if total_pnl is not None:
            pnl_str = f"{total_pnl:+.2f} USDT"
            if total_pnl_pct is not None:
                pnl_str += f" ({total_pnl_pct:+.2f}%)"
            lines.append(f"- 总盈亏: {pnl_str}")
        if margin_used is not None:
            margin_str = f"{margin_used:.2f} USDT"
            if margin_used_pct is not None:
                margin_str += f" ({margin_used_pct:.2f}%)"
            lines.append(f"- 已用保证金: {margin_str}")
        
        return "\n".join(lines) if lines else "无账户信息"

    def _format_positions(self, positions: list) -> str:
        """格式化持仓信息（包含完整信息）"""
        if not positions:
            return "无持仓"
        
        formatted_lines = []
        for pos in positions:
            symbol = pos.get('symbol', 'N/A')
            side = pos.get('side', 'N/A')
            size = pos.get('size', 0)
            entry_price = pos.get('entry_price', 0)
            mark_price = pos.get('mark_price', 0)
            unrealized_pnl = pos.get('unrealized_pnl', 0)
            leverage = pos.get('leverage', 1)
            liquidation_price = pos.get('liquidation_price')
            margin_used = pos.get('margin_used')
            update_time = pos.get('update_time')
            
            pnl_percent = (unrealized_pnl / (entry_price * size)) * 100 if entry_price * size > 0 else 0
            pnl_status = "盈利" if unrealized_pnl > 0 else "亏损" if unrealized_pnl < 0 else "持平"
            
            # 格式化更新时间
            update_time_str = "N/A"
            if update_time:
                try:
                    dt = datetime.fromtimestamp(update_time / 1000)  # 毫秒转秒
                    update_time_str = dt.strftime('%Y-%m-%d %H:%M:%S')
                except Exception:
                    update_time_str = str(update_time)
            
            formatted_lines.append(
                f"  {symbol}:\n"
                f"    - 方向: {side}\n"
                f"    - 数量: {size:.4f}\n"
                f"    - 杠杆: {leverage}x\n"
                f"    - 开仓价: {entry_price:.2f}\n"
                f"    - 标记价: {mark_price:.2f}\n"
                f"    - 未实现盈亏: {unrealized_pnl:+.2f} ({pnl_percent:+.2f}%) [{pnl_status}]\n"
                f"    - 清算价格: {liquidation_price:.2f if liquidation_price else 'N/A'}\n"
                f"    - 已用保证金: {margin_used:.2f if margin_used else 'N/A'} USDT\n"
                f"    - 更新时间: {update_time_str}"
            )
        
        return "\n".join(formatted_lines) if formatted_lines else "无持仓"
    
    def _format_candidate_coins(self, coins: list, coin_sources: dict) -> str:
        """格式化候选币种及其来源"""
        if not coins:
            return "无候选币种"
        
        formatted_lines = []
        for coin in coins:
            sources = coin_sources.get(coin, [])
            sources_str = ", ".join(sources) if sources else "配置币种"
            formatted_lines.append(f"  - {coin} (来源: {sources_str})")
        
        return "\n".join(formatted_lines) if formatted_lines else "无候选币种"
    
    def _format_oi_top_data(self, oi_top_data_map: dict) -> str:
        """格式化 OI Top 数据"""
        if not oi_top_data_map:
            return "无 OI Top 数据"
        
        formatted_lines = []
        for symbol, data in oi_top_data_map.items():
            oi_change = data.get('oi_change', 0)
            oi_change_percent = data.get('oi_change_percent', 0)
            time_range = data.get('time_range', '')
            
            formatted_lines.append(
                f"  {symbol}:\n"
                f"    - 持仓量变化: {oi_change:+.2f} ({oi_change_percent:+.2f}%)\n"
                f"    - 时间范围: {time_range if time_range else 'N/A'}"
            )
        
        return "\n".join(formatted_lines) if formatted_lines else "无 OI Top 数据"

    def _build_user_prompt(self, state: DecisionState):
        """构建结构化的用户提示词，保留K线数据"""
        coins = state.get('candidate_symbols', [])
        market_data_map = state.get('market_data_map', {})
        signal_data_map = state.get('signal_data_map', {})
        account_balance = state.get('account_balance', 0.0)
        positions = state.get('positions', [])
        coin_sources = state.get('coin_sources', {})
        oi_top_data_map = state.get('oi_top_data_map', {})
        
        # 获取详细账户信息
        account_info = {}
        if self.exchange_service:
            try:
                account_info = self.exchange_service.get_account_info()
            except Exception as e:
                logger.warning(f"无法获取详细账户信息: {e}")
                # 如果获取失败，至少使用余额
                if account_balance == 0.0:
                    try:
                        account_balance = self.exchange_service.get_balance()
                    except Exception:
                        pass
        
        # 获取杠杆配置
        btc_eth_leverage = self.trader_cfg.get('btc_eth_leverage', 5)
        altcoin_leverage = self.trader_cfg.get('altcoin_leverage', 5)
        
        # 格式化各部分信息
        account_info_str = self._format_account_info(account_info)
        market_info = self._format_market_data(market_data_map)
        signal_info = self._format_signal_data(signal_data_map)
        positions_info = self._format_positions(positions)
        candidate_coins_info = self._format_candidate_coins(coins, coin_sources)
        oi_top_info = self._format_oi_top_data(oi_top_data_map)
        
        user_prompt = f"""
# 交易决策分析请求

## 一、账户信息
{account_info_str}
- 当前持仓数量: {len(positions)} 个

## 二、持仓详情
{positions_info}

## 三、候选币种及来源
{candidate_coins_info}

## 四、OI Top 数据（持仓量增长Top币种）
{oi_top_info}

## 五、市场数据（包含K线数据）
{market_info}

## 六、技术信号分析（包含指标序列数据）
{signal_info}

## 七、交易配置
- BTC/ETH 杠杆上限: {btc_eth_leverage}x
- 山寨币杠杆上限: {altcoin_leverage}x

## 八、决策要求
请根据以上信息，对每个候选币种和现有持仓进行综合分析，并给出交易决策：

### 对于候选币种（开仓决策）：
1. 分析K线数据，识别价格趋势和形态
2. 结合3分钟和4小时指标，评估多时间框架信号
3. 观察序列数据的变化趋势
4. 参考 OI Top 数据（如果可用），评估持仓量变化
5. 考虑账户余额和现有持仓情况
6. 给出明确的交易建议：开多、开空或等待

### 对于现有持仓（平仓决策）：
1. 评估持仓的盈亏情况
2. 分析当前市场信号是否支持继续持有
3. 考虑清算价格风险
4. 给出明确的交易建议：平多、平空或持有

### 决策格式要求：
请以结构化的JSON数组格式返回决策结果，每个决策包含：
- symbol: 币种符号（如 "BTC/USDT"）
- action: 操作类型，必须是以下之一：
  - "open_long": 开多仓
  - "open_short": 开空仓
  - "close_long": 平多仓
  - "close_short": 平空仓
  - "hold": 持有（对现有持仓）
  - "wait": 等待（对候选币种，暂不开仓）
- leverage: 杠杆倍数（开仓时必填，1-{altcoin_leverage}，BTC/ETH最高{btc_eth_leverage}）
- position_size_usd: 仓位大小（USD，开仓时必填）
- stop_loss: 止损价格（开仓时必填，必须>0）
- take_profit: 止盈价格（开仓时必填，必须>0）
- confidence: 信心度 (0-100)
- risk_usd: 最大美元风险（开仓时必填）
- reasoning: 决策理由（需引用具体的K线形态、指标信号、OI Top数据等）

### 重要约束：
1. 风险回报比必须≥3:1（收益/风险 ≥ 3）
2. BTC/ETH 单币种仓位价值不能超过账户净值的10倍
3. 山寨币单币种仓位价值不能超过账户净值的1.5倍
4. 开仓操作必须提供完整的杠杆、仓位大小、止损、止盈参数
5. 止损和止盈价格必须合理（做多时止损<止盈，做空时止损>止盈）

请返回JSON数组格式的决策列表。
"""
        logger.debug(f"构建用户提示词完成 (持仓: {len(positions)}, 币种: {len(coins)})")
        return user_prompt

    def run(self, state: DecisionState) -> DecisionState:
        """执行AI决策"""
        if not hasattr(self, 'llm') or self.llm is None:
            logger.error("LLM未初始化，AI模型可能未启用或初始化失败")
            return state
        
        try:
            user_prompt = self._build_user_prompt(state)
            logger.debug(f"用户提示词构建完成，长度: {len(user_prompt)}字符")
            
            messages = [
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=user_prompt),
            ]
            
            logger.info("调用LLM进行决策...")
            response = self.llm.invoke(messages)
            
            # 使用结构化输出，直接获取DecisionOutput对象
            if isinstance(response, DecisionOutput):
                # 使用model_dump()（Pydantic v2）或dict()（Pydantic v1）
                try:
                    decisions = [item.model_dump() for item in response.decisions]
                except AttributeError:
                    # 回退到dict()方法（Pydantic v1）
                    decisions = [item.dict() for item in response.decisions]
                
                decision_count = len(decisions)
                logger.info(f"AI决策完成，共{decision_count}个决策")
                state['ai_decision'] = {
                    'decisions': decisions,
                    'raw_response': None  # 结构化输出不包含原始响应
                }
            else:
                # 回退到手动解析（如果结构化输出未启用）
                logger.warning("收到非结构化响应，尝试手动解析")
                if hasattr(response, 'content'):
                    import json
                    response_text = response.content
                    # 提取JSON（如果被代码块包裹）
                    if '```json' in response_text:
                        json_start = response_text.find('```json') + 7
                        json_end = response_text.find('```', json_start)
                        response_text = response_text[json_start:json_end].strip()
                    elif '```' in response_text:
                        json_start = response_text.find('```') + 3
                        json_end = response_text.find('```', json_start)
                        response_text = response_text[json_start:json_end].strip()
                    
                    try:
                        decisions = json.loads(response_text)
                        decision_count = len(decisions) if isinstance(decisions, list) else 1
                        logger.info(f"AI决策完成，共{decision_count}个决策")
                        state['ai_decision'] = {
                            'decisions': decisions if isinstance(decisions, list) else [decisions],
                            'raw_response': response.content
                        }
                    except json.JSONDecodeError as e:
                        logger.error(f"JSON解析失败: {e}")
                        state['ai_decision'] = {
                            'error': f"JSON解析失败: {str(e)}",
                            'raw_response': response.content
                        }
                else:
                    logger.error("无法解析响应格式")
                    state['ai_decision'] = {
                        'error': "无法解析响应格式",
                        'raw_response': str(response)
                    }
            
            return state
        except Exception as e:
            logger.error(f"AI决策执行失败: {e}", exc_info=True)
            return state