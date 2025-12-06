from langgraph.graph import StateGraph, START, END
from decision_engine.state import DecisionState
from decision_engine.nodes.data_collector import DataCollector
from decision_engine.nodes.coin_pool import CoinPool
from utils.logger import logger
from typing import Optional
from services.market.monitor import MarketMonitor
from decision_engine.nodes.signal_analyzer import SignalAnalyzer
from decision_engine.nodes.AI_decision import AIDecision
from services.ExchangeService import ExchangeService

# 前向引用，避免循环导入
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from services.market.symbol_filter import SymbolFilter

class GraphBuilder:
    def __init__(
        self, 
        exchange_config: dict, 
        market_monitor: Optional[MarketMonitor] = None, 
        trader_cfg: Optional[dict] = None, 
        exchange_service: Optional[ExchangeService] = None,
        symbol_filter: Optional['SymbolFilter'] = None
    ):
        self.graph = StateGraph(DecisionState)
        self.exchange_config = exchange_config
        self.market_monitor = market_monitor
        self.trader_cfg = trader_cfg or {}
        self.exchange_service = exchange_service
        # 创建节点实例
        self.data_collector = DataCollector(exchange_config, market_monitor, exchange_service)
        self.coin_pool = CoinPool(trader_cfg, symbol_filter=symbol_filter)
        self.signal_analyzer = SignalAnalyzer(exchange_config)
        self.AI_decision = AIDecision(exchange_config, trader_cfg, exchange_service)


    def build_graph(self):
        """构建决策引擎图（批量模式）"""
        # 节点顺序：START -> coin_pool -> data_collector -> signal_analyzer -> AI_decision -> END
        self.graph.add_node("coin_pool", self.coin_pool.get_candidate_coins)
        self.graph.add_node("data_collector", self.data_collector.run)
        self.graph.add_node("signal_analyzer", self.signal_analyzer.run)
        self.graph.add_node("AI_decision", self.AI_decision.run)
        
        # 边的连接
        self.graph.add_edge(START, "coin_pool")
        self.graph.add_edge("coin_pool", "data_collector")
        self.graph.add_edge("data_collector", "signal_analyzer")
        self.graph.add_edge("signal_analyzer", "AI_decision")
        self.graph.add_edge("AI_decision", END)
        
        compiled_graph = self.graph.compile()
        return compiled_graph