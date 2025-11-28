# 测试说明

## 运行测试

```bash
# 运行所有测试
uv run pytest

# 运行特定测试文件
uv run pytest tests/test_database_connection.py

# 运行特定测试类
uv run pytest tests/test_database_connection.py::TestDatabaseConnection

# 运行特定测试方法
uv run pytest tests/test_database_connection.py::TestDatabaseConnection::test_database_connection_success

# 显示详细输出
uv run pytest -v

# 显示覆盖率（需要安装 pytest-cov）
uv run pytest --cov=. --cov-report=html
```

## 测试覆盖

### 数据库连接测试 (`test_database_connection.py`)

#### TestDatabaseConnection (8个测试)
- ✅ 数据库连接成功
- ✅ 会话上下文管理器
- ✅ 连接池功能
- ✅ 事务回滚
- ✅ 连接恢复
- ✅ 查询执行
- ✅ 会话隔离
- ✅ 连接字符串验证

#### TestDatabaseErrorHandling (3个测试)
- ✅ 无效查询处理
- ✅ 错误时自动回滚
- ✅ 连接池耗尽处理

#### TestDatabaseORMIntegration (2个测试)
- ✅ ORM 查询执行
- ✅ ORM 模型创建

#### TestDatabaseConnectionResilience (4个测试)
- ✅ 连接池自动恢复
- ✅ 异常时会话自动关闭
- ✅ 多个会话独立性
- ✅ 引擎错误后重用

**总计：17 个测试用例，全部通过**

## 测试配置

测试使用 `pytest.ini` 配置文件，支持：
- 自动发现测试文件
- 标记系统（slow, integration, unit）
- 详细的错误输出

