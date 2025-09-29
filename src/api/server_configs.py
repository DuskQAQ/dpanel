from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import paramiko
import io
from datetime import datetime

from ..database import get_db
from ..models import Server, XrayRConfig
from ..crypto import decrypt_data
from ..xrayr_utils import XrayRConfigParser
from .auth import get_current_user

router = APIRouter()

# 请求模型
class GetServerConfigRequest(BaseModel):
    config_path: str = Field(default="/etc/XrayR/config.yml", max_length=500, description="配置文件路径")
    simplify: bool = Field(default=True, description="是否返回简化的配置")

# 响应模型
class ServerConfigResponse(BaseModel):
    success: bool
    server_info: Dict[str, Any]
    config_content: Optional[str] = None
    parsed_config: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

# 辅助函数
def get_ssh_client_by_server_id(server_id: int, db: Session) -> tuple:
    """
    根据服务器ID获取SSH客户端，仅支持新的Server模型
    返回: (ssh_client, server_info)
    """
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    # 获取服务器信息
    server = db.query(Server).filter(Server.id == server_id).first()
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"未找到ID为 {server_id} 的服务器"
        )
    
    try:
        # 优先尝试使用私钥连接
        if server.encrypted_private_key:
            try:
                private_key_content = decrypt_data(server.encrypted_private_key)
                private_key = paramiko.RSAKey.from_private_key(io.StringIO(private_key_content))
                
                ssh_client.connect(
                    hostname=server.hostname,
                    port=server.port,
                    username=server.username,
                    pkey=private_key,
                    timeout=30
                )
                
                server_info = {
                    "id": server.id,
                    "name": server.name,
                    "hostname": server.hostname,
                    "port": server.port,
                    "username": server.username,
                    "connection_type": "key"
                }
                
                return ssh_client, server_info
                
            except Exception as e:
                # 私钥连接失败，如果有密码则尝试密码连接
                if not server.encrypted_password:
                    ssh_client.close()
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
                timeout=30
            )
            
            server_info = {
                "id": server.id,
                "name": server.name,
                "hostname": server.hostname,
                "port": server.port,
                "username": server.username,
                "connection_type": "password"
            }
            
            return ssh_client, server_info
            
        # 没有可用的连接凭证
        ssh_client.close()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="服务器没有配置SSH连接凭证（私钥或密码）"
        )
        
    except Exception as e:
        ssh_client.close()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"SSH连接失败: {str(e)}"
        )

@router.post("/servers/{server_id}/config", response_model=ServerConfigResponse)
def get_and_parse_server_config(
    server_id: int,
    request: GetServerConfigRequest,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    根据服务器ID获取并解析配置文件，并保存到数据库
    
    参数:
    - server_id: Server模型的ID
    - request: 包含配置文件路径和是否简化配置的请求参数
    
    返回:
    - 服务器信息
    - 配置文件内容
    - 解析后的配置（可选简化）
    """
    ssh_client = None
    
    try:
        # 获取SSH客户端和服务器信息
        ssh_client, server_info = get_ssh_client_by_server_id(server_id, db)
        
        # 执行cat命令获取配置文件
        stdin, stdout, stderr = ssh_client.exec_command(f"cat {request.config_path}")
        
        # 读取输出
        config_content = stdout.read().decode('utf-8')
        error_output = stderr.read().decode('utf-8')
        
        if error_output:
            return ServerConfigResponse(
                success=False,
                server_info=server_info,
                error=f"读取配置文件失败: {error_output}"
            )
        
        # 解析配置
        parsed_config = XrayRConfigParser.parse_yaml_config(config_content)
        
        # 如果需要简化配置
        simplified_config = None
        if request.simplify:
            simplified_config = XrayRConfigParser.simplify_config(parsed_config)
        
        # 保存配置到数据库
        # 查找是否已有关联该服务器的配置
        xrayr_config = db.query(XrayRConfig).filter(XrayRConfig.server_id == server_id).first()
        
        # 创建默认配置名称
        config_name = f"server_{server_id}_config"
        
        if xrayr_config:
            # 更新现有配置
            xrayr_config.config_path = request.config_path
            xrayr_config.raw_config = config_content
            xrayr_config.parsed_config = simplified_config or parsed_config
            xrayr_config.last_sync_at = datetime.utcnow()
        else:
            # 创建新配置
            xrayr_config = XrayRConfig(
                name=config_name,
                server_id=server_id,
                config_path=request.config_path,
                raw_config=config_content,
                parsed_config=simplified_config or parsed_config,
                last_sync_at=datetime.utcnow()
            )
            db.add(xrayr_config)
        
        db.commit()
        db.refresh(xrayr_config)
        
        # 返回配置信息
        return ServerConfigResponse(
            success=True,
            server_info=server_info,
            config_content=config_content,
            parsed_config=simplified_config if simplified_config else parsed_config
        )
        
    except HTTPException as e:
        # 重新抛出HTTP异常
        raise e
    except Exception as e:
        return ServerConfigResponse(
            success=False,
            server_info={},  # 出错时可能没有服务器信息
            error=f"获取配置文件时发生错误: {str(e)}"
        )
    finally:
        if ssh_client:
            ssh_client.close()

@router.get("/servers/{server_id}/config/check")
def check_config_file_exists(
    server_id: int,
    config_path: str = Query("/etc/XrayR/config.yml", description="配置文件路径"),
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    检查服务器上的配置文件是否存在
    
    参数:
    - server_id: Server模型的ID
    - config_path: 配置文件路径，默认: /etc/XrayR/config.yml
    """
    ssh_client = None
    
    try:
        # 获取SSH客户端和服务器信息
        ssh_client, server_info = get_ssh_client_by_server_id(server_id, db)
        
        # 检查文件是否存在
        stdin, stdout, stderr = ssh_client.exec_command(f"test -f {config_path} && echo 'EXISTS' || echo 'NOT_EXISTS'")
        
        result = stdout.read().decode('utf-8').strip()
        error_output = stderr.read().decode('utf-8').strip()
        
        if error_output:
            return {
                "success": False,
                "server_info": server_info,
                "exists": False,
                "error": f"检查文件失败: {error_output}"
            }
        
        return {
            "success": True,
            "server_info": server_info,
            "exists": result == "EXISTS",
            "config_path": config_path
        }
        
    except Exception as e:
        return {
            "success": False,
            "server_info": {},
            "exists": False,
            "error": f"检查文件时发生错误: {str(e)}"
        }
    finally:
        if ssh_client:
            ssh_client.close()