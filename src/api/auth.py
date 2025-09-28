from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import secrets
from dotenv import load_dotenv
import os
from typing import Optional

# 加载环境变量
load_dotenv()

router = APIRouter()

# 本地模式配置
LOCAL_MODE = os.getenv("LOCAL_MODE", "false").lower() in ("true", "1", "yes", "on")

# 根据模式设置安全策略
security = HTTPBasic(auto_error=not LOCAL_MODE)

# 在实际生产环境中，这里应该从数据库或其他安全存储中获取用户凭证
# 这里使用环境变量中的配置作为演示
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin")

# 本地模式下的空认证函数
def no_auth():
    """
    本地模式下不需要认证
    """
    return "local_user"

# 验证凭据
def verify_credentials(credentials: HTTPBasicCredentials = Depends(security)):
    """
    验证用户凭据
    :param credentials: HTTP基本认证的凭据
    :return: 验证成功的用户名
    """
    # 使用secrets.compare_digest进行安全比较，防止时序攻击
    is_username_correct = secrets.compare_digest(
        credentials.username, ADMIN_USERNAME
    )
    is_password_correct = secrets.compare_digest(
        credentials.password, ADMIN_PASSWORD
    )
    
    if not (is_username_correct and is_password_correct):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

# 条件性认证依赖
def get_current_user(credentials: Optional[HTTPBasicCredentials] = Depends(security)):
    """
    根据LOCAL_MODE配置决定是否需要认证
    """
    if LOCAL_MODE:
        # 本地模式下不需要认证
        return "local_user"
    else:
        # 非本地模式下需要认证
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="需要认证",
                headers={"WWW-Authenticate": "Basic"},
            )
        
        # 验证凭据
        is_username_correct = secrets.compare_digest(
            credentials.username, ADMIN_USERNAME
        )
        is_password_correct = secrets.compare_digest(
            credentials.password, ADMIN_PASSWORD
        )
        
        if not (is_username_correct and is_password_correct):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误",
                headers={"WWW-Authenticate": "Basic"},
            )
        return credentials.username

@router.get("/check")
def check_auth(username: str = Depends(get_current_user)):
    """
    检查认证状态
    根据LOCAL_MODE决定是否需要认证
    """
    if LOCAL_MODE:
        return {
            "message": "本地模式，无需认证",
            "mode": "local",
            "user": username
        }
    else:
        return {
            "message": f"认证成功，欢迎 {username}",
            "mode": "authenticated",
            "user": username
        }

@router.get("/status")
def auth_status():
    """
    获取认证状态信息
    """
    return {
        "local_mode": LOCAL_MODE,
        "auth_required": not LOCAL_MODE,
        "message": "本地模式，无需认证" if LOCAL_MODE else "需要用户认证"
    }