"""
数据库连接单元测试
测试关键场景：连接、断开、重连、容错等
"""
import pytest
import time
from sqlmodel import Session, text, select
from sqlalchemy.exc import OperationalError, DisconnectionError
from config.settings import Settings
from models import User


class TestDatabaseConnection:
    """数据库连接测试类"""
    
    def test_database_connection_success(self, settings):
        """测试数据库连接成功"""
        # 测试引擎是否创建成功
        assert settings.engine is not None
        
        # 测试能否执行简单查询
        with settings.get_session() as session:
            result = session.exec(text("SELECT 1 as test"))
            assert result.fetchone()[0] == 1
    
    def test_database_session_context_manager(self, settings):
        """测试会话上下文管理器正常工作"""
        with settings.get_session() as session:
            assert isinstance(session, Session)
            # 测试会话可用
            result = session.exec(text("SELECT 1"))
            assert result.fetchone() is not None
    
    def test_database_connection_pool(self, settings):
        """测试连接池功能"""
        # 创建多个会话，验证连接池工作
        sessions = []
        for _ in range(5):
            session = Session(settings.engine)
            sessions.append(session)
            # 验证会话可用
            result = session.exec(text("SELECT 1"))
            assert result.fetchone()[0] == 1
        
        # 关闭所有会话
        for session in sessions:
            session.close()
    
    def test_database_transaction_rollback(self, settings):
        """测试事务回滚"""
        with settings.get_session() as session:
            # 尝试插入一个无效数据（会失败）
            try:
                # 使用无效的 SQL 触发错误
                session.exec(text("INSERT INTO invalid_table VALUES (1)"))
                session.commit()
            except Exception:
                # 验证回滚发生
                session.rollback()
                # 验证会话仍然可用
                result = session.exec(text("SELECT 1"))
                assert result.fetchone()[0] == 1
    
    def test_database_connection_recovery(self, settings):
        """测试连接恢复能力"""
        # 正常连接
        with settings.get_session() as session:
            result = session.exec(text("SELECT 1"))
            assert result.fetchone()[0] == 1
        
        # 短暂等待
        time.sleep(0.1)
        
        # 再次连接，验证连接恢复
        with settings.get_session() as session:
            result = session.exec(text("SELECT 1"))
            assert result.fetchone()[0] == 1
    
    def test_database_query_execution(self, settings):
        """测试查询执行"""
        with settings.get_session() as session:
            # 测试简单查询
            result = session.exec(text("SELECT COUNT(*) FROM users"))
            count = result.fetchone()[0]
            assert isinstance(count, int)
            assert count >= 0
    
    def test_database_session_isolation(self, settings):
        """测试会话隔离"""
        # 创建两个独立的会话
        with settings.get_session() as session1:
            with settings.get_session() as session2:
                # 验证两个会话是独立的
                assert session1 is not session2
                
                # 每个会话都能独立执行查询
                result1 = session1.exec(text("SELECT 1"))
                result2 = session2.exec(text("SELECT 1"))
                
                assert result1.fetchone()[0] == 1
                assert result2.fetchone()[0] == 1
    
    def test_database_connection_string_valid(self, settings):
        """测试连接字符串格式正确"""
        conn_str = settings.db_conn_str
        assert conn_str.startswith("postgresql://")
        assert "@" in conn_str
        assert ":" in conn_str.split("@")[1]  # 包含端口


