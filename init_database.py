#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库初始化程序

这是一个独立的数据库初始化工具，用于创建和初始化DPanel项目的数据库。
支持SQLite和MySQL数据库，通过环境变量进行配置。

使用方法:
    python init_database.py

环境变量配置:
    DATABASE_TYPE: 数据库类型 (sqlite 或 mysql)
    DATABASE_URL: 数据库连接URL

示例:
    # SQLite (默认)
    DATABASE_TYPE=sqlite
    DATABASE_URL=sqlite:///./ssh_keys.db
    
    # MySQL
    DATABASE_TYPE=mysql
    DATABASE_URL=mysql+pymysql://username:password@localhost:3306/dpanel
"""

import os
import sys
from pathlib import Path

# 添加src目录到Python路径
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from src.db_init import main

if __name__ == "__main__":
    print("DPanel 数据库初始化工具")
    print("=" * 50)
    print()
    
    # 检查.env文件是否存在
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if not env_file.exists() and env_example.exists():
        print("⚠ 未找到.env文件，但发现.env.example文件")
        print("请复制.env.example为.env并配置相应的数据库参数")
        print()
        print("Windows: copy .env.example .env")
        print("Linux/Mac: cp .env.example .env")
        print()
        
        response = input("是否继续使用默认配置进行初始化? (y/N): ")
        if response.lower() not in ['y', 'yes']:
            print("初始化已取消")
            sys.exit(0)
    
    # 运行初始化
    main()