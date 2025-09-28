from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

# 加载环境变量
load_dotenv()

# 创建FastAPI应用实例
app = FastAPI(
    title="SSH密钥管理系统",
    description="用于存储SSH密钥和使用SSH连接服务器进行操作的后端程序",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# 配置CORS
origins = [
    "*",  # 在生产环境中应限制为特定的域名
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 导入路由
from src.api import auth, ssh_keys, ssh_passwords, ssh_operations

# 注册路由
app.include_router(auth.router, prefix="/auth", tags=["认证"])
app.include_router(ssh_keys.router, prefix="/ssh-keys", tags=["SSH密钥管理"])
app.include_router(ssh_passwords.router, prefix="/ssh-passwords", tags=["SSH密码管理"])
app.include_router(ssh_operations.router, prefix="/ssh", tags=["SSH操作"])

# 根路径路由
@app.get("/")
def read_root():
    return {
        "message": "欢迎使用SSH密钥管理系统",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }