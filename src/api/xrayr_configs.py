from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import paramiko
import io

from ..database import get_db
from ..models import XrayRConfig, SSHKey, SSHPassword
from ..crypto import decrypt_data
from ..xrayr_utils import XrayRConfigParser, create_default_xrayr_config
from .auth import get_current_user

router = APIRouter()

# 请求模型
class XrayRConfigCreate(BaseModel):
    name: str = Field(..., max_length=100, description="配置名称")
    ssh_connection_id: int = Field(..., description="SSH连接ID")
    ssh_connection_type: str = Field(..., pattern="^(key|password)$", description="SSH连接类型: key 或 password")
    config_path: str = Field(default="/etc/XrayR/config.yml", max_length=500, description="配置文件路径")
    description: Optional[str] = Field(None, description="配置描述")

class XrayRConfigUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100, description="配置名称")
    ssh_connection_id: Optional[int] = Field(None, description="SSH连接ID")
    ssh_connection_type: Optional[str] = Field(None, pattern="^(key|password)$", description="SSH连接类型")
    config_path: Optional[str] = Field(None, max_length=500, description="配置文件路径")
    parsed_config: Optional[Dict[str, Any]] = Field(None, description="解析后的配置")
    description: Optional[str] = Field(None, description="配置描述")

class XrayRConfigResponse(BaseModel):
    id: int
    name: str
    ssh_connection_id: int
    ssh_connection_type: str
    config_path: str
    parsed_config: Optional[Dict[str, Any]]
    description: Optional[str]
    last_sync_at: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class SyncConfigRequest(BaseModel):
    force_update: bool = Field(default=False, description="是否强制更新")

class DeployConfigRequest(BaseModel):
    backup_original: bool = Field(default=True, description="是否备份原配置文件")

# 辅助函数
def get_ssh_client(ssh_connection_id: int, ssh_connection_type: str, db: Session) -> paramiko.SSHClient:
    """
    根据SSH连接信息创建SSH客户端
    """
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        if ssh_connection_type == "key":
            # 使用SSH密钥连接
            ssh_key = db.query(SSHKey).filter(SSHKey.id == ssh_connection_id).first()
            if not ssh_key:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="SSH密钥不存在"
                )
            
            # 解密私钥
            private_key_content = decrypt_data(ssh_key.encrypted_private_key)
            private_key = paramiko.RSAKey.from_private_key(io.StringIO(private_key_content))
            
            ssh_client.connect(
                hostname=ssh_key.hostname,
                port=ssh_key.port,
                username=ssh_key.username,
                pkey=private_key,
                timeout=30
            )
            
        elif ssh_connection_type == "password":
            # 使用SSH密码连接
            ssh_password = db.query(SSHPassword).filter(SSHPassword.id == ssh_connection_id).first()
            if not ssh_password:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="SSH密码连接不存在"
                )
            
            # 解密密码
            password = decrypt_data(ssh_password.encrypted_password)
            
            ssh_client.connect(
                hostname=ssh_password.hostname,
                port=ssh_password.port,
                username=ssh_password.username,
                password=password,
                timeout=30
            )
        
        return ssh_client
        
    except Exception as e:
        ssh_client.close()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"SSH连接失败: {str(e)}"
        )

def fetch_config_from_server(config_id: int, db: Session) -> str:
    """
    从服务器获取配置文件内容
    """
    config = db.query(XrayRConfig).filter(XrayRConfig.id == config_id).first()
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="配置不存在"
        )
    
    ssh_client = None
    try:
        ssh_client = get_ssh_client(config.ssh_connection_id, config.ssh_connection_type, db)
        
        # 执行cat命令获取配置文件
        stdin, stdout, stderr = ssh_client.exec_command(f"cat {config.config_path}")
        
        # 读取输出
        config_content = stdout.read().decode('utf-8')
        error_output = stderr.read().decode('utf-8')
        
        if error_output:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"读取配置文件失败: {error_output}"
            )
        
        return config_content
        
    finally:
        if ssh_client:
            ssh_client.close()

# API端点
@router.post("/", response_model=XrayRConfigResponse, status_code=status.HTTP_201_CREATED)
def create_xrayr_config(
    config: XrayRConfigCreate, 
    db: Session = Depends(get_db), 
    current_user: str = Depends(get_current_user)
):
    """
    创建新的XrayR配置
    """
    # 检查配置名称是否已存在
    db_config = db.query(XrayRConfig).filter(XrayRConfig.name == config.name).first()
    if db_config:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="配置名称已存在"
        )
    
    # 验证SSH连接是否存在
    if config.ssh_connection_type == "key":
        ssh_connection = db.query(SSHKey).filter(SSHKey.id == config.ssh_connection_id).first()
    else:
        ssh_connection = db.query(SSHPassword).filter(SSHPassword.id == config.ssh_connection_id).first()
    
    if not ssh_connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SSH连接不存在"
        )
    
    # 创建默认配置
    default_config = create_default_xrayr_config()
    
    # 创建数据库记录
    db_config = XrayRConfig(
        name=config.name,
        ssh_connection_id=config.ssh_connection_id,
        ssh_connection_type=config.ssh_connection_type,
        config_path=config.config_path,
        parsed_config=default_config,
        description=config.description
    )
    
    db.add(db_config)
    db.commit()
    db.refresh(db_config)
    
    return db_config

@router.get("/", response_model=List[XrayRConfigResponse])
def get_xrayr_configs(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db), 
    current_user: str = Depends(get_current_user)
):
    """
    获取XrayR配置列表
    """
    configs = db.query(XrayRConfig).offset(skip).limit(limit).all()
    return configs

