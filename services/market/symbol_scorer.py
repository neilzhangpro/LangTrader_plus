"""
币种评分器 - 使用AI或技术指标对币种进行评分
"""
from typing import List, Dict, Optional
import re
import json
import threading
from pathlib import Path
from datetime import datetime, timedelta
from utils.logger import logger
from services.market.indicators import IndicatorCalculator
from langchain_core.messages import SystemMessage, HumanMessage

# 前向引用，避免循环导入
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from services.market.monitor import MarketMonitor


class SymbolScorer:
    """币种评分器 - 使用AI或技术指标对币种进行评分，带缓存机制"""
    
    def __init__(
        self, 
        ai_model_config: Optional[dict] = None,
        cache_dir: str = "symbol_score_cache",
        cache_expiry_hours: int = 1
    ):
        """初始化币种评分器
        
        Args:
            ai_model_config: AI模型配置，如果提供且enabled=True，将使用LLM评分
            cache_dir: 缓存目录路径
            cache_expiry_hours: 缓存过期时间（小时）
        """
        self.ai_model_config = ai_model_config
        self.llm = None
        if ai_model_config and ai_model_config.get('enabled'):
            self.llm = self._init_llm(ai_model_config)
            if self.llm:
                logger.info("✅ AI模型已初始化，将使用LLM进行币种评分")
            else:
                logger.warning("⚠️ AI模型初始化失败，将回退到技术指标评分")
        
        # 缓存配置
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_expiry = timedelta(hours=cache_expiry_hours)
        
        # 内存缓存：{symbol: (score, timestamp)}
        self._memory_cache: Dict[str, tuple] = {}
        self._memory_cache_lock = threading.Lock()
        
        logger.info(f"SymbolScorer 初始化完成 (cache_dir={cache_dir}, cache_expiry={cache_expiry_hours}小时)")
    
    def _init_llm(self, ai_model_config: dict):
        """初始化LLM（使用统一的LLM工厂）"""
        from utils.llm_factory import LLMFactory
        return LLMFactory.create_llm(ai_model_config)
    
    def score_symbols(self, symbols: List[str], market_monitor: 'MarketMonitor') -> List[dict]:
        """批量评分币种（带缓存优化）
        
        Args:
            symbols: 要评分的币种列表
            market_monitor: MarketMonitor实例，用于获取K线数据
            
        Returns:
            评分结果列表，每个元素包含 {'symbol': str, 'score': int}
        """
        if self.llm:
            return self._score_with_llm_cached(symbols, market_monitor)
        else:
            return self._score_with_technical(symbols, market_monitor)
    
    def _score_with_llm_cached(self, symbols: List[str], market_monitor: 'MarketMonitor') -> List[dict]:
        """使用LLM进行评分（带缓存）"""
        # 1. 检查缓存
        cached_scores = {}
        uncached_symbols = []
        
        for symbol in symbols:
            cached_score = self._get_cached_score(symbol)
            if cached_score is not None:
                cached_scores[symbol] = cached_score
            else:
                uncached_symbols.append(symbol)
        
        cache_hit_count = len(cached_scores)
        cache_miss_count = len(uncached_symbols)
        
        if cache_hit_count > 0:
            logger.info(f"📦 缓存命中: {cache_hit_count}/{len(symbols)} 个币种")
        
        # 2. 只对未缓存的币种进行LLM评分
        new_scores = []
        if uncached_symbols:
            logger.info(f"🤖 开始使用LLM对 {cache_miss_count} 个币种进行AI评分...")
            new_scores = self._score_with_llm(uncached_symbols, market_monitor)
            
            # 3. 保存新评分到缓存
            for item in new_scores:
                self._save_score_cache(item['symbol'], item['score'])
                cached_scores[item['symbol']] = item['score']
        
        # 4. 合并结果
        result = []
        for symbol in symbols:
            if symbol in cached_scores:
                result.append({
                    'symbol': symbol,
                    'score': cached_scores[symbol]
                })
        
        total_scored = len(result)
        logger.info(f"✅ 评分完成: 共 {total_scored} 个币种（缓存: {cache_hit_count}, 新评分: {len(new_scores)}）")
        return result
    
    def _score_with_llm(self, symbols: List[str], market_monitor: 'MarketMonitor') -> List[dict]:
        """使用LLM进行评分"""
        scored_coins = []
        
        logger.info(f"🤖 开始使用LLM对 {len(symbols)} 个币种进行AI评分...")
        
        # 批量处理（每批10个币种，避免token过多）
        batch_size = 10
        for i in range(0, len(symbols), batch_size):
            batch_symbols = symbols[i:i+batch_size]
            batch_scores = self._score_batch_with_llm(batch_symbols, market_monitor)
            scored_coins.extend(batch_scores)
            
            if (i + batch_size) % 50 == 0:
                logger.info(f"📊 已评分 {min(i + batch_size, len(symbols))}/{len(symbols)} 个币种...")
        
        logger.info(f"✅ AI评分完成，共评分 {len(scored_coins)} 个币种")
        return scored_coins
    
    def _score_batch_with_llm(self, symbols: List[str], market_monitor: 'MarketMonitor') -> List[dict]:
        """使用LLM批量评分币种"""
        scored_coins = []
        
        for symbol in symbols:
            try:
                # 获取K线数据
                klines_3m = market_monitor.get_klines(symbol, "3m", limit=100)
                klines_4h = market_monitor.get_klines(symbol, "4h", limit=100)
                
                if not klines_3m or not klines_4h or len(klines_3m) < 20 or len(klines_4h) < 20:
                    continue
                
                # 计算技术指标
                ema20_3m = IndicatorCalculator.calculate_ema(klines_3m, 20)
                ema20_4h = IndicatorCalculator.calculate_ema(klines_4h, 20)
                ema50_4h = IndicatorCalculator.calculate_ema(klines_4h, 50)
                macd_3m = IndicatorCalculator.calculate_macd(klines_3m)
                macd_4h = IndicatorCalculator.calculate_macd(klines_4h)
                rsi7_3m = IndicatorCalculator.calculate_rsi(klines_3m, 7)
                rsi14_3m = IndicatorCalculator.calculate_rsi(klines_3m, 14)
                rsi14_4h = IndicatorCalculator.calculate_rsi(klines_4h, 14)
                atr_4h = IndicatorCalculator.calculate_atr(klines_4h, 14)
                
                current_price = klines_3m[-1].close
                
                # 计算价格变化
                price_change_1h = 0.0
                if len(klines_3m) >= 20:
                    price_1h_ago = klines_3m[-20].close
                    price_change_1h = (current_price - price_1h_ago) / price_1h_ago * 100
                
                price_change_4h = 0.0
                if len(klines_4h) >= 2:
                    price_4h_ago = klines_4h[-2].close
                    price_change_4h = (current_price - price_4h_ago) / price_4h_ago * 100 if price_4h_ago > 0 else 0.0
                
                # 构建提示词
                system_prompt = """你是一个专业的加密货币交易分析师。你的任务是对币种进行综合评分（0-100分），评估其交易潜力。

评分标准：
1. 技术指标信号强度（40分）
   - EMA趋势：价格相对EMA20/EMA50的位置
   - MACD信号：金叉/死叉、动量强度
   - RSI状态：超买/超卖程度
   - ATR波动率：市场活跃度

2. 价格动量（30分）
   - 短期价格变化（1小时）
   - 中期价格变化（4小时）
   - 价格趋势一致性

3. 市场结构（30分）
   - 多时间框架一致性（3分钟 vs 4小时）
   - 趋势强度
   - 突破潜力

请只返回一个0-100的整数分数，不要其他解释。"""

                user_prompt = f"""币种: {symbol}

【价格信息】
- 当前价格: {current_price:.4f}
- 1小时涨跌: {price_change_1h:+.2f}%
- 4小时涨跌: {price_change_4h:+.2f}%

【3分钟指标】
- EMA20: {ema20_3m:.4f} (价格{'高于' if current_price > ema20_3m else '低于'}EMA20)
- MACD: {macd_3m:.4f} ({'看涨' if macd_3m > 0 else '看跌'})
- RSI7: {rsi7_3m:.2f}
- RSI14: {rsi14_3m:.2f} ({'超买' if rsi14_3m > 70 else '超卖' if rsi14_3m < 30 else '正常'})

【4小时指标】
- EMA20: {ema20_4h:.4f} (价格{'高于' if current_price > ema20_4h else '低于'}EMA20)
- EMA50: {ema50_4h:.4f}
- MACD: {macd_4h:.4f} ({'看涨' if macd_4h > 0 else '看跌'})
- RSI14: {rsi14_4h:.2f} ({'超买' if rsi14_4h > 70 else '超卖' if rsi14_4h < 30 else '正常'})
- ATR: {atr_4h:.4f} (波动率)

请给出综合评分（0-100的整数）："""

                # 调用LLM
                messages = [
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=user_prompt)
                ]
                
                response = self.llm.invoke(messages)
                
                # 解析分数
                score_text = response.content.strip()
                # 尝试提取数字
                score_match = re.search(r'\d+', score_text)
                if score_match:
                    score = int(score_match.group())
                    score = max(0, min(100, score))  # 确保在0-100范围内
                else:
                    logger.warning(f"⚠️ {symbol} LLM返回格式异常: {score_text}，使用默认分50")
                    score = 50
                
                scored_coins.append({
                    'symbol': symbol,
                    'score': score
                })
                
            except Exception as e:
                logger.debug(f"⚠️ {symbol} AI评分失败: {e}")
                continue
        
        return scored_coins
    
    def _score_with_technical(self, symbols: List[str], market_monitor: 'MarketMonitor') -> List[dict]:
        """使用技术指标进行评分（回退方案）"""
        scored_coins = []
        
        logger.info(f"📊 开始使用技术指标对 {len(symbols)} 个币种进行评分...")
        
        for symbol in symbols:
            try:
                klines_3m = market_monitor.get_klines(symbol, "3m", limit=100)
                klines_4h = market_monitor.get_klines(symbol, "4h", limit=100)
                
                if not klines_3m or not klines_4h or len(klines_3m) < 20 or len(klines_4h) < 20:
                    continue
                
                # 计算技术指标
                ema20_3m = IndicatorCalculator.calculate_ema(klines_3m, 20)
                ema20_4h = IndicatorCalculator.calculate_ema(klines_4h, 20)
                macd_3m = IndicatorCalculator.calculate_macd(klines_3m)
                macd_4h = IndicatorCalculator.calculate_macd(klines_4h)
                rsi14_3m = IndicatorCalculator.calculate_rsi(klines_3m, 14)
                rsi14_4h = IndicatorCalculator.calculate_rsi(klines_4h, 14)
                
                current_price = klines_3m[-1].close
                
                # 简化的评分算法（0-100分）
                score = 50  # 基础分
                
                # 价格相对EMA位置（3分钟）
                if current_price > ema20_3m:
                    score += 10
                else:
                    score -= 10
                
                # 价格相对EMA位置（4小时）
                if current_price > ema20_4h:
                    score += 15
                else:
                    score -= 15
                
                # MACD信号（3分钟）
                if macd_3m > 0:
                    score += 10
                else:
                    score -= 10
                
                # MACD信号（4小时）
                if macd_4h > 0:
                    score += 15
                else:
                    score -= 15
                
                # RSI状态（避免极端超买/超卖）
                if 30 < rsi14_3m < 70:
                    score += 5
                if 30 < rsi14_4h < 70:
                    score += 5
                
                # 确保分数在0-100范围内
                score = max(0, min(100, score))
                
                scored_coins.append({
                    'symbol': symbol,
                    'score': score
                })
            except Exception as e:
                logger.debug(f"⚠️ {symbol} 评分失败: {e}")
                continue
        
        logger.info(f"✅ 技术指标评分完成，共评分 {len(scored_coins)} 个币种")
        return scored_coins
    
    def _get_cached_score(self, symbol: str) -> Optional[int]:
        """获取缓存的评分（先检查内存缓存，再检查文件缓存）"""
        # 1. 检查内存缓存
        with self._memory_cache_lock:
            if symbol in self._memory_cache:
                score, timestamp = self._memory_cache[symbol]
                # 检查是否过期
                if datetime.now() - timestamp < self.cache_expiry:
                    return score
                else:
                    # 过期，从内存缓存中移除
                    del self._memory_cache[symbol]
        
        # 2. 检查文件缓存
        cached_score = self._load_score_from_file_cache(symbol)
        if cached_score is not None:
            # 更新内存缓存
            with self._memory_cache_lock:
                self._memory_cache[symbol] = (cached_score, datetime.now())
            return cached_score
        
        return None
    
    def _save_score_cache(self, symbol: str, score: int):
        """保存评分到缓存（内存 + 文件）"""
        timestamp = datetime.now()
        
        # 保存到内存缓存
        with self._memory_cache_lock:
            self._memory_cache[symbol] = (score, timestamp)
        
        # 保存到文件缓存
        try:
            # 使用符号名作为文件名（避免特殊字符）
            safe_symbol = symbol.replace('/', '_').replace('\\', '_')
            cache_file = self.cache_dir / f"{safe_symbol}.json"
            
            cache_data = {
                'symbol': symbol,
                'score': score,
                'cached_at': timestamp.isoformat()
            }
            
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.debug(f"⚠️ 保存 {symbol} 评分缓存失败: {e}")
    
    def _load_score_from_file_cache(self, symbol: str) -> Optional[int]:
        """从文件缓存加载评分"""
        try:
            safe_symbol = symbol.replace('/', '_').replace('\\', '_')
            cache_file = self.cache_dir / f"{safe_symbol}.json"
            
            if not cache_file.exists():
                return None
            
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 检查缓存是否过期
            cached_at = datetime.fromisoformat(data['cached_at'])
            cache_age = datetime.now() - cached_at
            
            if cache_age > self.cache_expiry:
                # 缓存过期，删除文件
                try:
                    cache_file.unlink()
                except:
                    pass
                return None
            
            return int(data['score'])
        except Exception as e:
            logger.debug(f"⚠️ 加载 {symbol} 评分缓存失败: {e}")
            return None
    
    def clear_cache(self, symbol: Optional[str] = None):
        """清除缓存
        
        Args:
            symbol: 如果提供，只清除该币种的缓存；否则清除所有缓存
        """
        if symbol:
            # 清除单个币种的缓存
            with self._memory_cache_lock:
                if symbol in self._memory_cache:
                    del self._memory_cache[symbol]
            
            safe_symbol = symbol.replace('/', '_').replace('\\', '_')
            cache_file = self.cache_dir / f"{safe_symbol}.json"
            if cache_file.exists():
                try:
                    cache_file.unlink()
                    logger.info(f"✅ 已清除 {symbol} 的评分缓存")
                except Exception as e:
                    logger.warning(f"⚠️ 清除 {symbol} 缓存失败: {e}")
        else:
            # 清除所有缓存
            with self._memory_cache_lock:
                self._memory_cache.clear()
            
            # 清除所有文件缓存
            try:
                for cache_file in self.cache_dir.glob("*.json"):
                    cache_file.unlink()
                logger.info(f"✅ 已清除所有评分缓存")
            except Exception as e:
                logger.warning(f"⚠️ 清除文件缓存失败: {e}")

