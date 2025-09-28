from src.database import engine, Base
from src.models import SSHKey


def init_db():
    """
    初始化数据库
    创建所有表结构
    """
    # 创建所有表
    Base.metadata.create_all(bind=engine)
    print("数据库初始化完成，所有表已创建")


if __name__ == "__main__":
    init_db()