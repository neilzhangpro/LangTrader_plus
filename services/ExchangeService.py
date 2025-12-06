from config.settings import Settings
from models.exchange import Exchange
import ccxt
from utils.logger import logger
from sqlmodel import select
from typing import Optional
from services.trader.hyperliquid_trder import hyperliquid_trader

class ExchangeService:
    """
    ExchangeService class
    """

    def __init__(self,exchange_config: dict, settings: Settings):
        self.settings = settings
        self.exchange_config = exchange_config
        self.exchange_id = exchange_config.get('id')
        logger.info(f"Exchange {self.exchange_id} initialized")
        logger.info(f"Exchange {self.exchange_config}")
        #CCXT 初始化
        self._ccxt_exchange: Optional[ccxt.Exchange] = None
        #初始化 CCXT 交易所
        self._init_ccxt_exchange()
    
    def _init_ccxt_exchange(self):
        """初始化 CCXT 交易所"""
        #CEX使用CCXT, DEX暂时使用具备SDK的交易所
        try:
            if self.exchange_config.get('type') == 'CEX':
                #cex
                self._init_cex()
            elif self.exchange_config.get('type') == 'DEX':
                #dex
                self._init_dex()
            else:
                logger.error(f"❌ 不支持的交易所类型: {self.exchange_config.get('type')}")
                raise ValueError(f"不支持的交易所类型: {self.exchange_config.get('type')}")
        except Exception as e:
            logger.error(f"❌ 初始化 CCXT 交易所失败: {e}", exc_info=True)
            raise
    
    def _init_cex(self):
        """初始化 CEX 交易所"""
        exchange_name = self.exchange_config.get('name').lower()

        #映射CCXT的CEX交易所
        cex_mapping = {
            'binance': 'binance',
            'binance main': 'binance',
            'binance testnet': 'binance',
            'okx': 'okx',
            'okx main': 'okx',
            'gate.io': 'gate',
            'gate.io main': 'gate',
        }

        ccxt_exchange_name = cex_mapping.get(exchange_name)
        if not ccxt_exchange_name:
            logger.error(f"❌ 不支持的交易所: {exchange_name}")
            raise ValueError(f"不支持的交易所: {exchange_name}")
        
        #初始化 CCXT 交易所
        self._ccxt_exchange = ccxt.create(ccxt_exchange_name, {
            'apiKey': self.exchange_config.get('api_key'),
            'secret': self.exchange_config.get('secret_key'),
            'enableRateLimit': True,
            'options': {
                'defaultType': 'future', #默认合约交易
            }
        })
        logger.info(f"CCXT 交易所 {ccxt_exchange_name} 初始化成功")
    
    def _init_dex(self):
        exchange_name = self.exchange_config.get('name').lower()
        if exchange_name == 'hyperliquid':
            #TODO: 初始化 Hyperliquid 交易所
            self.hyperliquid_trader = hyperliquid_trader(self.exchange_config)
            return self.hyperliquid_trader
        logger.info(f"初始化 DEX 交易所成功")
        pass

    def get_balance(self, symbol: str = '') -> float:
        """获取账户余额（统一接口）"""
        try:
            if self.exchange_config.get('type') == 'CEX':
                # CEX 使用 CCXT
                if self._ccxt_exchange:
                    balance = self._ccxt_exchange.fetch_balance()
                    # 获取 USDT 余额
                    if 'USDT' in balance.get('total', {}):
                        return float(balance['total']['USDT'])
                    # 如果没有 USDT，返回第一个可用余额
                    for currency, amount in balance.get('total', {}).items():
                        if amount > 0:
                            return float(amount)
                    return 0.0
                else:
                    logger.warning("⚠️ CCXT 交易所未初始化")
                    return 0.0
            elif self.exchange_config.get('type') == 'DEX':
                # DEX 使用特定 SDK
                if self.hyperliquid_trader:
                    balance_decimal = self.hyperliquid_trader.get_balance(symbol)
                    return float(balance_decimal)
                else:
                    logger.warning("⚠️ Hyperliquid trader 未初始化")
                    return 0.0
            else:
                logger.warning(f"⚠️ 不支持的交易所类型: {self.exchange_config.get('type')}")
                return 0.0
        except Exception as e:
            logger.error(f"❌ 获取账户余额失败: {e}", exc_info=True)
            return 0.0

    def get_account_info(self) -> dict:
        """获取详细账户信息（统一接口）"""
        try:
            account_info = {
                'total_equity': None,
                'available_balance': None,
                'total_pnl': None,
                'total_pnl_pct': None,
                'margin_used': None,
                'margin_used_pct': None
            }
            
            if self.exchange_config.get('type') == 'CEX':
                # CEX 使用 CCXT
                if self._ccxt_exchange:
                    balance = self._ccxt_exchange.fetch_balance()
                    
                    # 账户净值（Total Equity）
                    total_equity = balance.get('total', {}).get('USDT', 0)
                    if total_equity == 0:
                        # 尝试从 info 中获取
                        info = balance.get('info', {})
                        total_equity = info.get('totalEquity') or info.get('totalWalletBalance') or 0
                    account_info['total_equity'] = float(total_equity) if total_equity else None
                    
                    # 可用余额（Available Balance）
                    available = balance.get('free', {}).get('USDT', 0)
                    account_info['available_balance'] = float(available) if available else None
                    
                    # 已用保证金（Margin Used）
                    used = balance.get('used', {}).get('USDT', 0)
                    if used == 0:
                        # 尝试从 info 中获取
                        info = balance.get('info', {})
                        used = info.get('totalMarginBalance') or info.get('usedMargin') or 0
                    account_info['margin_used'] = float(used) if used else None
                    
                    # 保证金使用率
                    if account_info['total_equity'] and account_info['total_equity'] > 0:
                        if account_info['margin_used']:
                            account_info['margin_used_pct'] = (account_info['margin_used'] / account_info['total_equity']) * 100
                    
                    # 总盈亏（Total PnL）- 从 info 中提取或计算
                    info = balance.get('info', {})
                    total_pnl = info.get('totalUnrealizedProfit') or info.get('totalPnL') or None
                    if total_pnl is None:
                        # 如果无法直接获取，尝试计算（需要初始余额，这里暂时返回 None）
                        pass
                    account_info['total_pnl'] = float(total_pnl) if total_pnl is not None else None
                    
                    # 总盈亏百分比
                    if account_info['total_pnl'] is not None and account_info['total_equity']:
                        # 计算百分比需要初始余额，这里暂时返回 None
                        # 或者使用 total_equity 作为基准
                        pass
                    
            elif self.exchange_config.get('type') == 'DEX':
                # DEX 使用 Hyperliquid SDK
                if self.hyperliquid_trader:
                    user_state = self.hyperliquid_trader.info.user_state(self.hyperliquid_trader.wallet_address)
                    
                    if user_state and isinstance(user_state, dict):
                        # 账户净值
                        if 'marginSummary' in user_state:
                            margin_summary = user_state['marginSummary']
                            if isinstance(margin_summary, dict):
                                account_value = margin_summary.get('accountValue', 0)
                                account_info['total_equity'] = float(account_value) if account_value else None
                        
                        # 可用余额
                        withdrawable = user_state.get('withdrawable', 0)
                        account_info['available_balance'] = float(withdrawable) if withdrawable else None
                        
                        # 已用保证金（账户净值 - 可用余额）
                        if account_info['total_equity'] and account_info['available_balance']:
                            account_info['margin_used'] = account_info['total_equity'] - account_info['available_balance']
                        
                        # 保证金使用率
                        if account_info['total_equity'] and account_info['total_equity'] > 0:
                            if account_info['margin_used']:
                                account_info['margin_used_pct'] = (account_info['margin_used'] / account_info['total_equity']) * 100
                        
                        # 总盈亏（需要从 user_state 中提取或计算）
                        # Hyperliquid 可能不直接提供总盈亏，需要计算
                        # 这里暂时返回 None，后续可以根据需要实现
                        
            return account_info
        except Exception as e:
            logger.error(f"❌ 获取账户信息失败: {e}", exc_info=True)
            return {
                'total_equity': None,
                'available_balance': None,
                'total_pnl': None,
                'total_pnl_pct': None,
                'margin_used': None,
                'margin_used_pct': None
            }

    def get_positions(self) -> list:
        """获取所有持仓（统一接口，包含完整信息）"""
        try:
            positions = []
            if self.exchange_config.get('type') == 'CEX':
                # CEX 使用 CCXT
                if self._ccxt_exchange:
                    ccxt_positions = self._ccxt_exchange.fetch_positions()
                    for pos in ccxt_positions:
                        if float(pos.get('contracts', 0)) != 0:  # 只返回有持仓的
                            # 获取清算价格
                            liquidation_price = pos.get('liquidationPrice')
                            if liquidation_price is None:
                                liquidation_price = pos.get('info', {}).get('liquidationPrice')
                            
                            # 获取已用保证金
                            margin_used = pos.get('marginUsed')
                            if margin_used is None:
                                margin_used = pos.get('info', {}).get('marginUsed')
                            
                            # 获取更新时间
                            update_time = pos.get('timestamp')
                            if update_time is None:
                                update_time = pos.get('info', {}).get('updateTime')
                            
                            positions.append({
                                'symbol': pos.get('symbol'),
                                'side': pos.get('side'),  # 'long' or 'short'
                                'size': float(pos.get('contracts', 0)),
                                'entry_price': float(pos.get('entryPrice', 0)),
                                'mark_price': float(pos.get('markPrice', 0)),
                                'unrealized_pnl': float(pos.get('unrealizedPnl', 0)),
                                'leverage': int(pos.get('leverage', 1)),
                                'liquidation_price': float(liquidation_price) if liquidation_price else None,
                                'margin_used': float(margin_used) if margin_used else None,
                                'update_time': int(update_time) if update_time else None,
                            })
            elif self.exchange_config.get('type') == 'DEX':
                # DEX 使用特定 SDK
                if self.hyperliquid_trader:
                    # TODO: 实现 Hyperliquid 持仓获取
                    # 从 user_state 中提取持仓信息
                    try:
                        user_state = self.hyperliquid_trader.info.user_state(self.hyperliquid_trader.wallet_address)
                        if user_state and isinstance(user_state, dict):
                            # Hyperliquid 的持仓信息可能在 'assetPositions' 或类似字段中
                            # 这里需要根据实际 SDK 响应格式实现
                            # 暂时返回空列表，等待 SDK 实现
                            pass
                    except Exception as e:
                        logger.warning(f"⚠️ 获取 Hyperliquid 持仓失败: {e}")
            return positions
        except Exception as e:
            logger.error(f"❌ 获取持仓失败: {e}", exc_info=True)
            return []   
