from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

from ..database import get_db
from ..models import SSHPassword
from ..crypto import encrypt_data, decrypt_data
from .auth import get_current_user

router = APIRouter()

# 请求模型
class SSHPasswordCreate(BaseModel):
    name: str = Field(..., max_length=100, description="连接名称")
    hostname: str = Field(..., max_length=255, description="主机名或IP地址")
    port: int = Field(default=22, ge=1, le=65535, description="SSH端口")
    username: str = Field(..., max_length=100, description="SSH用户名")
    password: str = Field(..., description="SSH密码")
    description: Optional[str] = Field(None, description="连接描述")

class SSHPasswordUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100, description="连接名称")
    hostname: Optional[str] = Field(None, max_length=255, description="主机名或IP地址")
    port: Optional[int] = Field(None, ge=1, le=65535, description="SSH端口")
    username: Optional[str] = Field(None, max_length=100, description="SSH用户名")
    password: Optional[str] = Field(None, description="SSH密码")
    description: Optional[str] = Field(None, description="连接描述")

# 响应模型
class SSHPasswordResponse(BaseModel):
    id: int
    name: str
    hostname: str
    port: int
    username: str
    description: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True

@router.post("/", response_model=SSHPasswordResponse, status_code=status.HTTP_201_CREATED)
def create_ssh_password(ssh_password: SSHPasswordCreate, db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    """
    创建新的SSH密码连接
    注意：密码会在存储前进行加密
    """
    # 检查连接名称是否已存在
    db_ssh_password = db.query(SSHPassword).filter(SSHPassword.name == ssh_password.name).first()
    if db_ssh_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="SSH连接名称已存在"
        )
    
    # 加密密码
    encrypted_password = encrypt_data(ssh_password.password)
    
    # 创建新的SSH密码记录
    db_ssh_password = SSHPassword(
        name=ssh_password.name,
        hostname=ssh_password.hostname,
        port=ssh_password.port,
        username=ssh_password.username,
        encrypted_password=encrypted_password,
        description=ssh_password.description
    )
    
    # 添加到数据库并提交
    db.add(db_ssh_password)
    db.commit()
    db.refresh(db_ssh_password)
    
    return db_ssh_password

@router.get("/", response_model=List[SSHPasswordResponse])
def get_ssh_passwords(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    """
    获取SSH密码连接列表
    """
    ssh_passwords = db.query(SSHPassword).offset(skip).limit(limit).all()
    return ssh_passwords

@router.get("/{ssh_password_id}", response_model=SSHPasswordResponse)
def get_ssh_password(ssh_password_id: int, db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    """
    获取单个SSH密码连接详情
    """
    db_ssh_password = db.query(SSHPassword).filter(SSHPassword.id == ssh_password_id).first()
    if db_ssh_password is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SSH密码连接不存在"
        )
    return db_ssh_password

@router.put("/{ssh_password_id}", response_model=SSHPasswordResponse)
def update_ssh_password(
    ssh_password_id: int,
    ssh_password: SSHPasswordUpdate,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    更新SSH密码连接信息
    """
    db_ssh_password = db.query(SSHPassword).filter(SSHPassword.id == ssh_password_id).first()
    if db_ssh_password is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SSH密码连接不存在"
        )
    
    # 检查新的连接名称是否已存在（如果提供了新名称）
    if ssh_password.name and ssh_password.name != db_ssh_password.name:
        existing_password = db.query(SSHPassword).filter(SSHPassword.name == ssh_password.name).first()
        if existing_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="SSH连接名称已存在"
            )
        db_ssh_password.name = ssh_password.name
    
    # 更新其他字段
    if ssh_password.hostname is not None:
        db_ssh_password.hostname = ssh_password.hostname
    if ssh_password.port is not None:
        db_ssh_password.port = ssh_password.port
    if ssh_password.username is not None:
        db_ssh_password.username = ssh_password.username
    if ssh_password.password is not None:
        db_ssh_password.encrypted_password = encrypt_data(ssh_password.password)
    if ssh_password.description is not None:
        db_ssh_password.description = ssh_password.description
    
    # 提交更新
    db.commit()
    db.refresh(db_ssh_password)
    
    return db_ssh_password

@router.delete("/{ssh_password_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ssh_password(ssh_password_id: int, db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    """
    删除SSH密码连接
    """
    db_ssh_password = db.query(SSHPassword).filter(SSHPassword.id == ssh_password_id).first()
    if db_ssh_password is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SSH密码连接不存在"
        )
    
    db.delete(db_ssh_password)
    db.commit()
    
    return None