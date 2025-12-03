from langgraph.graph import StateGraph, START, END
from decision_engine.state import DecisionState
from decision_engine.nodes.data_collector import DataCollector
from decision_engine.nodes.coin_pool import CoinPool
from utils.logger import logger
from typing import Optional
from services.market.monitor import MarketMonitor

class GraphBuilder:
    def __init__(self, exchange_config: dict, market_monitor: Optional[MarketMonitor] = None, trader_cfg: Optional[dict] = None):
        self.graph = StateGraph(DecisionState)
        self.exchange_config = exchange_config
        self.market_monitor = market_monitor
        self.trader_cfg = trader_cfg or {}
        
        # 创建节点实例
        self.data_collector = DataCollector(exchange_config, market_monitor)
        self.coin_pool = CoinPool(trader_cfg)

    def build_graph(self):
        """构建决策引擎图（批量模式）"""
        # 节点顺序：START -> coin_pool -> data_collector -> ... -> END
        self.graph.add_node("coin_pool", self.coin_pool.get_candidate_coins)
        self.graph.add_node("data_collector", self.data_collector.run)
        
        # 边的连接
        self.graph.add_edge(START, "coin_pool")  # 首先获取候选币种
        self.graph.add_edge("coin_pool", "data_collector")  # 然后收集市场数据
        self.graph.add_edge("data_collector", END)  # 暂时直接结束（后续添加其他节点）
        
        logger.info(f"GraphBuilder built (批量模式)")
        compiled_graph = self.graph.compile()
        return compiled_graph