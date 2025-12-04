from decision_engine.state import DecisionState
from utils.logger import logger
from pprint import pprint

class AIDecision:
    def __init__(self):
        logger.info(f"AIDecision initialized")

    def run(self, state: DecisionState):
        logger.info("==============AI Decision===============")
        pprint(state, width=80, depth=2)
        logger.info("========================================")