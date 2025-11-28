"""
Pytest 配置和共享 fixtures
"""
import pytest
import os
from config.settings import Settings
from sqlmodel import SQLModel, Session, create_engine, text
from dotenv import load_dotenv

load_dotenv()


@pytest.fixture(scope="session")
def settings():
    """创建 Settings 实例（整个测试会话共享）"""
    return Settings()


@pytest.fixture(scope="function")
def db_session(settings):
    """为每个测试函数提供数据库会话"""
    with settings.get_session() as session:
        yield session


@pytest.fixture(scope="function", autouse=True)
def cleanup_test_data(db_session):
    """每个测试后自动清理测试数据"""
    yield
    # 测试后的清理逻辑（如果需要）
    pass

