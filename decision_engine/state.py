from typing import Dict, List
from typing import TypedDict, Optional

class DecisionState(TypedDict):
    #处理的币种
    candidate_symbols: List[str] #候选币种列表
    #账户信息:余额, 持仓
    account_balance: float
    positions: List[Dict]

    #市场信息
    market_data_map: Dict[str, Dict]
    #信号信息
    signal_data_map: Dict[str, Dict]
    #AI决策信息:决策结果, 决策理由, 决策置信度,执行动作(买入,卖出,持有)
    ai_decision: Optional[Dict[str,Dict]]
    #风险检查结果,AI的决策是否通过了风险检查
    risk_approved: bool