from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
try:
    from .database import Base
except ImportError:
    from database import Base

class Server(Base):
    """
    服务器模型
    用于存储服务器信息和SSH连接凭证（密钥或密码）
    """
    __tablename__ = "servers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), index=True, nullable=False, unique=True)
    hostname = Column(String(255), nullable=False)  # 主机名或IP地址
    port = Column(Integer, default=22)
    username = Column(String(100), nullable=False)
    encrypted_private_key = Column(Text, nullable=True)  # 加密后的私钥（可选）
    encrypted_password = Column(Text, nullable=True)  # 加密后的密码（可选）
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
    server_id = Column(Integer, ForeignKey('servers.id'), nullable=False)  # 关联的服务器ID
    config_path = Column(String(500), default="/etc/XrayR/config.yml")  # 配置文件路径
    raw_config = Column(Text, nullable=True)  # 原始配置文件内容
    parsed_config = Column(JSON, nullable=True)  # 解析后的配置JSON
    description = Column(Text, nullable=True)
    last_sync_at = Column(DateTime(timezone=True), nullable=True)  # 最后同步时间
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

# 兼容旧代码的模型定义（将在后续完全迁移后移除）
class SSHKey(Base):
    __tablename__ = "ssh_keys"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), index=True, nullable=False, unique=True)
    hostname = Column(String(255), nullable=False)
    port = Column(Integer, default=22)
    username = Column(String(100), nullable=False)
    encrypted_private_key = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class SSHPassword(Base):
    __tablename__ = "ssh_passwords"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), index=True, nullable=False, unique=True)
    hostname = Column(String(255), nullable=False)
    port = Column(Integer, default=22)
    username = Column(String(100), nullable=False)
    encrypted_password = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())