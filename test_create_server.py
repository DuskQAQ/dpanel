import requests
import json

# API URL
# 注意：servers.py中的router已经有prefix="/servers"，main.py中又添加了一次，所以实际路径是/servers/servers/
url = "http://localhost:8000/servers/servers/"

# 测试数据
server_data = {
    "name": "测试服务器",
    "hostname": "192.168.1.100",
    "port": 22,
    "username": "root",
    "password": "test_password",
    "description": "用于测试的服务器"
}

# 添加基本认证（如果需要）
# 注意：在实际环境中，请使用环境变量或安全的方式存储凭证
# auth = ('admin', 'admin')

print(f"尝试创建服务器: {server_data['name']}")
print(f"API URL: {url}")

try:
    # 发送POST请求创建服务器
    # 如果需要认证，取消下面这行的注释并注释掉下面没有auth参数的那行
    # response = requests.post(url, json=server_data, auth=auth)
    response = requests.post(url, json=server_data)
    
    # 检查响应状态
    if response.status_code == 201:
        # 创建成功
        server = response.json()
        print(f"\n✓ 服务器创建成功!")
        print(f"服务器ID: {server['id']}")
        print(f"服务器名称: {server['name']}")
        print(f"主机名: {server['hostname']}")
        print(f"端口: {server['port']}")
        print(f"用户名: {server['username']}")
        print(f"是否有密码: {server['has_password']}")
        print(f"创建时间: {server['created_at']}")
        print(f"更新时间: {server['updated_at']}")
    else:
        # 创建失败
        print(f"\n✗ 服务器创建失败!")
        print(f"状态码: {response.status_code}")
        try:
            # 尝试解析错误响应
            error_data = response.json()
            print(f"错误详情: {json.dumps(error_data, ensure_ascii=False, indent=2)}")
        except json.JSONDecodeError:
            print(f"响应内容: {response.text}")
            
except Exception as e:
    print(f"\n✗ 发生异常: {str(e)}")

print("\n测试完成")