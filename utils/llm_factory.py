"""
LLM工厂类 - 统一管理LLM初始化
"""
from typing import Optional
from utils.logger import logger

try:
    from langchain_openai import ChatOpenAI
    from langchain_anthropic import ChatAnthropic
    from langchain_ollama import ChatOllama
except ImportError as e:
    logger.warning(f"LangChain导入失败: {e}")
    ChatOpenAI = None
    ChatAnthropic = None
    ChatOllama = None


class LLMFactory:
    """LLM工厂类 - 统一创建和管理LLM实例"""
    
    @staticmethod
    def create_llm(ai_model_config: dict) -> Optional[object]:
        """创建LLM实例
        
        Args:
            ai_model_config: AI模型配置字典，包含：
                - provider: 提供商 ('openai', 'anthropic', 'ollama')
                - model_name: 模型名称
                - api_key: API密钥（可选）
                - base_url: API基础URL（可选）
                - enabled: 是否启用（可选）
        
        Returns:
            LLM实例，如果创建失败则返回None
        """
        if not ai_model_config:
            logger.warning("AI模型配置为空")
            return None
        
        if not ai_model_config.get('enabled', True):
            logger.debug("AI模型未启用")
            return None
        
        provider = ai_model_config.get('provider', 'ollama')
        model_name = ai_model_config.get('model_name', 'qwen2.5:7b')
        api_key = ai_model_config.get('api_key', '')
        base_url = ai_model_config.get('base_url', '')
        temperature = ai_model_config.get('temperature', 0.0)
        
        try:
            if provider == 'openai':
                if not ChatOpenAI:
                    logger.error("ChatOpenAI未导入，请安装langchain-openai")
                    return None
                return ChatOpenAI(
                    model=model_name,
                    api_key=api_key,
                    base_url=base_url if base_url else None,
                    temperature=temperature,
                )
            elif provider == 'anthropic':
                if not ChatAnthropic:
                    logger.error("ChatAnthropic未导入，请安装langchain-anthropic")
                    return None
                return ChatAnthropic(
                    model=model_name,
                    api_key=api_key,
                    base_url=base_url if base_url else None,
                    temperature=temperature,
                )
            elif provider == 'ollama':
                if not ChatOllama:
                    logger.error("ChatOllama未导入，请安装langchain-ollama")
                    return None
                return ChatOllama(
                    model=model_name,
                    temperature=temperature,
                    base_url=base_url if base_url else 'http://localhost:11434',
                )
            else:
                logger.warning(f"不支持的LLM提供商: {provider}")
                return None
        except Exception as e:
            logger.error(f"创建LLM实例失败: {e}", exc_info=True)
            return None

