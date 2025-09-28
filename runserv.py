#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DPanel 服务启动脚本

这是DPanel项目的启动脚本，提供了便捷的服务启动功能。
支持开发模式和生产模式，包含环境检查和数据库验证。

使用方法:
    python runserv.py                    # 开发模式启动
    python runserv.py --prod             # 生产模式启动
    python runserv.py --port 8080        # 指定端口
    python runserv.py --host 0.0.0.0     # 指定主机
    python runserv.py --help             # 查看帮助

环境要求:
    - Python 3.8+
    - 已安装requirements.txt中的依赖
    - 已配置.env文件
    - 已初始化数据库
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path
from dotenv import load_dotenv

# 添加src目录到Python路径
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

def check_python_version():
    """检查Python版本"""
    if sys.version_info < (3, 8):
        print("✗ Python版本过低，需要Python 3.8或更高版本")
        print(f"当前版本: {sys.version}")
        return False
    print(f"✓ Python版本: {sys.version.split()[0]}")
    return True

def check_env_file():
    """检查环境配置文件"""
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if not env_file.exists():
        print("✗ 未找到.env文件")
        if env_example.exists():
            print("请复制.env.example为.env并配置相应参数:")
            print("  Windows: copy .env.example .env")
            print("  Linux/Mac: cp .env.example .env")
        else:
            print("请创建.env文件并配置必要的环境变量")
        return False
    
    print("✓ 找到.env配置文件")
    return True

def check_dependencies():
    """检查依赖包是否安装"""
    try:
        import fastapi
        import uvicorn
        import sqlalchemy
        import cryptography
        import paramiko
        print("✓ 核心依赖包已安装")
        return True
    except ImportError as e:
        print(f"✗ 缺少依赖包: {e}")
        print("请运行: pip install -r requirements.txt")
        return False

def check_database():
    """检查数据库配置和连接"""
    try:
        # 加载环境变量
        load_dotenv()
        
        from database import engine, DATABASE_TYPE, DATABASE_URL
        from sqlalchemy import text
        
        print(f"✓ 数据库类型: {DATABASE_TYPE}")
        print(f"✓ 数据库URL: {DATABASE_URL}")
        
        # 测试数据库连接
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
            print("✓ 数据库连接正常")
        
        # 检查表是否存在
        with engine.connect() as connection:
            if DATABASE_TYPE == "sqlite":
                result = connection.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
            elif DATABASE_TYPE == "mysql":
                result = connection.execute(text("SHOW TABLES"))
            else:
                result = connection.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = current_schema()"))
            
            tables = [row[0] for row in result.fetchall()]
            
            if not tables:
                print("⚠ 数据库中没有表，请先运行数据库初始化:")
                print("  python init_database.py")
                return False
            
            print(f"✓ 找到数据表: {', '.join(tables)}")
        
        return True
        
    except Exception as e:
        print(f"✗ 数据库检查失败: {e}")
        print("请检查数据库配置或运行数据库初始化:")
        print("  python init_database.py")
        return False

def check_crypto_key():
    """检查加密密钥配置"""
    load_dotenv()
    
    fernet_key = os.getenv("FERNET_KEY")
    secret_key = os.getenv("SECRET_KEY")
    
    if not fernet_key or fernet_key == "your-fernet-key-here":
        print("✗ FERNET_KEY未配置或使用默认值")
        print("请运行生成密钥工具: python generate_fernet_key.py")
        return False
    
    if not secret_key or secret_key == "your-secret-key-here":
        print("⚠ SECRET_KEY未配置或使用默认值")
        print("建议设置一个安全的SECRET_KEY")
    
    print("✓ 加密密钥配置正常")
    return True

def run_environment_checks():
    """运行所有环境检查"""
    print("DPanel 环境检查")
    print("=" * 40)
    
    checks = [
        ("Python版本", check_python_version),
        ("环境配置", check_env_file),
        ("依赖包", check_dependencies),
        ("数据库", check_database),
        ("加密密钥", check_crypto_key),
    ]
    
    all_passed = True
    for name, check_func in checks:
        print(f"\n检查 {name}...")
        if not check_func():
            all_passed = False
    
    print("\n" + "=" * 40)
    if all_passed:
        print("✓ 所有环境检查通过！")
    else:
        print("✗ 环境检查失败，请解决上述问题后重试")
    
    return all_passed

def start_server(host="127.0.0.1", port=8000, reload=True, workers=1):
    """启动服务器"""
    print(f"\n启动DPanel服务器...")
    print(f"主机: {host}")
    print(f"端口: {port}")
    print(f"模式: {'开发模式 (自动重载)' if reload else '生产模式'}")
    
    if not reload and workers > 1:
        print(f"工作进程: {workers}")
    
    print("\n" + "=" * 40)
    print("服务器启动中...")
    print("按 Ctrl+C 停止服务器")
    print("=" * 40)
    
    # 构建uvicorn命令
    cmd = [
        sys.executable, "-m", "uvicorn",
        "src.main:app",
        "--host", host,
        "--port", str(port)
    ]
    
    if reload:
        cmd.append("--reload")
    else:
        cmd.extend(["--workers", str(workers)])
    
    try:
        # 启动服务器
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\n\n服务器已停止")
    except subprocess.CalledProcessError as e:
        print(f"\n✗ 服务器启动失败: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ 启动异常: {e}")
        sys.exit(1)

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="DPanel 服务启动脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python runserv.py                    # 开发模式，默认127.0.0.1:8000
  python runserv.py --prod             # 生产模式
  python runserv.py --port 8080        # 指定端口
  python runserv.py --host 0.0.0.0     # 指定主机
  python runserv.py --prod --workers 4 # 生产模式，4个工作进程
  python runserv.py --no-check         # 跳过环境检查
        """
    )
    
    parser.add_argument(
        "--host", 
        default="127.0.0.1",
        help="服务器主机地址 (默认: 127.0.0.1)"
    )
    
    parser.add_argument(
        "--port", 
        type=int, 
        default=8000,
        help="服务器端口 (默认: 8000)"
    )
    
    parser.add_argument(
        "--prod", 
        action="store_true",
        help="生产模式启动 (禁用自动重载)"
    )
    
    parser.add_argument(
        "--workers", 
        type=int, 
        default=1,
        help="生产模式下的工作进程数 (默认: 1)"
    )
    
    parser.add_argument(
        "--no-check", 
        action="store_true",
        help="跳过环境检查"
    )
    
    parser.add_argument(
        "--check-only", 
        action="store_true",
        help="仅运行环境检查，不启动服务器"
    )
    
    args = parser.parse_args()
    
    print("DPanel 服务启动脚本")
    print("=" * 50)
    
    # 环境检查
    if not args.no_check:
        if not run_environment_checks():
            print("\n环境检查失败，使用 --no-check 跳过检查或解决问题后重试")
            sys.exit(1)
    else:
        print("⚠ 跳过环境检查")
    
    # 如果只是检查环境，则退出
    if args.check_only:
        print("\n环境检查完成，程序退出")
        return
    
    # 启动服务器
    start_server(
        host=args.host,
        port=args.port,
        reload=not args.prod,
        workers=args.workers if args.prod else 1
    )

if __name__ == "__main__":
    main()