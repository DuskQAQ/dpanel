# SSH密钥管理系统

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