"""
交易员管理器
负责启动、停止、监控交易员
"""
from config.settings import Settings
from models.trader import Trader
from typing import Dict
from sqlmodel import select
from services.prompt_service import PromptService
import threading
from models.user import User
from typing import List
from utils.logger import logger

class TraderManager:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.prompt_service = PromptService(settings)
        self.traders: Dict[str, Trader] = {}
        self._lock = threading.Lock()

    def load_traders_from_database(self):
        #从数据库加载交易员

        with self._lock:
            # 获取所有用户，并在会话关闭前提取 user_ids
            with self.settings.get_session() as session:
                users = session.exec(select(User)).all()
                # 在会话关闭前提取所有 user.id，避免 DetachedInstanceError
                user_ids = [user.id for user in users]
                logger.info(f"📋 发现 {len(users)} 个用户，开始加载所有交易员配置...")
            
            all_traders: List[Trader] = []
            for user_id in user_ids:
                # 获取每个用户的交易员
                with self.settings.get_session() as session:
                    traders = session.exec(
                        select(Trader).where(Trader.user_id == user_id)
                    ).all()
                    logger.info(f"📋 用户 {user_id}: {len(traders)} 个交易员")
                    all_traders.extend(traders)
            
            logger.info(f"📋 总共加载 {len(all_traders)} 个交易员配置")