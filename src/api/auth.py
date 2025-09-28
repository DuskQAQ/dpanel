from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import secrets
from dotenv import load_dotenv
import os

# 加载环境变量
load_dotenv()

router = APIRouter()
security = HTTPBasic()

# 在实际生产环境中，这里应该从数据库或其他安全存储中获取用户凭证
# 这里使用环境变量中的配置作为演示
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin")

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

@router.get("/check")
def check_auth(username: str = Depends(verify_credentials)):
    """
    检查认证状态
    需要基本认证
    """
    return {
        "message": f"认证成功，欢迎 {username}"
    }