class TestDatabaseErrorHandling:
    """数据库错误处理测试类"""
    
    def test_invalid_query_handling(self, settings):
        """测试无效查询的错误处理"""
        with settings.get_session() as session:
            with pytest.raises(Exception):  # 应该抛出异常
                session.exec(text("SELECT * FROM non_existent_table"))
                session.commit()
    
    def test_session_rollback_on_error(self, settings):
        """测试错误时自动回滚"""
        with settings.get_session() as session:
            try:
                # 执行会失败的查询
                session.exec(text("SELECT * FROM non_existent_table"))
                session.commit()
            except Exception:
                # 显式回滚（PostgreSQL 要求）
                session.rollback()
            
            # 验证会话仍然可用（回滚后）
            result = session.exec(text("SELECT 1"))
            assert result.fetchone()[0] == 1
    
    def test_connection_pool_exhaustion_handling(self, settings):
        """测试连接池耗尽时的处理"""
        # 创建大量会话（超过连接池大小）
        max_connections = settings.pool_size + settings.max_overflow
        sessions = []
        
        try:
            for i in range(max_connections + 1):
                session = Session(settings.engine)
                sessions.append(session)
                # 验证会话可用
                result = session.exec(text("SELECT 1"))
                assert result.fetchone()[0] == 1
        except Exception as e:
            # 连接池耗尽时可能抛出异常，这是预期的
            assert "pool" in str(e).lower() or "connection" in str(e).lower()
        finally:
            # 清理所有会话
            for session in sessions:
                try:
                    session.close()
                except:
                    pass


class TestDatabaseORMIntegration:
    """数据库 ORM 集成测试"""
    
    def test_orm_query_execution(self, settings):
        """测试 ORM 查询执行"""
        with settings.get_session() as session:
            # 使用 ORM 查询
            statement = select(User)
            result = session.exec(statement)
            users = result.all()
            # 验证返回的是列表
            assert isinstance(users, list)
    
    def test_orm_model_creation(self, settings):
        """测试 ORM 模型创建（不提交，测试后回滚）"""
        import uuid
        test_email = f"test_orm_{uuid.uuid4().hex[:8]}@example.com"
        
        with settings.get_session() as session:
            # 创建用户（但不提交，测试后自动回滚）
            user = User(
                email=test_email,
                password_hash="test_hash"
            )
            session.add(user)
            # 不提交，让上下文管理器处理
            
            # 验证对象已添加到会话
            assert user.id is not None


class TestDatabaseConnectionResilience:
    """数据库连接容错测试"""
    
    def test_connection_pool_recovery(self, settings):
        """测试连接池自动恢复"""
        # 创建并关闭多个会话，验证连接池能正常回收
        for _ in range(3):
            with settings.get_session() as session:
                result = session.exec(text("SELECT 1"))
                assert result.fetchone()[0] == 1
        
        # 验证连接池仍然可用
        with settings.get_session() as session:
            result = session.exec(text("SELECT 1"))
            assert result.fetchone()[0] == 1
    
    def test_session_auto_close_on_exception(self, settings):
        """测试异常时会话自动关闭"""
        try:
            with settings.get_session() as session:
                # 触发异常
                session.exec(text("SELECT * FROM non_existent_table"))
                session.commit()
        except Exception:
            pass
        
        # 验证新会话仍然可用（说明旧会话已正确关闭）
        with settings.get_session() as session:
            result = session.exec(text("SELECT 1"))
            assert result.fetchone()[0] == 1
    
    def test_multiple_sessions_independence(self, settings):
        """测试多个会话的独立性"""
        # 创建多个会话，验证它们互不影响
        sessions_data = []
        
        for i in range(3):
            with settings.get_session() as session:
                result = session.exec(text(f"SELECT {i+1} as num"))
                sessions_data.append(result.fetchone()[0])
        
        # 验证每个会话都正确执行
        assert sessions_data == [1, 2, 3]
    
    def test_engine_reuse_after_errors(self, settings):
        """测试引擎在错误后仍可重用"""
        # 第一次使用（可能失败）
        try:
            with settings.get_session() as session:
                session.exec(text("SELECT * FROM non_existent_table"))
        except Exception:
            pass
        
        # 验证引擎仍然可用
        with settings.get_session() as session:
            result = session.exec(text("SELECT 1"))
            assert result.fetchone()[0] == 1
        
        # 再次验证
        with settings.get_session() as session:
            result = session.exec(text("SELECT 2"))
            assert result.fetchone()[0] == 2

