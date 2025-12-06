import os
import json
import threading
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
import requests
from utils.logger import logger

@dataclass
class CoinInfo:
    """币种信息（对应 Nofx 的 CoinInfo）"""
    symbol: str
    score: float = 0.0
    start_time: int = 0
    start_price: float = 0.0
    last_score: float = 0.0
    max_score: float = 0.0
    max_price: float = 0.0
    increase_percent: float = 0.0
    is_available: bool = True

@dataclass
class CoinPoolCache:
    """币种池缓存结构"""
    coins: List[CoinInfo]
    fetched_at: str  # ISO 格式时间戳
    source_type: str  # "api" or "cache"

@dataclass
class OIPosition:
    """OI Top 持仓信息"""
    symbol: str
    oi_change: float = 0.0
    oi_change_percent: float = 0.0
    time_range: str = ""

@dataclass
class OITopCache:
    """OI Top 缓存结构"""
    positions: List[OIPosition]
    fetched_at: str  # ISO 格式时间戳
    source_type: str  # "api" or "cache"
    time_range: str = ""

class CoinPoolService:
    """币种池服务 - 负责从多个信号源获取币种，带缓存和重试"""
    
    # 默认主流币种池
    DEFAULT_MAINSTREAM_COINS = [
        "BTC/USDT", "ETH/USDT", "SOL/USDT", "BNB/USDT",
        "XRP/USDT", "DOGE/USDT", "ADA/USDT", "HYPE/USDT"
    ]
    
    def __init__(
        self,
        coin_pool_url: Optional[str] = None,
        oi_top_url: Optional[str] = None,
        cache_dir: str = "coin_pool_cache",
        timeout: int = 30,
        max_retries: int = 3,
        use_default_coins: bool = False
    ):
        self.coin_pool_url = coin_pool_url
        self.oi_top_url = oi_top_url
        self.cache_dir = Path(cache_dir)
        self.timeout = timeout
        self.max_retries = max_retries
        self.use_default_coins = use_default_coins
        
        # 内存缓存（快速访问）
        self._coin_pool_memory_cache: Optional[CoinPoolCache] = None
        self._oi_top_memory_cache: Optional[OITopCache] = None
        self._memory_cache_lock = threading.Lock()
        self._cache_expiry = timedelta(hours=1)  # 内存缓存1小时过期
        
        # 确保缓存目录存在
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"CoinPoolService 初始化完成 (cache_dir={cache_dir})")
    
    def get_coin_pool(self) -> List[CoinInfo]:
        """获取币种池（带缓存和重试）"""
        # 1. 检查是否使用默认币种
        if self.use_default_coins:
            logger.info("✓ 已启用默认主流币种列表")
            return self._convert_symbols_to_coins(self.DEFAULT_MAINSTREAM_COINS)
        
        # 2. 检查API URL是否配置
        if not self.coin_pool_url or not self.coin_pool_url.strip():
            logger.warning("⚠️ 未配置币种池API URL，使用默认主流币种列表")
            return self._convert_symbols_to_coins(self.DEFAULT_MAINSTREAM_COINS)
        
        # 3. 检查内存缓存
        cached = self._get_coin_pool_memory_cache()
        if cached:
            logger.debug("✓ 使用内存缓存")
            return cached.coins
        
        # 4. 尝试从 API 获取（带重试）
        coins = self._fetch_coin_pool_with_retry()
        if coins:
            # 保存到缓存
            self._save_coin_pool_cache(coins, source_type="api")
            return coins
        
        # 5. API 失败，尝试从文件缓存加载
        logger.warning("⚠️ API请求失败，尝试使用文件缓存...")
        cached_coins = self._load_coin_pool_file_cache()
        if cached_coins:
            logger.info(f"✓ 使用文件缓存（共{len(cached_coins)}个币种）")
            return cached_coins
        
        # 6. 缓存也失败，使用默认币种
        logger.warning("⚠️ 无法加载缓存，使用默认主流币种列表")
        return self._convert_symbols_to_coins(self.DEFAULT_MAINSTREAM_COINS)
    
    def get_oi_top(self) -> List[CoinInfo]:
        """获取 OI Top 币种（带缓存和重试）"""
        # 1. 检查API URL是否配置
        if not self.oi_top_url or not self.oi_top_url.strip():
            logger.debug("⚠️ 未配置OI Top API URL，跳过")
            return []
        
        # 2. 检查内存缓存
        cached = self._get_oi_top_memory_cache()
        if cached:
            logger.debug("✓ 使用OI Top内存缓存")
            return self._convert_oi_positions_to_coins(cached.positions)
        
        # 3. 尝试从 API 获取（带重试）
        positions = self._fetch_oi_top_with_retry()
        if positions:
            # 保存到缓存
            self._save_oi_top_cache(positions, source_type="api")
            return self._convert_oi_positions_to_coins(positions)
        
        # 4. API 失败，尝试从文件缓存加载
        logger.warning("⚠️ OI Top API请求失败，尝试使用文件缓存...")
        cached_positions = self._load_oi_top_file_cache()
        if cached_positions:
            logger.info(f"✓ 使用OI Top文件缓存（共{len(cached_positions)}个币种）")
            return self._convert_oi_positions_to_coins(cached_positions)
        
        # 5. 缓存也失败，返回空列表（OI Top是可选的）
        logger.warning("⚠️ 无法加载OI Top缓存，跳过OI Top数据")
        return []
    
    def get_oi_top_details(self) -> Dict[str, OIPosition]:
        """获取 OI Top 详细信息映射（币种 -> OI Top 详细信息）"""
        # 1. 检查API URL是否配置
        if not self.oi_top_url or not self.oi_top_url.strip():
            return {}
        
        # 2. 检查内存缓存
        cached = self._get_oi_top_memory_cache()
        if cached:
            logger.debug("✓ 使用OI Top内存缓存获取详细信息")
            return {pos.symbol: pos for pos in cached.positions}
        
        # 3. 尝试从 API 获取（带重试）
        positions = self._fetch_oi_top_with_retry()
        if positions:
            # 保存到缓存
            self._save_oi_top_cache(positions, source_type="api")
            return {pos.symbol: pos for pos in positions}
        
        # 4. API 失败，尝试从文件缓存加载
        cached_positions = self._load_oi_top_file_cache()
        if cached_positions:
            logger.info(f"✓ 使用OI Top文件缓存获取详细信息（共{len(cached_positions)}个币种）")
            return {pos.symbol: pos for pos in cached_positions}
        
        # 5. 缓存也失败，返回空字典
        return {}
    
    def _fetch_coin_pool_with_retry(self) -> Optional[List[CoinInfo]]:
        """带重试的币种池获取"""
        last_err = None
        for attempt in range(1, self.max_retries + 1):
            if attempt > 1:
                logger.info(f"⚠️ 第{attempt}次重试获取币种池（共{self.max_retries}次）...")
                time.sleep(2)  # 重试前等待2秒
            
            try:
                coins = self._fetch_coin_pool_api()
                if attempt > 1:
                    logger.info(f"✓ 第{attempt}次重试成功")
                return coins
            except Exception as e:
                last_err = e
                logger.error(f"❌ 第{attempt}次请求失败: {e}")
        
        logger.error(f"❌ 所有重试均失败: {last_err}")
        return None
    
    def _fetch_coin_pool_api(self) -> List[CoinInfo]:
        """实际执行 Coin Pool API 请求"""
        logger.info("🔄 正在请求币种池API...")
        
        response = requests.get(self.coin_pool_url, timeout=self.timeout)
        response.raise_for_status()
        data = response.json()
        
        # 验证响应格式（对应 Nofx 的 CoinPoolAPIResponse）
        coins_data = []
        if isinstance(data, dict):
            if not data.get('success', True):  # 如果没有success字段，默认为True
                # 检查是否有明确的失败标志
                if 'success' in data and not data['success']:
                    raise ValueError("API返回失败状态")
            
            # 尝试多种可能的响应格式
            if 'data' in data and isinstance(data['data'], dict):
                coins_data = data['data'].get('coins', [])
            elif 'coins' in data:
                coins_data = data['coins']
            elif 'data' in data and isinstance(data['data'], list):
                coins_data = data['data']
        elif isinstance(data, list):
            coins_data = data
        else:
            raise ValueError("无效的API响应格式")
        
        if not coins_data:
            raise ValueError("币种列表为空")
        
        # 转换为 CoinInfo 对象
        coins = []
        for item in coins_data:
            if isinstance(item, dict):
                coin = CoinInfo(
                    symbol=self._normalize_symbol(item.get('symbol', item.get('pair', ''))),
                    score=float(item.get('score', 0)),
                    start_time=int(item.get('start_time', 0)),
                    start_price=float(item.get('start_price', 0)),
                    last_score=float(item.get('last_score', 0)),
                    max_score=float(item.get('max_score', 0)),
                    max_price=float(item.get('max_price', 0)),
                    increase_percent=float(item.get('increase_percent', 0)),
                    is_available=item.get('is_available', True)
                )
            else:
                # 如果只是字符串
                coin = CoinInfo(symbol=self._normalize_symbol(str(item)))
            coins.append(coin)
        
        logger.info(f"✓ 成功获取{len(coins)}个币种")
        return coins
    
    def _fetch_oi_top_with_retry(self) -> Optional[List[OIPosition]]:
        """带重试的 OI Top 获取"""
        last_err = None
        for attempt in range(1, self.max_retries + 1):
            if attempt > 1:
                logger.info(f"⚠️ 第{attempt}次重试获取OI Top（共{self.max_retries}次）...")
                time.sleep(2)  # 重试前等待2秒
            
            try:
                positions = self._fetch_oi_top_api()
                if attempt > 1:
                    logger.info(f"✓ 第{attempt}次重试成功")
                return positions
            except Exception as e:
                last_err = e
                logger.error(f"❌ 第{attempt}次请求OI Top失败: {e}")
        
        logger.error(f"❌ 所有重试均失败: {last_err}")
        return None
    
    def _fetch_oi_top_api(self) -> List[OIPosition]:
        """实际执行 OI Top API 请求"""
        logger.info("🔄 正在请求OI Top API...")
        
        response = requests.get(self.oi_top_url, timeout=self.timeout)
        response.raise_for_status()
        data = response.json()
        
        # 解析 OI Top API 响应
        positions_data = []
        time_range = ""
        
        if isinstance(data, dict):
            if not data.get('success', True):
                if 'success' in data and not data['success']:
                    raise ValueError("OI Top API返回失败状态")
            
            # 尝试多种可能的响应格式
            if 'data' in data and isinstance(data['data'], dict):
                positions_data = data['data'].get('positions', [])
                time_range = data['data'].get('time_range', '')
            elif 'positions' in data:
                positions_data = data['positions']
            elif 'data' in data and isinstance(data['data'], list):
                positions_data = data['data']
        elif isinstance(data, list):
            positions_data = data
        else:
            raise ValueError("无效的OI Top API响应格式")
        
        if not positions_data:
            raise ValueError("OI Top持仓列表为空")
        
        # 转换为 OIPosition 对象
        positions = []
        for item in positions_data:
            if isinstance(item, dict):
                position = OIPosition(
                    symbol=self._normalize_symbol(item.get('symbol', '')),
                    oi_change=float(item.get('oi_change', 0)),
                    oi_change_percent=float(item.get('oi_change_percent', 0)),
                    time_range=item.get('time_range', time_range)
                )
            else:
                # 如果只是字符串
                position = OIPosition(symbol=self._normalize_symbol(str(item)))
            positions.append(position)
        
        logger.info(f"✓ 成功获取{len(positions)}个OI Top币种（时间范围: {time_range}）")
        return positions
    
    def _normalize_symbol(self, symbol: str) -> str:
        """符号规范化（统一格式为 "BTC/USDT"）"""
        if not symbol:
            return symbol
        
        symbol = symbol.upper().strip()
        
        # 如果已经包含斜杠，直接返回
        if '/' in symbol:
            return symbol
        
        # 处理 "BTCUSDT" -> "BTC/USDT" 的转换
        if symbol.endswith('USDT'):
            base = symbol[:-4]
            return f"{base}/USDT"
        elif symbol.endswith('USD'):
            base = symbol[:-3]
            return f"{base}/USD"
        elif symbol.endswith('BTC'):
            base = symbol[:-3]
            return f"{base}/BTC"
        elif symbol.endswith('ETH'):
            base = symbol[:-3]
            return f"{base}/ETH"
        
        # 如果无法识别，返回原样
        return symbol
    
    def _save_coin_pool_cache(self, coins: List[CoinInfo], source_type: str = "api"):
        """保存币种池缓存（文件 + 内存）"""
        cache = CoinPoolCache(
            coins=coins,
            fetched_at=datetime.now().isoformat(),
            source_type=source_type
        )
        
        # 保存到内存缓存
        with self._memory_cache_lock:
            self._coin_pool_memory_cache = cache
        
        # 保存到文件缓存
        try:
            cache_file = self.cache_dir / "latest.json"
            # 将 CoinInfo 对象转换为字典
            cache_dict = {
                'coins': [asdict(coin) for coin in coins],
                'fetched_at': cache.fetched_at,
                'source_type': cache.source_type
            }
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_dict, f, indent=2, ensure_ascii=False)
            logger.info(f"💾 已保存币种池缓存到文件: {cache_file}（{len(coins)}个币种）")
        except Exception as e:
            logger.warning(f"⚠️ 保存文件缓存失败: {e}")
    
    def _load_coin_pool_file_cache(self) -> Optional[List[CoinInfo]]:
        """从文件加载币种池缓存"""
        cache_file = self.cache_dir / "latest.json"
        
        if not cache_file.exists():
            return None
        
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 检查缓存是否过期（24小时）
            fetched_at = datetime.fromisoformat(data['fetched_at'])
            cache_age = datetime.now() - fetched_at
            
            if cache_age > timedelta(hours=24):
                logger.warning(f"⚠️ 缓存数据较旧（{cache_age.days}天前），但仍可使用")
            else:
                logger.info(f"📂 缓存数据时间: {fetched_at.strftime('%Y-%m-%d %H:%M:%S')}（{cache_age.seconds//60}分钟前）")
            
            # 转换为 CoinInfo 对象
            coins = [CoinInfo(**item) for item in data['coins']]
            
            # 更新内存缓存
            cache = CoinPoolCache(
                coins=coins,
                fetched_at=data['fetched_at'],
                source_type="cache"
            )
            with self._memory_cache_lock:
                self._coin_pool_memory_cache = cache
            
            return coins
        except Exception as e:
            logger.error(f"❌ 加载文件缓存失败: {e}")
            return None
    
    def _get_coin_pool_memory_cache(self) -> Optional[CoinPoolCache]:
        """获取币种池内存缓存（如果未过期）"""
        with self._memory_cache_lock:
            if self._coin_pool_memory_cache is None:
                return None
            
            # 检查是否过期
            fetched_at = datetime.fromisoformat(self._coin_pool_memory_cache.fetched_at)
            if datetime.now() - fetched_at > self._cache_expiry:
                self._coin_pool_memory_cache = None
                return None
            
            return self._coin_pool_memory_cache
    
    def _save_oi_top_cache(self, positions: List[OIPosition], source_type: str = "api", time_range: str = ""):
        """保存 OI Top 缓存（文件 + 内存）"""
        cache = OITopCache(
            positions=positions,
            fetched_at=datetime.now().isoformat(),
            source_type=source_type,
            time_range=time_range
        )
        
        # 保存到内存缓存
        with self._memory_cache_lock:
            self._oi_top_memory_cache = cache
        
        # 保存到文件缓存
        try:
            cache_file = self.cache_dir / "oi_top_latest.json"
            cache_dict = {
                'positions': [asdict(pos) for pos in positions],
                'fetched_at': cache.fetched_at,
                'source_type': cache.source_type,
                'time_range': cache.time_range
            }
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_dict, f, indent=2, ensure_ascii=False)
            logger.info(f"💾 已保存OI Top缓存到文件: {cache_file}（{len(positions)}个币种）")
        except Exception as e:
            logger.warning(f"⚠️ 保存OI Top文件缓存失败: {e}")
    
    def _load_oi_top_file_cache(self) -> Optional[List[OIPosition]]:
        """从文件加载 OI Top 缓存"""
        cache_file = self.cache_dir / "oi_top_latest.json"
        
        if not cache_file.exists():
            return None
        
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 检查缓存是否过期（24小时）
            fetched_at = datetime.fromisoformat(data['fetched_at'])
            cache_age = datetime.now() - fetched_at
            
            if cache_age > timedelta(hours=24):
                logger.warning(f"⚠️ OI Top缓存数据较旧（{cache_age.days}天前），但仍可使用")
            else:
                logger.info(f"📂 OI Top缓存数据时间: {fetched_at.strftime('%Y-%m-%d %H:%M:%S')}（{cache_age.seconds//60}分钟前）")
            
            # 转换为 OIPosition 对象
            positions = [OIPosition(**item) for item in data['positions']]
            
            # 更新内存缓存
            cache = OITopCache(
                positions=positions,
                fetched_at=data['fetched_at'],
                source_type=data.get('source_type', 'cache'),
                time_range=data.get('time_range', '')
            )
            with self._memory_cache_lock:
                self._oi_top_memory_cache = cache
            
            return positions
        except Exception as e:
            logger.error(f"❌ 加载OI Top文件缓存失败: {e}")
            return None
    
    def _get_oi_top_memory_cache(self) -> Optional[OITopCache]:
        """获取 OI Top 内存缓存（如果未过期）"""
        with self._memory_cache_lock:
            if self._oi_top_memory_cache is None:
                return None
            
            # 检查是否过期
            fetched_at = datetime.fromisoformat(self._oi_top_memory_cache.fetched_at)
            if datetime.now() - fetched_at > self._cache_expiry:
                self._oi_top_memory_cache = None
                return None
            
            return self._oi_top_memory_cache
    
    def _convert_symbols_to_coins(self, symbols: List[str]) -> List[CoinInfo]:
        """将符号列表转换为 CoinInfo 列表"""
        return [CoinInfo(symbol=self._normalize_symbol(s)) for s in symbols]
    
    def _convert_oi_positions_to_coins(self, positions: List[OIPosition]) -> List[CoinInfo]:
        """将 OI Position 列表转换为 CoinInfo 列表"""
        return [CoinInfo(symbol=pos.symbol) for pos in positions]
