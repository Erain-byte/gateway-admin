# Gateway 测试指南

本文档说明如何测试 Gateway 的完整功能，包括服务注册、HMAC 验证、请求转发等。

## 📋 测试文件说明

### 1. **test_user_service.py** - 模拟后端服务
- 模拟一个 User Service
- 启动时自动注册到 Consul
- 提供用户管理 API
- 支持健康检查

### 2. **test_frontend_simulation.py** - 前端模拟测试
- 模拟前端通过 Gateway 访问后端
- 包含 HMAC 签名生成和验证
- 测试请求转发、负载均衡、限流等功能

### 3. **test_integration_auto.py** - 自动化集成测试
- 一键启动所有服务
- 自动运行完整测试流程
- 自动清理资源

### 4. **test_gateway_simple.py** - Gateway 核心功能测试
- 测试 CORS、配置管理等
- 不需要后端服务

---

## 🚀 快速开始

### 前置条件

确保以下服务已启动：
```bash
# 1. Redis (密码: 123123)
redis-server --requirepass 123123

# 2. Consul
cd d:\python_project\consul
.\consul.exe agent -dev -data-dir="d:\python_project\consul\data"

# 3. Gateway
cd d:\python_project\gateway
python main.py
```

---

## 🧪 测试方法

### 方法 1: 自动化测试（推荐）

最简单的方式，一键完成所有测试：

```bash
cd d:\python_project\gateway
python test_integration_auto.py
```

**流程：**
1. ✅ 检查 Gateway 状态
2. ✅ 自动启动 User Service
3. ✅ 等待服务注册
4. ✅ 运行前端模拟测试
5. ✅ 自动清理资源

---

### 方法 2: 手动分步测试

#### 步骤 1: 启动 User Service

```bash
cd d:\python_project\gateway
python test_user_service.py
```

你会看到：
```
🚀 user-service 启动中...
✅ HMAC 密钥已创建: user-service
✅ 服务已注册到 Consul: user-service (user-service-001)
✅ user-service 已就绪: http://127.0.0.1:8001
```

#### 步骤 2: 验证服务注册

在浏览器访问 Consul UI：
```
http://localhost:8500/ui/dc1/services
```

或命令行查询：
```bash
curl http://localhost:8500/v1/catalog/service/user-service
```

#### 步骤 3: 运行前端模拟测试

打开新的终端：

```bash
cd d:\python_project\gateway
python test_frontend_simulation.py
```

按提示进行测试。

---

## 📊 测试场景详解

### 测试 1: 服务注册验证

**目的**: 验证服务成功注册到 Consul

**预期结果**:
```
✅ 发现 1 个 user-service 实例:
   - ID: user-service-001
     Address: 127.0.0.1:8001
     Tags: ['user', 'api', 'protocol:http']
```

---

### 测试 2: HMAC 签名认证

**目的**: 验证 HMAC 签名机制工作正常

**测试内容**:
1. ✅ 正确的签名 - 应该通过
2. ❌ 错误的签名 - 应该被拒绝 (401)
3. ❌ 过期的时间戳 - 应该被拒绝 (401)

**HMAC 签名生成示例**:
```python
import hmac
import hashlib
import base64
import time

app_id = "user-service"
secret_key = "test-secret-key-for-development-only-12345678"
timestamp = str(int(time.time()))
nonce = "abc123def456"
body = ""

message = f"{app_id}\n{timestamp}\n{nonce}\n{body}"
signature = hmac.new(
    secret_key.encode(),
    message.encode(),
    hashlib.sha256
).digest()

headers = {
    "X-App-ID": app_id,
    "X-Timestamp": timestamp,
    "X-Nonce": nonce,
    "X-Signature": base64.b64encode(signature).decode()
}
```

---

### 测试 3: 请求转发

**目的**: 验证 Gateway 正确转发请求到后端服务

**测试端点**:
- `GET /user/api/users` - 获取用户列表
- `GET /user/api/users/1` - 获取单个用户
- `POST /user/api/users` - 创建用户

**预期结果**:
```json
{
  "code": 200,
  "message": "success",
  "data": [
    {"id": 1, "name": "张三", "email": "zhangsan@example.com"},
    ...
  ]
}
```

---

### 测试 4: 负载均衡

**目的**: 验证多个服务实例间的负载均衡

**测试方法**:
1. 启动多个 User Service 实例（不同端口）
2. 发送多个请求
3. 观察请求是否分发到不同实例

**注意**: 当前只有 1 个实例，此测试会显示单实例行为

---

### 测试 5: 限流功能

**目的**: 验证限流中间件工作正常

**配置**: 
- 最大请求数: 100 次/分钟
- 算法: 滑动窗口（Redis ZSET）

**测试方法**:
发送超过 100 个快速请求，观察是否返回 429

