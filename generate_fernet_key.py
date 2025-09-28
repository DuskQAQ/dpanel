#!/usr/bin/env python3
"""
生成有效的Fernet加密密钥
Fernet密钥必须是32字节的url-safe base64编码字符串
"""
from cryptography.fernet import Fernet

# 生成新的Fernet密钥
fernet_key = Fernet.generate_key()

# 输出密钥（已编码为url-safe base64字符串）
print("生成的有效Fernet密钥:")
print(fernet_key.decode())
print("\n请将此密钥复制到.env文件中的FERNET_KEY变量中")