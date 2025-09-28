from cryptography.fernet import Fernet
from dotenv import load_dotenv
import os

# 加载环境变量
load_dotenv()

# 获取Fernet密钥
FERNET_KEY = os.getenv("FERNET_KEY")

if not FERNET_KEY:
    raise ValueError("FERNET_KEY环境变量未设置。请在.env文件中设置FERNET_KEY或生成一个新的。")

# 创建Fernet实例
fernet = Fernet(FERNET_KEY)

def encrypt_data(data: str) -> str:
    """
    加密数据
    :param data: 要加密的字符串数据
    :return: 加密后的字符串
    """
    return fernet.encrypt(data.encode()).decode()

def decrypt_data(encrypted_data: str) -> str:
    """
    解密数据
    :param encrypted_data: 加密后的字符串
    :return: 解密后的原始字符串
    """
    return fernet.decrypt(encrypted_data.encode()).decode()

def generate_fernet_key() -> str:
    """
    生成新的Fernet密钥
    注意：此函数用于生成新密钥，不应在生产环境中随意调用
    :return: 新生成的Fernet密钥
    """
    return Fernet.generate_key().decode()