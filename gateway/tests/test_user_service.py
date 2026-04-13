"""
模拟 User Service - 用于测试 Gateway 的请求转发

这个服务会：
1. 启动时向 Gateway 注册
2. 提供简单的 API 端点
3. 支持健康检查
"""

from fastapi import FastAPI, Request
from contextlib import asynccontextmanager
from pydantic import BaseModel
import uvicorn
import requests
import time
import hashlib
import hmac
import base64
import json

@asynccontextmanager
async def lifespan(app: FastAPI):
    """服务生命周期管理"""
    # 启动时
    print(f"\n{'='*60}")
    print(f"🚀 {SERVICE_NAME} 启动中...")
    print(f"{'='*60}")
    await register_to_gateway()
    print(f"✅ {SERVICE_NAME} 已就绪: http://{SERVICE_HOST}:{SERVICE_PORT}")
    
    yield
    
    # 关闭时
    print(f"\n{'='*60}")
    print(f"🛑 {SERVICE_NAME} 关闭中...")
    print(f"{'='*60}")
    await unregister_from_gateway()


app = FastAPI(title="User Service", version="1.0.0", lifespan=lifespan)

# 服务配置
SERVICE_NAME = "user-service"
SERVICE_ID = f"{SERVICE_NAME}-001"
SERVICE_HOST = "127.0.0.1"
SERVICE_PORT = 8001
GATEWAY_URL = "http://localhost:9000"
HMAC_SECRET_KEY = "test-secret-key-for-development-only-12345678"


def generate_hmac_signature(app_id, secret_key, body="", timestamp=None, nonce=None):
    """生成 HMAC 签名"""
    if timestamp is None:
        timestamp = str(int(time.time()))
    if nonce is None:
        nonce = hashlib.md5(f"{timestamp}{app_id}".encode()).hexdigest()[:16]
    
    message = f"{app_id}\n{timestamp}\n{nonce}\n{body}"
    signature = hmac.new(
        secret_key.encode(),
        message.encode(),
        hashlib.sha256
    ).digest()
    
    return {
        "X-App-ID": app_id,
        "X-Timestamp": timestamp,
        "X-Nonce": nonce,
        "X-Signature": base64.b64encode(signature).decode()
    }


async def register_to_gateway():
    """向 Gateway 注册服务"""
    try:
        # 1. 注册到 Consul（通过 Gateway API）
        service_data = {
            "id": SERVICE_ID,
            "name": SERVICE_NAME,
            "host": SERVICE_HOST,
            "port": SERVICE_PORT,
            "url": f"http://{SERVICE_HOST}:{SERVICE_PORT}",
            "weight": 1,
            "status": "healthy",
            "metadata": {
                "version": "1.0.0",
                "tags": ["user", "api"]
            }
        }
        
        # 2. 获取 HMAC 密钥
        headers = generate_hmac_signature("admin", HMAC_SECRET_KEY)
        response = requests.post(
            f"{GATEWAY_URL}/api/config/hmac/key",
            json={
                "app_id": SERVICE_NAME,
                "secret_key": HMAC_SECRET_KEY
            },
            headers=headers,
            timeout=5
        )
        
        if response.status_code == 200:
            print(f"✅ HMAC 密钥已创建: {SERVICE_NAME}")
        
        # 3. 注册到 Consul
        consul_url = "http://localhost:8500/v1/agent/service/register"
        consul_data = {
            "ID": SERVICE_ID,
            "Name": SERVICE_NAME,
            "Address": SERVICE_HOST,
            "Port": SERVICE_PORT,
            "Tags": ["user", "api", "protocol:http"],
            "Check": {
                "HTTP": f"http://{SERVICE_HOST}:{SERVICE_PORT}/health",
                "Interval": "10s",
                "Timeout": "5s"
            }
        }
        
        response = requests.put(consul_url, json=consul_data, timeout=5)
        if response.status_code == 200:
            print(f"✅ 服务已注册到 Consul: {SERVICE_NAME} ({SERVICE_ID})")
        else:
            print(f"⚠️  注册失败: {response.text}")
            
    except Exception as e:
        print(f"❌ 注册失败: {e}")


async def unregister_from_gateway():
    """从 Gateway 注销服务"""
    try:
        consul_url = f"http://localhost:8500/v1/agent/service/deregister/{SERVICE_ID}"
        response = requests.put(consul_url, timeout=5)
        if response.status_code == 200:
            print(f"✅ 服务已注销: {SERVICE_ID}")
    except Exception as e:
        print(f"❌ 注销失败: {e}")


@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "service": SERVICE_NAME,
        "version": "1.0.0"
    }


@app.get("/api/users")
async def get_users():
    """获取用户列表"""
    return {
        "code": 200,
        "message": "success",
        "data": [
            {"id": 1, "name": "张三", "email": "zhangsan@example.com"},
            {"id": 2, "name": "李四", "email": "lisi@example.com"},
            {"id": 3, "name": "王五", "email": "wangwu@example.com"}
        ]
    }


@app.get("/api/users/{user_id}")
async def get_user(user_id: int):
    """获取单个用户"""
    users = {
        1: {"id": 1, "name": "张三", "email": "zhangsan@example.com", "age": 25},
        2: {"id": 2, "name": "李四", "email": "lisi@example.com", "age": 30},
        3: {"id": 3, "name": "王五", "email": "wangwu@example.com", "age": 28}
    }
    
    user = users.get(user_id)
    if user:
        return {"code": 200, "data": user}
    else:
        return {"code": 404, "message": "用户不存在"}


@app.post("/api/users")
async def create_user(request: Request):
    """创建用户"""
    body = await request.json()
    return {
        "code": 201,
        "message": "用户创建成功",
        "data": {
            "id": 4,
            "name": body.get("name"),
            "email": body.get("email")
        }
    }



if __name__ == "__main__":
    print(f"\n启动 {SERVICE_NAME} on port {SERVICE_PORT}...")
    uvicorn.run(app, host=SERVICE_HOST, port=SERVICE_PORT)
