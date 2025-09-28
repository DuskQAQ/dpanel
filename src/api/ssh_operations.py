from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
import paramiko
import io
import time

from src.database import get_db
from src.models import SSHKey, SSHPassword
from src.crypto import decrypt_data
from src.api.auth import verify_credentials

router = APIRouter(dependencies=[Depends(verify_credentials)])

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

# 创建SSH客户端连接（使用密钥）
def create_ssh_client_with_key(ssh_key_id: int, db: Session) -> paramiko.SSHClient:
    """
    创建SSH客户端连接（使用密钥）
    :param ssh_key_id: SSH密钥ID
    :param db: 数据库会话
    :return: paramiko SSH客户端对象
    """
    # 获取SSH密钥
    db_ssh_key = db.query(SSHKey).filter(SSHKey.id == ssh_key_id).first()
    if db_ssh_key is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SSH密钥不存在"
        )
    
    # 解密私钥
    try:
        private_key_str = decrypt_data(db_ssh_key.encrypted_private_key)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"解密SSH密钥失败: {str(e)}"
        )
    
    # 创建SSH客户端
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    # 加载私钥
    try:
        private_key = paramiko.RSAKey.from_private_key(io.StringIO(private_key_str))
    except paramiko.SSHException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"SSH私钥格式无效: {str(e)}"
        )
    
    # 连接到远程服务器
    try:
        ssh_client.connect(
            hostname=db_ssh_key.hostname,
            port=db_ssh_key.port,
            username=db_ssh_key.username,
            pkey=private_key,
            timeout=10
        )
    except paramiko.AuthenticationException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="SSH认证失败"
        )
    except paramiko.SSHException as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"SSH连接失败: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"连接远程服务器失败: {str(e)}"
        )
    
    return ssh_client

# 创建SSH客户端连接（使用密码）
def create_ssh_client_with_password(ssh_password_id: int, db: Session) -> paramiko.SSHClient:
    """
    创建SSH客户端连接（使用密码）
    :param ssh_password_id: SSH密码连接ID
    :param db: 数据库会话
    :return: paramiko SSH客户端对象
    """
    # 获取SSH密码连接
    db_ssh_password = db.query(SSHPassword).filter(SSHPassword.id == ssh_password_id).first()
    if db_ssh_password is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SSH密码连接不存在"
        )
    
    # 解密密码
    try:
        password = decrypt_data(db_ssh_password.encrypted_password)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"解密SSH密码失败: {str(e)}"
        )
    
    # 创建SSH客户端
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    # 连接到远程服务器
    try:
        ssh_client.connect(
            hostname=db_ssh_password.hostname,
            port=db_ssh_password.port,
            username=db_ssh_password.username,
            password=password,
            timeout=10
        )
    except paramiko.AuthenticationException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="SSH认证失败"
        )
    except paramiko.SSHException as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"SSH连接失败: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"连接远程服务器失败: {str(e)}"
        )
    
    return ssh_client

# 保持向后兼容性的旧函数
def create_ssh_client(ssh_key_id: int, db: Session) -> paramiko.SSHClient:
    """
    创建SSH客户端连接（保持向后兼容性）
    :param ssh_key_id: SSH密钥ID
    :param db: 数据库会话
    :return: paramiko SSH客户端对象
    """
    return create_ssh_client_with_key(ssh_key_id, db)

@router.post("/{ssh_key_id}/execute", response_model=SSHCommandResponse)
def execute_ssh_command(
    ssh_key_id: int,
    command_request: SSHCommand,
    db: Session = Depends(get_db)
):
    """
    在远程服务器上执行SSH命令（使用密钥）
    """
    ssh_client = None
    try:
        # 创建SSH客户端连接
        ssh_client = create_ssh_client_with_key(ssh_key_id, db)
        
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

@router.post("/password/{ssh_password_id}/execute", response_model=SSHCommandResponse)
def execute_ssh_command_with_password(
    ssh_password_id: int,
    command_request: SSHCommand,
    db: Session = Depends(get_db)
):
    """
    在远程服务器上执行SSH命令（使用密码）
    """
    ssh_client = None
    try:
        # 创建SSH客户端连接
        ssh_client = create_ssh_client_with_password(ssh_password_id, db)
        
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

@router.get("/{ssh_key_id}/test-connection")
def test_ssh_connection(
    ssh_key_id: int,
    db: Session = Depends(get_db)
):
    """
    测试SSH连接是否正常（使用密钥）
    """
    ssh_client = None
    try:
        # 创建SSH客户端连接
        ssh_client = create_ssh_client_with_key(ssh_key_id, db)
        
        # 执行简单命令测试连接
        stdin, stdout, stderr = ssh_client.exec_command("echo 'Connection test successful'")
        output = stdout.read().decode().strip()
        
        if output == "Connection test successful":
            return {
                "status": "success",
                "message": "SSH连接测试成功"
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

@router.get("/password/{ssh_password_id}/test-connection")
def test_ssh_connection_with_password(
    ssh_password_id: int,
    db: Session = Depends(get_db)
):
    """
    测试SSH连接是否正常（使用密码）
    """
    ssh_client = None
    try:
        # 创建SSH客户端连接
        ssh_client = create_ssh_client_with_password(ssh_password_id, db)
        
        # 执行简单命令测试连接
        stdin, stdout, stderr = ssh_client.exec_command("echo 'Connection test successful'")
        output = stdout.read().decode().strip()
        
        if output == "Connection test successful":
            return {
                "status": "success",
                "message": "SSH连接测试成功"
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