from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

from src.database import get_db
from src.models import SSHKey
from src.crypto import encrypt_data, decrypt_data
from src.api.auth import verify_credentials

router = APIRouter(dependencies=[Depends(verify_credentials)])

# 请求模型
class SSHKeyCreate(BaseModel):
    name: str = Field(..., max_length=100, description="密钥名称")
    hostname: str = Field(..., max_length=255, description="主机名或IP地址")
    port: int = Field(default=22, ge=1, le=65535, description="SSH端口")
    username: str = Field(..., max_length=100, description="SSH用户名")
    private_key: str = Field(..., description="SSH私钥内容")
    description: Optional[str] = Field(None, description="密钥描述")

class SSHKeyUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100, description="密钥名称")
    hostname: Optional[str] = Field(None, max_length=255, description="主机名或IP地址")
    port: Optional[int] = Field(None, ge=1, le=65535, description="SSH端口")
    username: Optional[str] = Field(None, max_length=100, description="SSH用户名")
    private_key: Optional[str] = Field(None, description="SSH私钥内容")
    description: Optional[str] = Field(None, description="密钥描述")

# 响应模型
class SSHKeyResponse(BaseModel):
    id: int
    name: str
    hostname: str
    port: int
    username: str
    description: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        orm_mode = True

@router.post("/", response_model=SSHKeyResponse, status_code=status.HTTP_201_CREATED)
def create_ssh_key(ssh_key: SSHKeyCreate, db: Session = Depends(get_db)):
    """
    创建新的SSH密钥
    注意：私钥会在存储前进行加密
    """
    # 检查密钥名称是否已存在
    db_ssh_key = db.query(SSHKey).filter(SSHKey.name == ssh_key.name).first()
    if db_ssh_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="SSH密钥名称已存在"
        )
    
    # 加密私钥
    encrypted_private_key = encrypt_data(ssh_key.private_key)
    
    # 创建新的SSH密钥记录
    db_ssh_key = SSHKey(
        name=ssh_key.name,
        hostname=ssh_key.hostname,
        port=ssh_key.port,
        username=ssh_key.username,
        encrypted_private_key=encrypted_private_key,
        description=ssh_key.description
    )
    
    # 添加到数据库并提交
    db.add(db_ssh_key)
    db.commit()
    db.refresh(db_ssh_key)
    
    return db_ssh_key

@router.get("/", response_model=List[SSHKeyResponse])
def get_ssh_keys(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    获取SSH密钥列表
    """
    ssh_keys = db.query(SSHKey).offset(skip).limit(limit).all()
    return ssh_keys

@router.get("/{ssh_key_id}", response_model=SSHKeyResponse)
def get_ssh_key(ssh_key_id: int, db: Session = Depends(get_db)):
    """
    获取单个SSH密钥详情
    """
    db_ssh_key = db.query(SSHKey).filter(SSHKey.id == ssh_key_id).first()
    if db_ssh_key is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SSH密钥不存在"
        )
    return db_ssh_key

@router.put("/{ssh_key_id}", response_model=SSHKeyResponse)
def update_ssh_key(
    ssh_key_id: int,
    ssh_key: SSHKeyUpdate,
    db: Session = Depends(get_db)
):
    """
    更新SSH密钥信息
    """
    db_ssh_key = db.query(SSHKey).filter(SSHKey.id == ssh_key_id).first()
    if db_ssh_key is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SSH密钥不存在"
        )
    
    # 检查新的密钥名称是否已存在（如果提供了新名称）
    if ssh_key.name and ssh_key.name != db_ssh_key.name:
        existing_key = db.query(SSHKey).filter(SSHKey.name == ssh_key.name).first()
        if existing_key:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="SSH密钥名称已存在"
            )
        db_ssh_key.name = ssh_key.name
    
    # 更新其他字段
    if ssh_key.hostname is not None:
        db_ssh_key.hostname = ssh_key.hostname
    if ssh_key.port is not None:
        db_ssh_key.port = ssh_key.port
    if ssh_key.username is not None:
        db_ssh_key.username = ssh_key.username
    if ssh_key.private_key is not None:
        db_ssh_key.encrypted_private_key = encrypt_data(ssh_key.private_key)
    if ssh_key.description is not None:
        db_ssh_key.description = ssh_key.description
    
    # 提交更新
    db.commit()
    db.refresh(db_ssh_key)
    
    return db_ssh_key

@router.delete("/{ssh_key_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ssh_key(ssh_key_id: int, db: Session = Depends(get_db)):
    """
    删除SSH密钥
    """
    db_ssh_key = db.query(SSHKey).filter(SSHKey.id == ssh_key_id).first()
    if db_ssh_key is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SSH密钥不存在"
        )
    
    db.delete(db_ssh_key)
    db.commit()
    
    return None