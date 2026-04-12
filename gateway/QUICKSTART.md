# Gateway API - 快速启动指南

## 🚀 首次运行

### 1. 生成安全密钥

```bash
# 方法1：使用提供的脚本
python generate_key.py

# 方法2：使用 Python 命令
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 2. 配置环境变量

复制配置模板并修改：

```bash
cp .env.example .env
```

编辑 `.env` 文件，**必须修改以下配置**：

```bash
# ⚠️ 必填项
HMAC_SECRET_KEY=your-generated-key-here  # 使用上一步生成的密钥
REDIS_PASSWORD=your-redis-password        # Redis 密码
CORS_ORIGINS=["https://your-domain.com"]  # 你的域名
DEBUG=False                                # 生产环境设为 False
```

### 3. 启动服务

```bash
# HTTP 模式（默认）
python main.py

# HTTPS 模式（需要先配置 SSL 证书）
# 详见 docs/HTTPS配置指南.md
python main.py
```

**启动成功标志**：

```
✅ 已启动服务 [user-service] 的健康检查
✅ 已启动服务 [order-service] 的健康检查
INFO:     Gateway 启动成功: http://0.0.0.0:9000
```

如果启用了 HTTPS：

```
✅ HTTPS 已启用 - 证书: /path/to/cert.pem
INFO:     Gateway 启动成功: https://0.0.0.0:9000
```

### 4. 验证启动

#### 健康检查端点

```bash
# 基础健康检查
curl http://localhost:9000/health

# 详细健康检查（包含依赖状态）
curl http://localhost:9000/health | jq .
```

**预期响应**：

```json
{
  "status": "healthy",
  "service": "gateway",
  "checks": {
    "gateway": "healthy",
    "redis": "healthy",
    "consul": "disabled"
  },
  "timestamp": 1234567890
}
```

#### 手动触发服务健康检查

```bash
curl -X POST http://localhost:9000/health/check-services | jq .
```

**预期响应**：

```json
{
  "message": "Health check completed",
  "services": {
    "user-service": {
      "total_instances": 2,
      "healthy_instances": 2,
      "instances": [
        {
          "id": "instance-1",
          "host": "localhost",
          "port": 8081,
          "status": "healthy"
        }
      ]
    }
  },
  "timestamp": 1234567890
}
```

---

## 🔧 常用配置

### 启用 HTTPS（生产环境推荐）

1. 获取 SSL 证书（Let's Encrypt 或商业证书）
2. 修改 `.env`：

```bash
HTTPS_ENABLED=true
SSL_CERT_PATH=/path/to/cert.pem
SSL_KEY_PATH=/path/to/key.pem
SSL_VERIFY=true
```

3. 启动时使用 SSL：

```bash
uvicorn main:app \
  --host 0.0.0.0 \
  --port 9000 \
  --ssl-certfile /path/to/cert.pem \
  --ssl-keyfile /path/to/key.pem
```

### 启用 Consul 服务发现

```bash
CONSUL_ENABLED=true
CONSUL_HOST=consul-server-host
CONSUL_PORT=8500
```

### 调整限流策略

```bash
RATE_LIMIT_MAX_REQUESTS=100    # 每窗口最大请求数
RATE_LIMIT_WINDOW_SECONDS=60   # 窗口大小（秒）
```

---

## 📊 监控和管理

### 查看熔断器状态

```bash
curl http://localhost:9000/api/circuit-breakers
```

### 管理 CORS 配置

```bash
# 查看当前配置
curl http://localhost:9000/api/config/cors

# 更新配置
curl -X PUT http://localhost:9000/api/config/cors \
  -H "Content-Type: application/json" \
  -d '{
    "origins": ["https://example.com"],
    "credentials": true,
    "methods": ["GET", "POST"],
    "headers": ["Authorization"]
  }'
```

### 管理 HMAC 密钥

```bash
# 创建新密钥
curl -X POST http://localhost:9000/api/config/hmac/key \
  -H "Content-Type: application/json" \
  -d '{"app_id": "my-service"}'

# 列出所有密钥
curl http://localhost:9000/api/config/hmac/keys
```

---

## ⚠️ 生产环境检查清单

部署前请确认：

- [ ] `DEBUG=False`
- [ ] `HMAC_SECRET_KEY` 已设置为强密钥（至少32字符）
- [ ] `REDIS_PASSWORD` 已设置
- [ ] `CORS_ORIGINS` 只包含允许的域名
- [ ] 启用了 HTTPS（或通过反向代理）
- [ ] 配置了日志轮转
- [ ] Redis 使用哨兵或集群模式
- [ ] 设置了合理的限流阈值
- [ ] 配置了监控和告警

---

## 🐛 故障排查

### 启动失败：HMAC_SECRET_KEY 未配置

```
RuntimeError: HMAC 已启用但未配置 HMAC_SECRET_KEY！
```

**解决方法**：

```bash
# 方法1：在 .env 文件中配置
echo "HMAC_SECRET_KEY=$(python -c 'import secrets; print(secrets.token_urlsafe(32))')" >> .env

# 方法2：设置环境变量
export HMAC_SECRET_KEY=$(python -c 'import secrets; print(secrets.token_urlsafe(32))')
```

### Redis 连接失败

```
redis.exceptions.ConnectionError: Error connecting to localhost:6379
```

**解决方法**：

1. 检查 Redis 是否运行：`redis-cli ping`
2. 检查 `.env` 中的 `REDIS_PASSWORD` 是否正确
3. 检查防火墙规则

### 服务注册失败

检查 Consul 是否运行：

```bash
curl http://localhost:8500/v1/agent/self
```

---

## 📚 更多信息

- [API 文档](http://localhost:9000/docs)
- [功能模块说明](docs/功能模块说明.md)
- [工程提示词](docs/工程提示词.md)