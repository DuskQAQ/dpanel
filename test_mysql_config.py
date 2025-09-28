#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MySQL配置测试脚本

这个脚本用于测试MySQL数据库配置是否正确。
在实际使用MySQL之前，可以运行此脚本进行测试。

使用方法:
    1. 确保MySQL服务已启动
    2. 在.env文件中配置MySQL连接信息
    3. 运行: python test_mysql_config.py
"""

import os
import sys
from pathlib import Path

# 添加src目录到Python路径
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

# 加载环境变量
load_dotenv()

def test_mysql_connection():
    """
    测试MySQL连接配置
    """
    print("MySQL连接测试")
    print("=" * 30)
    
    # 检查环境变量
    db_type = os.getenv("DATABASE_TYPE", "sqlite").lower()
    db_url = os.getenv("DATABASE_URL", "")
    
    print(f"数据库类型: {db_type}")
    print(f"数据库URL: {db_url}")
    print()
    
    if db_type != "mysql":
        print("⚠ 当前配置不是MySQL，请在.env文件中设置:")
        print("DATABASE_TYPE=mysql")
        print("DATABASE_URL=mysql+pymysql://username:password@localhost:3306/database_name")
        return False
    
    if not db_url or not db_url.startswith("mysql"):
        print("✗ MySQL数据库URL配置错误")
        print("请在.env文件中正确配置DATABASE_URL")
        return False
    
    try:
        # 尝试连接MySQL
        print("正在测试MySQL连接...")
        engine = create_engine(db_url)
        
        with engine.connect() as connection:
            result = connection.execute(text("SELECT VERSION()"))
            version = result.fetchone()[0]
            print(f"✓ MySQL连接成功！")
            print(f"✓ MySQL版本: {version}")
            
            # 测试数据库操作权限
            result = connection.execute(text("SELECT DATABASE()"))
            current_db = result.fetchone()[0]
            print(f"✓ 当前数据库: {current_db}")
            
            # 测试创建表权限
            try:
                connection.execute(text("CREATE TABLE IF NOT EXISTS test_table (id INT PRIMARY KEY)"))
                connection.execute(text("DROP TABLE IF EXISTS test_table"))
                connection.commit()
                print("✓ 数据库操作权限正常")
            except Exception as e:
                print(f"⚠ 数据库操作权限测试失败: {e}")
        
        engine.dispose()
        return True
        
    except OperationalError as e:
        print(f"✗ MySQL连接失败: {e}")
        print("\n请检查:")
        print("1. MySQL服务是否启动")
        print("2. 用户名和密码是否正确")
        print("3. 数据库是否存在")
        print("4. 网络连接是否正常")
        print("5. 是否安装了pymysql: pip install pymysql")
        return False
    except Exception as e:
        print(f"✗ 连接测试失败: {e}")
        return False

def main():
    """
    主函数
    """
    print("DPanel MySQL配置测试工具")
    print("=" * 50)
    print()
    
    # 检查.env文件
    env_file = Path(".env")
    if not env_file.exists():
        print("✗ 未找到.env文件")
        print("请先复制.env.example为.env并配置MySQL连接信息")
        return
    
    success = test_mysql_connection()
    
    if success:
        print("\n✓ MySQL配置测试通过！")
        print("现在可以运行数据库初始化程序:")
        print("python init_database.py")
    else:
        print("\n✗ MySQL配置测试失败")
        print("请检查配置后重试")

if __name__ == "__main__":
    main()