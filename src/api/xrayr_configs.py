from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..database import get_db
from ..models import XrayRConfig, Server
from ..crypto import decrypt_data
from ..xrayr_utils import XrayRConfigParser, create_default_xrayr_config
from .auth import get_current_user

router = APIRouter()

# 请求模型
class XrayRConfigCreate(BaseModel):
    name: str = Field(..., max_length=100, description="配置名称")
    config_path: str = Field(default="/etc/XrayR/config.yml", max_length=500, description="配置文件路径")
    description: Optional[str] = Field(None, description="配置描述")

class XrayRConfigUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100, description="配置名称")
    config_path: Optional[str] = Field(None, max_length=500, description="配置文件路径")
    parsed_config: Optional[Dict[str, Any]] = Field(None, description="解析后的配置")
    description: Optional[str] = Field(None, description="配置描述")

class XrayRConfigResponse(BaseModel):
    id: int
    name: str
    server_id: int
    server_hostname: str
    server_username: str
    config_path: str
    parsed_config: Optional[Dict[str, Any]]
    description: Optional[str]
    last_sync_at: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True
        
        @classmethod
        def from_orm(cls, obj):
            # 自定义from_orm方法以包含服务器信息
            data = {
                'id': obj.id,
                'name': obj.name,
                'server_id': obj.server_id,
                'server_hostname': obj.server.hostname if obj.server else None,
                'server_username': obj.server.username if obj.server else None,
                'config_path': obj.config_path,
                'parsed_config': obj.parsed_config,
                'description': obj.description,
                'last_sync_at': obj.last_sync_at,
                'created_at': obj.created_at,
                'updated_at': obj.updated_at
            }
            return cls(**data)

# API端点 - 基于服务器ID的配置管理
@router.post("/servers/{server_id}/configs", response_model=XrayRConfigResponse, status_code=status.HTTP_201_CREATED)
def create_server_config(
    server_id: int,
    config: XrayRConfigCreate,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    为指定服务器创建新的XrayR配置
    """
    # 验证服务器是否存在
    server = db.query(Server).filter(Server.id == server_id).first()
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="服务器不存在"
        )
    
    # 检查配置名称是否已存在
    existing_config = db.query(XrayRConfig).filter(
        XrayRConfig.name == config.name, 
        XrayRConfig.server_id == server_id
    ).first()
    if existing_config:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该服务器下已存在同名配置"
        )
    
    # 检查服务器是否有有效的连接凭证
    if not server.encrypted_private_key and not server.encrypted_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="服务器既没有配置SSH密钥也没有配置SSH密码"
        )
    
    # 创建默认配置
    default_config = create_default_xrayr_config()
    
    # 创建数据库记录
    db_config = XrayRConfig(
        name=config.name,
        server_id=server_id,
        config_path=config.config_path,
        parsed_config=default_config,
        description=config.description
    )
    
    db.add(db_config)
    db.commit()
    db.refresh(db_config)
    
    return db_config

@router.get("/servers/{server_id}/configs", response_model=List[XrayRConfigResponse])
def get_server_configs(
    server_id: int,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    获取指定服务器的所有XrayR配置
    """
    # 验证服务器是否存在
    server = db.query(Server).filter(Server.id == server_id).first()
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="服务器不存在"
        )
    
    configs = db.query(XrayRConfig).filter(XrayRConfig.server_id == server_id).all()
    return configs

@router.get("/servers/{server_id}/configs/{config_id}", response_model=XrayRConfigResponse)
def get_server_config(
    server_id: int,
    config_id: int,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    获取指定服务器的特定XrayR配置
    """
    # 验证服务器是否存在
    server = db.query(Server).filter(Server.id == server_id).first()
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="服务器不存在"
        )
    
    # 验证配置是否存在且属于该服务器
    config = db.query(XrayRConfig).filter(
        XrayRConfig.id == config_id,
        XrayRConfig.server_id == server_id
    ).first()
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="配置不存在或不属于该服务器"
        )
    
    return config

@router.put("/servers/{server_id}/configs/{config_id}", response_model=XrayRConfigResponse)
def update_server_config(
    server_id: int,
    config_id: int,
    config: XrayRConfigUpdate,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    更新指定服务器的特定XrayR配置
    """
    # 验证服务器是否存在
    server = db.query(Server).filter(Server.id == server_id).first()
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="服务器不存在"
        )
    
    # 验证配置是否存在且属于该服务器
    db_config = db.query(XrayRConfig).filter(
        XrayRConfig.id == config_id,
        XrayRConfig.server_id == server_id
    ).first()
    if not db_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="配置不存在或不属于该服务器"
        )
    
    # 检查名称是否重复（如果有修改名称）
    if config.name and config.name != db_config.name:
        existing_config = db.query(XrayRConfig).filter(
            XrayRConfig.name == config.name, 
            XrayRConfig.server_id == server_id,
            XrayRConfig.id != config_id
        ).first()
        if existing_config:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该服务器下已存在同名配置"
            )
    
    # 验证配置有效性
    if config.parsed_config:
        is_valid, error_msg = XrayRConfigParser.validate_config(config.parsed_config)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"配置验证失败: {error_msg}"
            )
    
    # 更新字段
    update_data = config.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_config, field, value)
    
    db.commit()
    db.refresh(db_config)
    
    return db_config

@router.delete("/servers/{server_id}/configs/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_server_config(
    server_id: int,
    config_id: int,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    删除指定服务器的特定XrayR配置
    """
    # 验证服务器是否存在
    server = db.query(Server).filter(Server.id == server_id).first()
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="服务器不存在"
        )
    
    # 验证配置是否存在且属于该服务器
    config = db.query(XrayRConfig).filter(
        XrayRConfig.id == config_id,
        XrayRConfig.server_id == server_id
    ).first()
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="配置不存在或不属于该服务器"
        )
    
    db.delete(config)
    db.commit()
    
    return None

@router.get("/configs/{config_id}", response_model=XrayRConfigResponse)
def get_config_by_id(
    config_id: int,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    根据配置ID获取XrayR配置（兼容旧接口）
    """
    config = db.query(XrayRConfig).filter(XrayRConfig.id == config_id).first()
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="配置不存在"
        )
    return config