# main.py
from config.settings import Settings
from services.prompt_service import PromptService
from sqlmodel import select
from models import Trader

def main():
    settings = Settings()
    prompt_service = PromptService(settings)
    
    # 从数据库查询第一个 trader
    with settings.get_session() as session:
        trader = session.exec(select(Trader)).first()
        if trader:
            prompt = prompt_service.get_prompt_by_trader(trader.id)
            print(f"交易员: {trader.name}")
            print(f"提示词: {prompt[:100] if prompt else '未找到'}...")  # 只显示前100字符
        else:
            # 如果没有 trader，使用默认提示词
            default_prompt = prompt_service.get_prompt_by_name("default")
            print(f"默认提示词: {default_prompt[:100] if default_prompt else '未找到'}...")

if __name__ == "__main__":
    main()