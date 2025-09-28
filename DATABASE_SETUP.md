# 数据库设置指南

本文档介绍如何配置和初始化DPanel项目的数据库。

## 支持的数据库

- **SQLite** (默认) - 适用于开发和小型部署
- **MySQL** - 适用于生产环境

## 配置步骤

### 1. 环境变量配置

首先复制环境变量模板文件：

```bash
# Windows
copy .env.example .env

# Linux/Mac
cp .env.example .env
```

### 2. 数据库配置

编辑 `.env` 文件，根据需要选择数据库类型：

#### SQLite 配置 (默认)

```env
# 数据库类型
DATABASE_TYPE=sqlite
# SQLite数据库文件路径
DATABASE_URL=sqlite:///./ssh_keys.db
```

#### MySQL 配置

```env
# 数据库类型
DATABASE_TYPE=mysql
# MySQL连接URL
DATABASE_URL=mysql+pymysql://username:password@localhost:3306/dpanel
```

**MySQL URL 格式说明：**
- `username`: MySQL用户名
- `password`: MySQL密码
- `localhost`: MySQL服务器地址
- `3306`: MySQL端口号
- `dpanel`: 数据库名称

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 初始化数据库

运行数据库初始化程序：

```bash
python init_database.py
```

或者直接运行：

```bash
python src/db_init.py
```

## MySQL 特殊说明

### 安装MySQL驱动

项目使用 `pymysql` 作为MySQL驱动，已包含在 `requirements.txt` 中。

### 创建MySQL数据库

如果使用MySQL，初始化程序会自动尝试创建数据库（如果不存在）。但建议手动创建：

```sql
CREATE DATABASE dpanel CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### MySQL用户权限

确保MySQL用户具有以下权限：
- `CREATE` - 创建数据库和表
- `DROP` - 删除表（如需要）
- `SELECT`, `INSERT`, `UPDATE`, `DELETE` - 基本CRUD操作
- `ALTER` - 修改表结构（用于数据库迁移）

## 初始化程序功能

数据库初始化程序会执行以下操作：

1. **连接测试** - 验证数据库连接是否正常
2. **数据库创建** - 如果是MySQL且数据库不存在，会自动创建
3. **表结构创建** - 创建所有必要的数据表
4. **验证** - 确认表创建成功

## 数据表结构

初始化后会创建以下数据表：

- `ssh_keys` - SSH密钥存储表
- `ssh_passwords` - SSH密码存储表

## 故障排除

### SQLite 问题

- **权限错误**: 确保应用有写入当前目录的权限
- **文件锁定**: 确保没有其他程序正在使用数据库文件

### MySQL 问题

- **连接失败**: 检查MySQL服务是否启动
- **认证失败**: 验证用户名和密码是否正确
- **数据库不存在**: 确保数据库已创建或有创建权限
- **驱动问题**: 确保已安装 `pymysql`

### 常见错误

1. **ModuleNotFoundError: No module named 'pymysql'**
   ```bash
   pip install pymysql
   ```

2. **Access denied for user**
   - 检查MySQL用户名和密码
   - 确保用户有访问指定数据库的权限

3. **Can't connect to MySQL server**
   - 检查MySQL服务是否启动
   - 验证服务器地址和端口

## 环境变量参考

完整的 `.env` 文件示例：

```env
# 数据库配置
DATABASE_TYPE=sqlite
DATABASE_URL=sqlite:///./ssh_keys.db

# Fernet加密密钥
FERNET_KEY=your-fernet-key-here

# FastAPI配置
SECRET_KEY=your-secret-key-here
DEBUG=True
```

## 数据库迁移

如果需要从SQLite迁移到MySQL或反之，请：

1. 导出现有数据
2. 更新 `.env` 配置
3. 重新运行初始化程序
4. 导入数据

**注意**: 数据迁移需要额外的脚本，当前初始化程序只负责创建表结构。