# DPanel

SSH密钥管理面板 - 一个安全的SSH连接管理工具

## 功能特性

- 🔐 SSH密钥和密码的安全存储
- 🗄️ 支持SQLite和MySQL数据库
- 🔒 使用Fernet加密保护敏感信息
- 🚀 基于FastAPI的现代Web API
- 📱 RESTful API设计

## 快速开始

### 1. 环境配置

```bash
# 克隆项目
git clone <repository-url>
cd dpanel

# 复制环境配置文件
copy .env.example .env  # Windows
cp .env.example .env    # Linux/Mac

# 安装依赖
pip install -r requirements.txt
```

### 2. 数据库初始化

#### SQLite (默认，推荐用于开发)

```bash
# 使用默认SQLite配置
python init_database.py
```

#### MySQL (推荐用于生产)

```bash
# 1. 编辑.env文件，配置MySQL连接
# DATABASE_TYPE=mysql
# DATABASE_URL=mysql+pymysql://username:password@localhost:3306/dpanel

# 2. 测试MySQL连接
python test_mysql_config.py

# 3. 初始化数据库
python init_database.py
```

### 3. 启动应用

```bash
# 开发模式
uvicorn src.main:app --reload

# 生产模式
uvicorn src.main:app --host 0.0.0.0 --port 8000
```

## 项目结构

```
dpanel/
├── src/                    # 源代码目录
│   ├── api/               # API路由
│   │   ├── auth.py        # 认证相关
│   │   ├── ssh_keys.py    # SSH密钥管理
│   │   ├── ssh_operations.py  # SSH操作
│   │   └── ssh_passwords.py   # SSH密码管理
│   ├── database.py        # 数据库配置
│   ├── models.py          # 数据模型
│   ├── crypto.py          # 加密工具
│   ├── db_init.py         # 数据库初始化
│   └── main.py            # 应用入口
├── init_database.py       # 独立数据库初始化工具
├── test_mysql_config.py   # MySQL配置测试工具
├── generate_fernet_key.py # 加密密钥生成工具
├── requirements.txt       # Python依赖
├── .env.example          # 环境变量模板
├── DATABASE_SETUP.md     # 数据库设置指南
└── README.md             # 项目说明
```

## 数据库支持

### SQLite
- 适用于开发和小型部署
- 无需额外配置
- 数据存储在本地文件中

### MySQL
- 适用于生产环境
- 支持高并发访问
- 需要MySQL服务器

详细配置请参考 [DATABASE_SETUP.md](DATABASE_SETUP.md)

## 安全特性

- **加密存储**: 所有SSH私钥和密码使用Fernet加密存储
- **安全传输**: API支持HTTPS
- **访问控制**: 基于JWT的身份认证
- **数据隔离**: 每个用户的数据完全隔离

## API文档

启动应用后，访问以下地址查看API文档：

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 开发工具

### 数据库初始化
```bash
# 初始化数据库（支持SQLite和MySQL）
python init_database.py

# 或直接运行
python src/db_init.py
```

### MySQL测试
```bash
# 测试MySQL连接配置
python test_mysql_config.py
```

### 生成加密密钥
```bash
# 生成新的Fernet加密密钥
python generate_fernet_key.py
```

## 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `DATABASE_TYPE` | 数据库类型 (sqlite/mysql) | sqlite |
| `DATABASE_URL` | 数据库连接URL | sqlite:///./ssh_keys.db |
| `FERNET_KEY` | 加密密钥 | 需要生成 |
| `SECRET_KEY` | JWT密钥 | 需要设置 |
| `DEBUG` | 调试模式 | True |

## 故障排除

### 常见问题

1. **ModuleNotFoundError**: 确保在正确的目录运行命令
2. **数据库连接失败**: 检查数据库配置和服务状态
3. **加密错误**: 确保FERNET_KEY正确配置

### 获取帮助

- 查看 [DATABASE_SETUP.md](DATABASE_SETUP.md) 了解数据库配置
- 检查日志文件获取详细错误信息
- 确保所有依赖正确安装

## 许可证

[添加许可证信息]

## 贡献

欢迎提交Issue和Pull Request！

