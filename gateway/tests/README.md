# Gateway 测试目录结构

## 📁 目录组织

```
tests/
├── __init__.py
├── conftest.py              # Pytest 配置和 fixtures
├── unit/                    # 单元测试
│   ├── __init__.py
│   ├── test_circuit_breaker.py
│   ├── test_config.py
│   ├── test_cors.py
│   ├── test_hmac.py
│   ├── test_load_balancer.py
│   ├── test_models.py
│   └── test_rate_limiter.py
├── integration/             # 集成测试
│   └── __init__.py
├── test_user_service.py     # 模拟后端服务
├── test_frontend_simulation.py  # 前端模拟测试
├── test_gateway_features.py     # Gateway 功能测试
├── test_gateway_simple.py       # Gateway 简单测试
├── test_integration_auto.py     # 自动化集成测试
├── test_cache_fallback.py       # 缓存降级测试
└── 其他测试文件...
```

---

## 🧪 测试分类

### 1. 单元测试 (unit/)

测试独立的组件和功能：
- 熔断器
- 配置管理
- CORS
- HMAC 验证
- 负载均衡
- 数据模型
- 限流器

**运行方式**:
```bash
pytest tests/unit/ -v
```

### 2. 集成测试 (integration/)

测试多个组件的交互：
- 完整的请求流程
- 服务间通信
- 数据库操作

**运行方式**:
```bash
pytest tests/integration/ -v
```

### 3. 功能测试 (根目录)

测试完整的业务场景：
- `test_user_service.py` - 模拟后端服务
- `test_frontend_simulation.py` - 前端模拟
- `test_gateway_features.py` - Gateway 完整功能
- `test_gateway_simple.py` - Gateway 核心功能
- `test_integration_auto.py` - 自动化测试
- `test_cache_fallback.py` - 缓存降级测试

---

## 🚀 运行测试

### 运行所有测试

```bash
cd d:\python_project\gateway
pytest tests/ -v
```

### 运行特定测试文件

```bash
# 运行前端模拟测试
pytest tests/test_frontend_simulation.py -v

# 运行缓存测试
pytest tests/test_cache_fallback.py -v
```

### 运行单元测试

```bash
pytest tests/unit/ -v
```

### 运行集成测试

```bash
pytest tests/integration/ -v
```

### 带覆盖率报告

```bash
pytest tests/ --cov=app --cov-report=html
```

---

## 📝 测试文件说明

### test_user_service.py
**用途**: 模拟一个真实的后端微服务
**功能**:
- 启动 FastAPI 服务（端口 8001）
- 自动注册到 Consul
- 提供用户管理 API
- 健康检查端点

**运行**:
```bash
python tests/test_user_service.py
```

### test_frontend_simulation.py
**用途**: 模拟前端应用通过 Gateway 访问后端
**测试内容**:
- 服务注册验证
- HMAC 签名认证
- 请求转发
- 负载均衡
- 限流功能
- 熔断器
- 并发请求

**运行**:
```bash
python tests/test_frontend_simulation.py
```

### test_gateway_simple.py
**用途**: Gateway 核心功能测试
**测试内容**:
- 健康检查
- CORS 配置
- HMAC 密钥管理
- 服务发现
- 限流机制

**运行**:
```bash
python tests/test_gateway_simple.py
```

### test_integration_auto.py
**用途**: 自动化集成测试
**功能**:
- 自动检查依赖服务
- 自动启动 User Service
- 运行完整测试
- 自动清理资源

**运行**:
```bash
python tests/test_integration_auto.py
```

### test_cache_fallback.py
**用途**: 测试降级缓存功能
**测试内容**:
- 缓存目录位置
- 缓存保存和加载
- 降级策略

**运行**:
```bash
python tests/test_cache_fallback.py
```

---

## ⚙️ Pytest 配置

配置文件: `pytest.ini`

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short
```

---

## 🔧 Fixtures (conftest.py)

常用的测试 fixtures:

```python
import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
def client():
    """创建测试客户端"""
    return TestClient(app)

@pytest.fixture
def sample_user():
    """示例用户数据"""
    return {
        "id": 1,
        "name": "张三",
        "email": "zhangsan@example.com"
    }
```

---

## 📊 测试最佳实践

### 1. 命名规范

- 测试文件: `test_<module>.py`
- 测试类: `Test<Class>`
- 测试函数: `test_<functionality>`

**示例**:
```python
# tests/unit/test_hmac.py
class TestHMACValidator:
    def test_valid_signature(self):
        """测试有效的签名"""
        pass
    
    def test_invalid_signature(self):
        """测试无效的签名"""
        pass
```

### 2. 使用 Fixtures

避免重复代码，使用 fixtures 提供测试数据：

```python
@pytest.fixture
def hmac_headers():
    """生成 HMAC 头部"""
    return generate_hmac_signature("test-app", "secret-key")

def test_hmac_validation(client, hmac_headers):
    response = client.get("/api/test", headers=hmac_headers)
    assert response.status_code == 200
```

### 3. 隔离测试

每个测试应该独立，不依赖其他测试的状态：

```python
# ✅ 好的做法
def test_create_user(client):
    response = client.post("/users", json={"name": "Test"})
    assert response.status_code == 201

def test_get_user(client):
    # 不依赖 test_create_user
    response = client.get("/users/1")
    assert response.status_code == 200

# ❌ 不好的做法
def test_get_user_created_in_previous_test(client):
    # 依赖之前的测试创建了用户
    response = client.get("/users/1")
    assert response.status_code == 200
```

### 4. 清理资源

测试完成后清理资源：

```python
def test_with_cleanup(client):
    try:
        # 执行测试
        response = client.post("/users", json={"name": "Test"})
        assert response.status_code == 201
    finally:
        # 清理
        client.delete("/users/1")
```

---

## ⚠️ 注意事项

### 1. 不要使用已废弃的函数

**❌ 避免**:
```python
@app.on_event("startup")
async def startup():
    pass

@app.on_event("shutdown")
async def shutdown():
    pass
```

**✅ 使用**:
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时
    yield
    # 关闭时
```

### 2. 测试文件位置

所有测试文件必须在 `tests/` 目录下，不要在项目根目录。

### 3. 环境变量

测试时使用 `.env.test` 或设置测试专用的环境变量。

### 4. 数据库隔离

使用测试数据库，不要污染开发或生产数据库。

---

## 🔍 常见问题

### Q: 如何调试测试？

```bash
# 使用 pdb
pytest tests/test_example.py --pdb

# 打印输出
pytest tests/test_example.py -s

# 只运行失败的测试
pytest tests/ --lf
```

### Q: 如何跳过测试？

```python
import pytest

@pytest.mark.skip(reason="暂未实现")
def test_future_feature():
    pass

@pytest.mark.skipif(sys.version_info < (3, 10), reason="需要 Python 3.10+")
def test_python310_feature():
    pass
```

### Q: 如何参数化测试？

```python
@pytest.mark.parametrize("input,expected", [
    (1, 2),
    (2, 4),
    (3, 6),
])
def test_double(input, expected):
    assert input * 2 == expected
```

---

## 📚 相关文档

- [Gateway 测试指南](../TESTING.md)
- [测试说明](../测试说明.md)
- [Pytest 文档](https://docs.pytest.org/)

---

**保持测试文件在 tests 目录，使用最新的 API！** ✅
