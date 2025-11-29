# logger.py
import sys
from loguru import logger
from pathlib import Path

# 移除默认handler
logger.remove()

# 1. 控制台输出（彩色，方便开发）
logger.add(
    sys.stderr,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}:{function}:{line}</cyan> - <level>{message}</level>",
    level="DEBUG",
    colorize=True,
)

# 2. 文件输出（自动轮转）
log_dir = Path("./logs")
log_dir.mkdir(exist_ok=True)

logger.add(
    "./logs/app.log",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}",
    level="INFO",
    rotation="500 MB",      # 文件大小超过500MB就新建
    retention="10 days",    # 只保留10天
    compression="zip",      # 旧日志压缩
    encoding="utf-8",
)

# 3. 错误日志单独记录
logger.add(
    "./logs/error.log",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}",
    level="ERROR",
    rotation="100 MB",
    retention="30 days",
    backtrace=True,         # 完整堆栈
    diagnose=True,          # 详细诊断
    encoding="utf-8",
)