**预期结果**:
```
✅ 请求 101 被限流 (429)
```

---

### 测试 6: 熔断器

**目的**: 验证后端故障时的熔断保护

**测试方法**:
1. 正常运行时发送请求（应该成功）
2. 停止 User Service
3. 继续发送请求（应该快速失败）

**预期结果**:
```
✅ 后端不可用，返回 503
{
  "error": "Service unavailable",
  "service": "user-service"
}
```

**熔断器状态**:
- CLOSED: 正常状态
- OPEN: 熔断状态（快速失败）
- HALF_OPEN: 半开状态（尝试恢复）

---

### 测试 7: 并发请求

**目的**: 验证 Gateway 的并发处理能力

**测试方法**:
使用线程池发送 10 个并发请求

**预期结果**:
```
✅ 成功请求: 10/10
✅ 平均响应时间: 50.23ms
✅ 并发处理能力良好
```

---

## 🔍 调试技巧

### 查看 Gateway 日志

Gateway 运行时会在终端输出详细日志：

```
2026-04-13 09:27:19.239 | INFO | CORS缓存已更新: 2 个源
2026-04-13 09:27:21.285 | INFO | HMAC 密钥已加载: 2 个
```

### 查看 Redis 数据

```bash
# 连接 Redis
redis-cli -a 123123

# 查看 HMAC 密钥
KEYS hmac:*

# 查看限流数据
KEYS rate_limit:*

# 查看 CORS 配置
GET cors:config
```

### 查看 Consul 服务

```bash
# 查看所有服务
curl http://localhost:8500/v1/catalog/services

# 查看特定服务
curl http://localhost:8500/v1/catalog/service/user-service

# 查看服务健康状态
curl http://localhost:8500/v1/health/service/user-service
```

---

## ⚠️ 常见问题

### Q1: 测试返回 401 Unauthorized

**原因**: HMAC 签名错误

**解决**:
1. 检查 `HMAC_SECRET_KEY` 是否正确
2. 检查签名生成逻辑
3. 检查时间戳是否在容忍范围内（默认 300 秒）

### Q2: 测试返回 503 Service Unavailable

**原因**: 后端服务未启动或未注册

**解决**:
1. 确认 User Service 正在运行
2. 检查 Consul 中是否有服务注册
3. 查看 Gateway 日志中的错误信息

### Q3: 限流测试没有触发 429

**原因**: 未达到限流阈值

**解决**:
1. 增加请求数量（>100）
2. 降低限流配置（修改 `.env` 中的 `RATE_LIMIT_MAX_REQUESTS`）
3. 确保请求来自同一 IP

### Q4: 服务注册失败

**原因**: Consul 未启动或网络问题

**解决**:
1. 确认 Consul 正在运行
2. 检查 Consul 地址配置（`.env` 中的 `CONSUL_HOST`）
3. 查看 Consul 日志

---

## 📈 性能测试

### 使用 ab (Apache Bench)

```bash
# 测试 Gateway 吞吐量
ab -n 1000 -c 10 http://localhost:9000/health

# 带 HMAC 签名的测试
ab -n 1000 -c 10 \
   -H "X-App-ID: user-service" \
   -H "X-Timestamp: $(date +%s)" \
   -H "X-Nonce: abc123" \
   -H "X-Signature: xxx" \
   http://localhost:9000/user/api/users
```

### 使用 wrk

```bash
wrk -t12 -c400 -d30s http://localhost:9000/health
```

---

## 🎯 测试检查清单

完成以下检查，确认 Gateway 功能完整：

- [ ] Gateway 启动成功
- [ ] Redis 连接正常
- [ ] Consul 连接正常
- [ ] User Service 注册成功
- [ ] HMAC 签名验证通过
- [ ] 请求转发到后端
- [ ] CORS 配置正确
- [ ] 限流功能工作
- [ ] 熔断器保护生效
- [ ] 并发请求处理正常
- [ ] 服务注销正常

---

## 📚 相关文档

- [Gateway 工程提示词](docs/工程提示词.md)
- [功能模块说明](docs/功能模块说明.md)
- [HTTPS 配置指南](docs/HTTPS配置指南.md)

---

## 💡 下一步

测试通过后，可以：

1. **部署到生产环境**
   - 启用 HTTPS
   - 配置强密码
   - 调整限流阈值

2. **添加更多后端服务**
   - 复制 `test_user_service.py`
   - 修改服务名称和端口
   - 注册到 Consul

3. **监控和告警**
   - 集成 Prometheus
   - 配置 Grafana 仪表板
   - 设置告警规则

4. **性能优化**
   - 调整连接池大小
   - 优化超时配置
   - 启用 HTTP/2

---

**祝测试顺利！** 🎉