@router.get("/{config_id}", response_model=XrayRConfigResponse)
def get_xrayr_config(
    config_id: int, 
    db: Session = Depends(get_db), 
    current_user: str = Depends(get_current_user)
):
    """
    获取单个XrayR配置详情
    """
    config = db.query(XrayRConfig).filter(XrayRConfig.id == config_id).first()
    if config is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="配置不存在"
        )
    return config

@router.put("/{config_id}", response_model=XrayRConfigResponse)
def update_xrayr_config(
    config_id: int,
    config: XrayRConfigUpdate,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    更新XrayR配置
    """
    db_config = db.query(XrayRConfig).filter(XrayRConfig.id == config_id).first()
    if db_config is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="配置不存在"
        )
    
    # 检查名称是否重复
    if config.name and config.name != db_config.name:
        existing_config = db.query(XrayRConfig).filter(XrayRConfig.name == config.name).first()
        if existing_config:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="配置名称已存在"
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

@router.delete("/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_xrayr_config(
    config_id: int, 
    db: Session = Depends(get_db), 
    current_user: str = Depends(get_current_user)
):
    """
    删除XrayR配置
    """
    config = db.query(XrayRConfig).filter(XrayRConfig.id == config_id).first()
    if config is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="配置不存在"
        )
    
    db.delete(config)
    db.commit()
    
    return None

@router.post("/{config_id}/sync")
def sync_config_from_server(
    config_id: int,
    sync_request: SyncConfigRequest,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    从服务器同步配置文件
    """
    config = db.query(XrayRConfig).filter(XrayRConfig.id == config_id).first()
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="配置不存在"
        )
    
    try:
        # 从服务器获取配置文件内容
        raw_config = fetch_config_from_server(config_id, db)
        
        # 解析配置
        parsed_config = XrayRConfigParser.parse_yaml_config(raw_config)
        simplified_config = XrayRConfigParser.simplify_config(parsed_config)
        
        # 验证配置
        is_valid, error_msg = XrayRConfigParser.validate_config(simplified_config)
        if not is_valid:
            return {
                "success": False,
                "message": f"配置验证失败: {error_msg}",
                "raw_config": raw_config[:500] + "..." if len(raw_config) > 500 else raw_config
            }
        
        # 更新数据库
        config.raw_config = raw_config
        config.parsed_config = simplified_config
        config.last_sync_at = datetime.utcnow()
        
        db.commit()
        
        return {
            "success": True,
            "message": "配置同步成功",
            "last_sync_at": config.last_sync_at,
            "config_size": len(raw_config)
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"同步失败: {str(e)}"
        }

@router.post("/{config_id}/deploy")
def deploy_config_to_server(
    config_id: int,
    deploy_request: DeployConfigRequest,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    将配置部署到服务器
    """
    config = db.query(XrayRConfig).filter(XrayRConfig.id == config_id).first()
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="配置不存在"
        )
    
    if not config.parsed_config:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="没有可部署的配置"
        )
    
    ssh_client = None
    try:
        ssh_client = get_ssh_client(config.ssh_connection_id, config.ssh_connection_type, db)
        
        # 备份原配置文件
        if deploy_request.backup_original:
            backup_path = f"{config.config_path}.backup.{int(datetime.utcnow().timestamp())}"
            stdin, stdout, stderr = ssh_client.exec_command(f"cp {config.config_path} {backup_path}")
            stderr_output = stderr.read().decode('utf-8')
            if stderr_output:
                return {
                    "success": False,
                    "message": f"备份原配置失败: {stderr_output}"
                }
        
        # 将简化配置扩展为完整配置
        expanded_config = XrayRConfigParser.expand_simplified_config(config.parsed_config)
        
        # 转换为YAML格式
        yaml_content = XrayRConfigParser.config_to_yaml(expanded_config)
        
        # 写入配置文件
        stdin, stdout, stderr = ssh_client.exec_command(f"cat > {config.config_path}")
        stdin.write(yaml_content)
        stdin.close()
        
        stderr_output = stderr.read().decode('utf-8')
        if stderr_output:
            return {
                "success": False,
                "message": f"部署配置失败: {stderr_output}"
            }
        
        # 验证配置文件
        stdin, stdout, stderr = ssh_client.exec_command(f"test -f {config.config_path} && echo 'OK'")
        result = stdout.read().decode('utf-8').strip()
        
        if result != "OK":
            return {
                "success": False,
                "message": "配置文件部署后验证失败"
            }
        
        return {
            "success": True,
            "message": "配置部署成功",
            "backup_created": deploy_request.backup_original,
            "config_size": len(yaml_content)
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"部署失败: {str(e)}"
        }
    finally:
        if ssh_client:
            ssh_client.close()

@router.get("/{config_id}/yaml")
def get_config_as_yaml(
    config_id: int,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    获取配置的YAML格式
    """
    config = db.query(XrayRConfig).filter(XrayRConfig.id == config_id).first()
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="配置不存在"
        )
    
    if not config.parsed_config:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="没有可用的配置数据"
        )
    
    try:
        # 将简化配置扩展为完整配置
        expanded_config = XrayRConfigParser.expand_simplified_config(config.parsed_config)
        
        # 转换为YAML格式
        yaml_content = XrayRConfigParser.config_to_yaml(expanded_config)
        
        return {
            "config_name": config.name,
            "yaml_content": yaml_content,
            "last_updated": config.updated_at
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"生成YAML失败: {str(e)}"
        )