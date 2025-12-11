import ccxt
from decimal import Decimal
from services.trader.interface import ExchangeInterface
from utils.logger import logger

class CCXTTrader(ExchangeInterface):
    """CCXT交易所交易接口"""
    def __init__(self, exchange_config: dict):
        self.exchange_config = exchange_config
        exchange_id = exchange_config.get("name")
        exchange_class = getattr(ccxt, exchange_id)
        self.exchange = exchange_class({
            'wallet_address':exchange_config.get("wallet_address"),
            'privateKey':exchange_config.get("secret_key"),
            'pro':False,
            'testnet':exchange_config.get("testnet"),
            'options':{
                'fetchMarkets': {
                    'types': ['spot', 'swap'],  # 排除 'hip3'，只加载 spot 和 swap 市场
                }
            }
        })

        #判断是否支持API
        if self.exchange.has['fetchPositions']:
            self.positions = self.exchange.fetchPositions()
        else:
            self.positions = []
            logger.error(f"交易所 {exchange_id} 不支持获取持仓")

        if self.exchange.has['fetchBalance']:
            self.account_balance = self.exchange.fetchBalance()
        else:
            self.account_balance = {}
            logger.error(f"交易所 {exchange_id} 不支持获取余额")
        


    def get_balance(self, symbol: str) -> Decimal:
        """获取账户余额"""
        pass

    def get_all_position(self, symbol: str) -> Decimal:
        """获取所有持仓"""
        if symbol:
            #获取单个仓位信息
            return self.exchange.fetchPosition(symbol)
        else:
            #获取所有仓位信息
            return self.exchange.fetchPositions()

    def openLong(self, symbol: str, quantity: Decimal, leverage: int) -> Decimal:
        """开多仓"""
        pass

    def openShort(self, symbol: str, quantity: Decimal, leverage: int) -> Decimal:
        """开空仓"""
        pass

    def closeLong(self, symbol: str, quantity: Decimal) -> Decimal:
        """平多仓"""
        pass

    def closeShort(self, symbol: str, quantity: Decimal) -> Decimal:
        """平空仓"""
        pass

    def setLeverage(self, symbol: str, leverage: int) -> Decimal:
        """设置杠杆"""
        pass

    def setMarginMode(self, isCrossMargin: bool) -> Decimal:
        """设置保证金模式 全仓/逐仓 isCrossMargin=True 表示全仓, isCrossMargin=False 表示逐仓"""
        pass

    def getMarketPrice(self, symbol: str) -> Decimal:
        """获取市场价格"""
        pass

    def setStopLoss(self, symbol: str, positionSide: str, quantity: Decimal, stopPrice: Decimal) -> Decimal:
        """设置止损 positionSide=long 表示多仓, positionSide=short 表示空仓 quantity=0 表示设置所有仓位止损 stopPrice=0 表示不设置止损"""
        pass

    def setTakeProfit(self, symbol: str, positionSide: str, quantity: Decimal, takeProfitPrice: Decimal) -> Decimal:
        """设置止盈 positionSide=long 表示多仓, positionSide=short 表示空仓 quantity=0 表示设置所有仓位止盈 takeProfitPrice=0 表示不设置止盈"""
        pass

    def cancelAllOrders(self, symbol: str) -> Decimal:
        """取消所有订单"""
        pass

    def formatQuantity(self, symbol: str, quantity: Decimal) -> Decimal:
        """格式化数量到正确的精度"""
        pass