from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
import paramiko
import io
import time
from fastapi import APIRouter, Depends, HTTPException, status

from ..database import get_db
from ..models import Server
from ..crypto import decrypt_data
from .auth import get_current_user

router = APIRouter()

# 请求模型
class SSHCommand(BaseModel):
    command: str = Field(..., description="要在远程服务器上执行的命令")
    timeout: int = Field(default=30, ge=5, le=300, description="命令执行超时时间(秒)")

class SSHTunnelRequest(BaseModel):
    local_port: int = Field(..., ge=1024, le=65535, description="本地端口")
    remote_host: str = Field(..., description="远程主机")
    remote_port: int = Field(..., ge=1, le=65535, description="远程端口")
    timeout: int = Field(default=60, ge=10, le=300, description="隧道超时时间(秒)")

# 响应模型
class SSHCommandResponse(BaseModel):
    stdout: str
    stderr: str
    exit_code: int

# 创建SSH客户端连接（使用服务器ID，优先密钥然后密码）
def create_ssh_client_with_server(server_id: int, db: Session) -> paramiko.SSHClient:
    """
    创建SSH客户端连接（使用服务器ID，优先使用密钥，如果不存在则使用密码）
    :param server_id: 服务器ID
    :param db: 数据库会话
    :return: paramiko SSH客户端对象
    """
    # 获取服务器信息
    server = db.query(Server).filter(Server.id == server_id).first()
    if server is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="服务器不存在"
        )
    
    # 创建SSH客户端
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    # 优先尝试使用密钥连接
    if server.encrypted_private_key:
        try:
            # 解密私钥
            private_key_str = decrypt_data(server.encrypted_private_key)
            private_key = paramiko.RSAKey.from_private_key(io.StringIO(private_key_str))
            
            ssh_client.connect(
                hostname=server.hostname,
                port=server.port,
                username=server.username,
                pkey=private_key,
                timeout=10
            )
            return ssh_client
        except Exception as key_error:
            # 密钥连接失败，如果有密码则尝试密码连接
            if server.encrypted_password:
                # 继续尝试密码连接
                pass
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"SSH密钥连接失败: {str(key_error)}"
                )
    
    # 使用密码连接
    if server.encrypted_password:
        try:
            # 解密密码
            password = decrypt_data(server.encrypted_password)
            
            ssh_client.connect(
                hostname=server.hostname,
                port=server.port,
                username=server.username,
                password=password,
                timeout=10
            )
            return ssh_client
        except paramiko.AuthenticationException:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="SSH密码认证失败"
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"SSH密码连接失败: {str(e)}"
            )
    
    # 既没有密钥也没有密码
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="服务器既没有配置SSH密钥也没有配置SSH密码"
    )

@router.post("/servers/{server_id}/execute", response_model=SSHCommandResponse)
def execute_ssh_command_with_server(
    server_id: int,
    command_request: SSHCommand,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    在远程服务器上执行SSH命令（使用服务器ID，优先密钥然后密码）
    """
    ssh_client = None
    try:
        # 创建SSH客户端连接
        ssh_client = create_ssh_client_with_server(server_id, db)
        
        # 执行命令
        stdin, stdout, stderr = ssh_client.exec_command(
            command_request.command,
            timeout=command_request.timeout
        )
        
        # 获取命令输出
        stdout_str = stdout.read().decode()
        stderr_str = stderr.read().decode()
        exit_code = stdout.channel.recv_exit_status()
        
        return {
            "stdout": stdout_str,
            "stderr": stderr_str,
            "exit_code": exit_code
        }
    except Exception as e:
        # 如果已经有HTTPException，直接抛出
        if isinstance(e, HTTPException):
            raise
        # 否则包装为500错误
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"执行SSH命令失败: {str(e)}"
        )
    finally:
        # 关闭SSH连接
        if ssh_client:
            ssh_client.close()

@router.get("/servers/{server_id}/test-connection")
def test_ssh_connection_with_server(
    server_id: int,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    测试SSH连接是否正常（使用服务器ID，优先密钥然后密码）
    """
    ssh_client = None
    try:
        # 创建SSH客户端连接
        ssh_client = create_ssh_client_with_server(server_id, db)
        
        # 执行简单命令测试连接
        stdin, stdout, stderr = ssh_client.exec_command("echo 'Connection test successful'")
        output = stdout.read().decode().strip()
        
        if output == "Connection test successful":
            return {
                "status": "success",
                "message": "SSH连接测试成功",
                "connection_type": "key" if server.encrypted_private_key else "password"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="SSH连接测试失败: 命令执行结果不符合预期"
            )
    except Exception as e:
        # 如果已经有HTTPException，直接抛出
        if isinstance(e, HTTPException):
            raise
        # 否则包装为500错误
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"SSH连接测试失败: {str(e)}"
        )
    finally:
        # 关闭SSH连接
        if ssh_client:
            ssh_client.close()