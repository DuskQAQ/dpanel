from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator
import paramiko
import io

from ..database import get_db
from ..models import Server
from ..crypto import encrypt_data, decrypt_data
from .auth import get_current_user

router = APIRouter(
    prefix="/servers",
    tags=["服务器管理"],
    responses={404: {"description": "未找到"}},
)

# 请求和响应模型
class ServerBase(BaseModel):
    name: str = Field(..., max_length=100, description="服务器名称")
    hostname: str = Field(..., max_length=255, description="主机名或IP地址")
    port: int = Field(default=22, ge=1, le=65535, description="SSH端口")
    username: str = Field(..., max_length=100, description="SSH用户名")
    description: Optional[str] = Field(default=None, description="描述信息")

class ServerCreate(ServerBase):
    private_key: str = Field(default=None, description="SSH私钥（与密码二选一）")
    password: str = Field(default=None, description="SSH密码（与私钥二选一）")
    
    @field_validator('private_key', 'password')
    def check_credentials(cls, v, info):
        # 获取所有字段值
        values = info.data
        # 确保至少提供了私钥或密码中的一个
        if ('private_key' in values and 'password' in values):
            if not values['private_key'] and not values['password']:
                raise ValueError("至少需要提供私钥或密码中的一个")
        return v

class ServerUpdate(ServerCreate):
    name: str = Field(default=None, max_length=100, description="服务器名称")
    hostname: str = Field(default=None, max_length=255, description="主机名或IP地址")
    username: str = Field(default=None, max_length=100, description="SSH用户名")

class ServerResponse(ServerBase):
    id: int
    has_private_key: bool = Field(..., description="是否有私钥")
    has_password: bool = Field(..., description="是否有密码")
    created_at: str
    updated_at: Optional[str] = Field(default=None)
    
    class Config:
        from_attributes = True

# 辅助函数
@router.post("/", response_model=ServerResponse, status_code=status.HTTP_201_CREATED)
def create_server(server: ServerCreate, db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    """
    创建新服务器
    支持同时存储私钥和密码，连接时优先使用私钥
    """
    # 检查服务器名称是否已存在
    db_server = db.query(Server).filter(Server.name == server.name).first()
    if db_server:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="服务器名称已存在"
        )
    
    # 加密凭证
    encrypted_private_key = None
    encrypted_password = None
    
    if server.private_key:
        encrypted_private_key = encrypt_data(server.private_key)
    if server.password:
        encrypted_password = encrypt_data(server.password)
    
    # 创建服务器记录
    db_server = Server(
        name=server.name,
        hostname=server.hostname,
        port=server.port,
        username=server.username,
        encrypted_private_key=encrypted_private_key,
        encrypted_password=encrypted_password,
        description=server.description
    )
    
    db.add(db_server)
    db.commit()
    db.refresh(db_server)
    
    # 构建响应，不返回敏感信息
    response_data = ServerResponse(
        id=db_server.id,
        name=db_server.name,
        hostname=db_server.hostname,
        port=db_server.port,
        username=db_server.username,
        description=db_server.description,
        has_private_key=db_server.encrypted_private_key is not None,
        has_password=db_server.encrypted_password is not None,
        created_at=db_server.created_at.isoformat(),
        updated_at=db_server.updated_at.isoformat() if db_server.updated_at else None
    )
    
    return response_data

