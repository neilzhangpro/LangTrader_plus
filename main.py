# main.py
from config.settings import Settings
from sqlmodel import select
from models import Trader
from services.trader_manager import TraderManager

def main():
    settings = Settings()
    trader_manager = TraderManager(settings)
    
    # 加载所有交易员配置
    trader_manager.load_traders_from_database()

if __name__ == "__main__":
    main()