import os
import sys
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError, OperationalError
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

from database import engine, Base, DATABASE_TYPE, DATABASE_URL
from models import SSHKey, SSHPassword, XrayRConfig


def test_database_connection():
    """
    测试数据库连接
    """
    try:
        with engine.connect() as connection:
            # 执行简单查询测试连接
            if DATABASE_TYPE == "sqlite":
                result = connection.execute(text("SELECT 1"))
            elif DATABASE_TYPE == "mysql":
                result = connection.execute(text("SELECT 1"))
            else:
                result = connection.execute(text("SELECT 1"))
            
            result.fetchone()
            print(f"✓ 数据库连接测试成功 ({DATABASE_TYPE})")
            print(f"✓ 数据库URL: {DATABASE_URL}")
            return True
    except OperationalError as e:
        print(f"✗ 数据库连接失败: {e}")
        if DATABASE_TYPE == "mysql":
            print("请检查:")
            print("1. MySQL服务是否启动")
            print("2. 数据库连接信息是否正确")
            print("3. 是否安装了pymysql: pip install pymysql")
        return False
    except Exception as e:
        print(f"✗ 数据库连接测试失败: {e}")
        return False


def create_database_if_not_exists():
    """
    如果是MySQL，尝试创建数据库（如果不存在）
    """
    if DATABASE_TYPE != "mysql":
        return True
    
    try:
        # 解析数据库URL获取数据库名
        from urllib.parse import urlparse
        from sqlalchemy import create_engine as create_temp_engine
        
        parsed = urlparse(DATABASE_URL)
        db_name = parsed.path.lstrip('/')
        
        if not db_name:
            print("✗ MySQL数据库名称未指定")
            return False
        
        # 创建不包含数据库名的连接URL
        base_url = f"{parsed.scheme}://{parsed.netloc}/"
        
        # 连接到MySQL服务器（不指定数据库）
        temp_engine = create_temp_engine(base_url)
        
        with temp_engine.connect() as connection:
            # 检查数据库是否存在
            result = connection.execute(text(f"SHOW DATABASES LIKE '{db_name}'"))
            if not result.fetchone():
                # 创建数据库
                connection.execute(text(f"CREATE DATABASE {db_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
                connection.commit()
                print(f"✓ 创建数据库: {db_name}")
            else:
                print(f"✓ 数据库已存在: {db_name}")
        
        temp_engine.dispose()
        return True
        
    except Exception as e:
        print(f"✗ 创建数据库失败: {e}")
        return False


def init_db():
    """
    初始化数据库
    创建所有表结构
    """
    print("=== 数据库初始化程序 ===")
    print(f"数据库类型: {DATABASE_TYPE}")
    
    # 1. 测试数据库连接
    if not test_database_connection():
        print("\n数据库连接失败，初始化终止")
        return False
    
    # 2. 如果是MySQL，尝试创建数据库
    if not create_database_if_not_exists():
        print("\n数据库创建失败，初始化终止")
        return False
    
    # 3. 创建所有表
    try:
        print("\n开始创建数据表...")
        Base.metadata.create_all(bind=engine)
        
        # 验证表是否创建成功
        with engine.connect() as connection:
            if DATABASE_TYPE == "sqlite":
                result = connection.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
            elif DATABASE_TYPE == "mysql":
                result = connection.execute(text("SHOW TABLES"))
            else:
                result = connection.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = current_schema()"))
            
            tables = [row[0] for row in result.fetchall()]
            
            if tables:
                print("✓ 数据表创建成功:")
                for table in tables:
                    print(f"  - {table}")
            else:
                print("⚠ 未发现任何数据表")
        
        print("\n✓ 数据库初始化完成！")
        return True
        
    except SQLAlchemyError as e:
        print(f"✗ 创建数据表失败: {e}")
        return False
    except Exception as e:
        print(f"✗ 数据库初始化失败: {e}")
        return False


def main():
    """
    主函数
    """
    try:
        success = init_db()
        if success:
            print("\n数据库初始化成功，程序即将退出...")
            sys.exit(0)
        else:
            print("\n数据库初始化失败，程序即将退出...")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n用户中断，程序退出")
        sys.exit(1)
    except Exception as e:
        print(f"\n程序异常: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()