这是一个用于存储SSH密钥和使用SSH连接服务器进行操作的后端程序。该系统使用FastAPI框架开发，采用最小化的 `.env` + Fernet加密 + 数据库 的方式存储敏感的SSH密钥信息。

## 功能特点

- **安全存储SSH密钥**：使用Fernet对称加密算法加密存储SSH私钥
- **SSH密钥管理**：支持添加、查看、更新和删除SSH密钥信息
- **远程服务器操作**：使用存储的SSH密钥连接远程服务器并执行命令
- **连接测试**：支持测试SSH连接是否正常
- **基础认证**：提供简单的HTTP Basic认证机制

## 技术栈

- **后端框架**：FastAPI
- **数据库**：SQLAlchemy + SQLite（默认，可配置为其他数据库）
- **加密**：cryptography（Fernet加密）
- **SSH客户端**：paramiko
- **环境管理**：python-dotenv
- **API文档**：Swagger UI (FastAPI内置)

## 环境要求

- Python 3.8+ 
- pip

## 安装步骤

1. **克隆项目代码**（如果有git仓库）
   ```bash
   git clone <repository-url>
   cd ssh-key-management
   ```

2. **创建虚拟环境**
   ```bash
   python -m venv venv
   ```

3. **激活虚拟环境**
   - Windows:
     ```bash
     venv\Scripts\activate
     ```
   - Linux/Mac:
     ```bash
     source venv/bin/activate
     ```

4. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

5. **配置环境变量**
   - 复制 `.env.example` 文件并重命名为 `.env`
     ```bash
     cp .env.example .env
     ```
   - 编辑 `.env` 文件，设置必要的环境变量
     ```env
     # 数据库配置
     DATABASE_URL=sqlite:///./ssh_keys.db
     
     # Fernet加密密钥（用于加密SSH私钥）
     FERNET_KEY=your-fernet-key-here
     
     # FastAPI配置
     SECRET_KEY=your-secret-key-here
     DEBUG=True
     
     # 认证配置
     ADMIN_USERNAME=admin
     ADMIN_PASSWORD=admin
     ```
   - 生成Fernet密钥的方法：
     ```python
     from cryptography.fernet import Fernet
     print(Fernet.generate_key().decode())
     ```

6. **初始化数据库**
   ```bash
   python -m src.db_init
   ```

## 运行应用

```bash
uvicorn src.main:app --reload
```

应用启动后，可以通过以下URL访问：
- API文档：http://localhost:8000/docs
- ReDoc文档：http://localhost:8000/redoc
- 首页：http://localhost:8000/

## API使用说明

### 认证

所有需要认证的API都使用HTTP Basic认证，默认用户名和密码为`admin`/`admin`（可在.env文件中修改）。

### SSH密钥管理

- **添加SSH密钥**：`POST /ssh-keys/`
- **获取所有SSH密钥**：`GET /ssh-keys/`
- **获取单个SSH密钥**：`GET /ssh-keys/{ssh_key_id}`
- **更新SSH密钥**：`PUT /ssh-keys/{ssh_key_id}`
- **删除SSH密钥**：`DELETE /ssh-keys/{ssh_key_id}`

### SSH操作

- **执行SSH命令**：`POST /ssh/{ssh_key_id}/execute`
- **测试SSH连接**：`GET /ssh/{ssh_key_id}/test-connection`

## 安全注意事项

1. **环境变量保护**：`.env`文件包含敏感信息，请确保该文件不会被提交到版本控制系统中
2. **密码强度**：在生产环境中，请使用强密码并定期更换
3. **密钥管理**：定期更新和轮换SSH密钥
4. **访问控制**：在生产环境中，考虑使用更严格的认证和授权机制
5. **HTTPS**：在生产环境中，请配置HTTPS以加密传输的数据

## 部署建议

1. 使用Docker容器化部署
2. 配置反向代理（如Nginx）处理HTTPS和负载均衡
3. 考虑使用更强大的数据库（如PostgreSQL或MySQL）
4. 配置适当的日志记录和监控
5. 定期备份数据库

## 开发指南

1. 安装开发依赖：`pip install -e .[dev]`（如果有setup.py文件）
2. 运行测试：`pytest`
3. 代码格式化：`black src/`
4. 代码检查：`pylint src/`

## License

[MIT](https://opensource.org/licenses/MIT)