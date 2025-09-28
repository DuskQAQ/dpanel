from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

# 加载环境变量
load_dotenv()

# 获取数据库配置
DATABASE_TYPE = os.getenv("DATABASE_TYPE", "sqlite").lower()
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./ssh_keys.db")

# 根据数据库类型设置连接参数
def get_engine_config():
    """根据数据库类型获取引擎配置"""
    if DATABASE_TYPE == "sqlite":
        return {
            "connect_args": {"check_same_thread": False},
            "echo": False
        }
    elif DATABASE_TYPE == "mysql":
        return {
            "pool_pre_ping": True,
            "pool_recycle": 300,
            "echo": False
        }
    else:
        return {"echo": False}

# 创建数据库引擎
engine = create_engine(DATABASE_URL, **get_engine_config())

# 创建会话本地类
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基础类
Base = declarative_base()

# 依赖项：获取数据库会话
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()