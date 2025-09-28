from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
try:
    from .database import Base
except ImportError:
    from database import Base

class SSHKey(Base):
    """
    SSH密钥模型
    用于存储加密后的SSH密钥信息
    """
    __tablename__ = "ssh_keys"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), index=True, nullable=False, unique=True)
    hostname = Column(String(255), nullable=False)
    port = Column(Integer, default=22)
    username = Column(String(100), nullable=False)
    encrypted_private_key = Column(Text, nullable=False)  # 加密后的私钥
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class XrayRConfig(Base):
    """
    XrayR配置模型
    用于存储和管理XrayR配置文件
    """
    __tablename__ = "xrayr_configs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), index=True, nullable=False, unique=True)
    ssh_connection_id = Column(Integer, nullable=False)  # 关联的SSH连接ID（可以是ssh_keys或ssh_passwords的ID）
    ssh_connection_type = Column(String(20), nullable=False)  # 'key' 或 'password'
    config_path = Column(String(500), default="/etc/XrayR/config.yml")  # 配置文件路径
    raw_config = Column(Text, nullable=True)  # 原始配置文件内容
    parsed_config = Column(JSON, nullable=True)  # 解析后的配置JSON
    description = Column(Text, nullable=True)
    last_sync_at = Column(DateTime(timezone=True), nullable=True)  # 最后同步时间
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class SSHPassword(Base):
    """
    SSH密码模型
    用于存储加密后的SSH密码登录信息
    """
    __tablename__ = "ssh_passwords"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), index=True, nullable=False, unique=True)
    hostname = Column(String(255), nullable=False)
    port = Column(Integer, default=22)
    username = Column(String(100), nullable=False)
    encrypted_password = Column(Text, nullable=False)  # 加密后的密码
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())