@router.get("/", response_model=List[ServerResponse])
def read_servers(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    """
    获取所有服务器列表
    """
    servers = db.query(Server).offset(skip).limit(limit).all()
    
    # 构建响应列表，不返回敏感信息
    response_data = []
    for server in servers:
        response_data.append(
            ServerResponse(
                id=server.id,
                name=server.name,
                hostname=server.hostname,
                port=server.port,
                username=server.username,
                description=server.description,
                has_private_key=server.encrypted_private_key is not None,
                has_password=server.encrypted_password is not None,
                created_at=server.created_at.isoformat(),
                updated_at=server.updated_at.isoformat() if server.updated_at else None
            )
        )
    
    return response_data

@router.get("/{server_id}", response_model=ServerResponse)
def read_server(server_id: int, db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    """
    获取单个服务器信息
    """
    db_server = db.query(Server).filter(Server.id == server_id).first()
    if db_server is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="服务器不存在"
        )
    
    # 构建响应，不返回敏感信息
    response_data = ServerResponse(
        id=db_server.id,
        name=db_server.name,
        hostname=db_server.hostname,
        port=db_server.port,
        username=db_server.username,
        description=db_server.description,
        has_private_key=db_server.encrypted_private_key is not None,
        has_password=db_server.encrypted_password is not None,
        created_at=db_server.created_at.isoformat(),
        updated_at=db_server.updated_at.isoformat() if db_server.updated_at else None
    )
    
    return response_data

@router.put("/{server_id}", response_model=ServerResponse)
def update_server(
    server_id: int,
    server: ServerUpdate,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    更新服务器信息
    """
    db_server = db.query(Server).filter(Server.id == server_id).first()
    if db_server is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="服务器不存在"
        )
    
    # 检查新名称是否已存在（如果提供了新名称）
    if server.name and server.name != db_server.name:
        existing_server = db.query(Server).filter(Server.name == server.name).first()
        if existing_server:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="服务器名称已存在"
            )
    
    # 更新基本信息
    if server.name:
        db_server.name = server.name
    if server.hostname:
        db_server.hostname = server.hostname
    if server.port:
        db_server.port = server.port
    if server.username:
        db_server.username = server.username
    if server.description is not None:
        db_server.description = server.description
    
    # 更新凭证（如果提供了新凭证）
    if server.private_key is not None:
        if server.private_key:
            db_server.encrypted_private_key = encrypt_data(server.private_key)
        else:
            db_server.encrypted_private_key = None
    
    if server.password is not None:
        if server.password:
            db_server.encrypted_password = encrypt_data(server.password)
        else:
            db_server.encrypted_password = None
    
    db.commit()
    db.refresh(db_server)
    
    # 构建响应，不返回敏感信息
    response_data = ServerResponse(
        id=db_server.id,
        name=db_server.name,
        hostname=db_server.hostname,
        port=db_server.port,
        username=db_server.username,
        description=db_server.description,
        has_private_key=db_server.encrypted_private_key is not None,
        has_password=db_server.encrypted_password is not None,
        created_at=db_server.created_at.isoformat(),
        updated_at=db_server.updated_at.isoformat() if db_server.updated_at else None
    )
    
    return response_data

@router.delete("/{server_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_server(server_id: int, db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    """
    删除服务器
    """
    db_server = db.query(Server).filter(Server.id == server_id).first()
    if db_server is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="服务器不存在"
        )
    
    db.delete(db_server)
    db.commit()
    
    return None

@router.post("/{server_id}/test-connection")
def test_server_connection(server_id: int, db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    """
    测试服务器SSH连接
    优先使用私钥连接，如果失败则尝试使用密码连接
    """
    server = db.query(Server).filter(Server.id == server_id).first()
    if server is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="服务器不存在"
        )
    
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        # 尝试使用私钥连接
        if server.encrypted_private_key:
            try:
                private_key_content = decrypt_data(server.encrypted_private_key)
                private_key = paramiko.RSAKey.from_private_key(io.StringIO(private_key_content))
                
                ssh_client.connect(
                    hostname=server.hostname,
                    port=server.port,
                    username=server.username,
                    pkey=private_key,
                    timeout=10
                )
                
                return {
                    "status": "success",
                    "message": "SSH连接成功（使用私钥）",
                    "connection_type": "key"
                }
            except Exception as e:
                # 私钥连接失败，如果有密码则尝试密码连接
                if not server.encrypted_password:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=f"SSH私钥连接失败: {str(e)}"
                    )
        
        # 尝试使用密码连接
        if server.encrypted_password:
            password = decrypt_data(server.encrypted_password)
            
            ssh_client.connect(
                hostname=server.hostname,
                port=server.port,
                username=server.username,
                password=password,
                timeout=10
            )
            
            return {
                "status": "success",
                "message": "SSH连接成功（使用密码）",
                "connection_type": "password"
            }
        
        # 没有可用的连接凭证
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="服务器没有配置SSH连接凭证（私钥或密码）"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"SSH连接失败: {str(e)}"
        )
    finally:
        ssh_client.close()