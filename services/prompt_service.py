"""
提示词服务
从数据库加载系统提示词
如果用户设置的trader有自定义提示词
则使用自定义提示词
"""
from config.settings import Settings
from models.prompt_template import PromptTemplate
from sqlmodel import select
from models.trader import Trader

# services/prompt_service.py
class PromptService:
    def __init__(self, settings: Settings):
        self.settings = settings

    def get_prompt_by_name(self, name: str) -> str | None:
        """获取提示词内容（返回字符串）"""
        try:
            with self.settings.get_session() as session:
                prompt = session.exec(
                    select(PromptTemplate).where(PromptTemplate.name == name)
                ).first()
                # 在会话关闭前提取 content
                return prompt.content if prompt else None
        except Exception as e:
            print(f"Error getting prompt by name: {e}")
            return None
    
    def get_prompt_by_trader(self, trader_id: str) -> str | None:
        """获取交易员的提示词（返回字符串）"""
        try:
            with self.settings.get_session() as session:
                trader = session.exec(
                    select(Trader).where(Trader.id == trader_id)
                ).first()
                
                if trader:
                    # 如果有自定义提示词且覆盖基础提示词
                    if trader.custom_prompt and trader.override_base_prompt:
                        return trader.custom_prompt
                    
                    # 否则获取系统提示词模板
                    template_name = trader.system_prompt_template or "default"
                    template = session.exec(
                        select(PromptTemplate).where(
                            PromptTemplate.name == template_name
                        )
                    ).first()
                    
                    if template:
                        base_content = template.content
                        # 如果有自定义提示词但不覆盖，则追加
                        if trader.custom_prompt:
                            return f"{base_content}\n\n{trader.custom_prompt}"
                        return base_content
                    else:
                        # 如果模板不存在，返回自定义提示词或 None
                        return trader.custom_prompt
                else:
                    # 交易员不存在，返回默认提示词
                    return self.get_prompt_by_name("default")
        except Exception as e:
            print(f"Error getting prompt by trader: {e}")
            return None