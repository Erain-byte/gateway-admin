# Token + HMAC 混合认证架构改造方案

## 一、架构概述

### 当前问题
- 前端/移动端需要配置 HMAC 密钥，存在安全风险（密钥暴露）
- 白名单配置复杂，维护成本高

### 目标架构
```
客户端 (Token)
  ↓
Gateway (验证 Token + 生成 HMAC)
  ↓ X-User-ID, X-User-Role + HMAC 签名
内部服务 (读取用户信息 + 验证 HMAC + 权限检查)
```

**核心原则**：
- **Token**：用于客户端认证（前端/移动端），存储在 Redis/MySQL
- **HMAC**：用于服务间通信保护（Gateway ↔ 内部服务）

---

## 二、需要修改的部分

### 1. Gateway 层

#### 1.1 新增 Token 验证中间件
**文件**：`gateway/app/middleware/token_auth.py`（新建）

**功能**：
- 从请求头 `Authorization: Bearer <token>` 提取 Token
- 查询 Redis/数据库验证 Token 有效性
- 提取用户信息（user_id, role, permissions）
- 将用户信息添加到请求头：
  - `X-User-ID`: 用户ID
  - `X-User-Role`: 用户角色
  - `X-User-Permissions`: 用户权限列表（可选）

**豁免路径**：
- `/api/auth/*`（登录、注册等）
- `/api/captcha/*`（验证码）
- `/healthz`（健康检查）

#### 1.2 修改路由转发逻辑
**文件**：`gateway/app/services/router.py`

**修改点**：
- 保留现有的 HMAC 签名生成逻辑
- 确保 Token 用户信息透传到内部服务
- 清除前端的 `Authorization` header（避免泄露）

#### 1.3 使用统一的 HMAC 密钥
**采用选项 A**：所有内部服务使用同一个 HMAC 密钥
- 统一密钥：`config:hmac:gateway`
- Gateway 转发到任何服务都使用这个密钥签名
- 内部服务都用这个密钥验证签名
- **优势**：配置简单，易于维护，适合中小规模系统

---

### 2. Admin 服务层

#### 2.1 移除 Token 验证中间件
**文件**：`admin/app/middleware/service_auth.py`

**修改点**：
- 移除当前的 Token 验证逻辑（从数据库/Redis 查询）
- 改为从 Header 读取 Gateway 传递的用户信息：
  - `X-User-ID`
  - `X-User-Role`
  - `X-User-Permissions`

#### 2.2 保留权限检查逻辑
**文件**：`admin/app/middleware/permission_check.py`（可能需要新建或修改现有逻辑）

**功能**：
- 根据 `X-User-Role` 和 `X-User-Permissions` 进行权限验证
- 结合路由路径判断是否有访问权限

#### 2.3 使用统一的 HMAC 密钥验证
- 所有内部服务使用 `config:hmac:gateway` 验证签名
- 不再需要 `X-Forwarded-By` 来判断使用哪个密钥
- 简化验证逻辑

---

### 3. 前端/移动端

#### 3.1 移除 HMAC 签名逻辑
**文件**：`frontend/admin-ui/src/api/request.ts`

**修改点**：
- 移除 HMAC 签名生成代码
- 移除 `.env` 中的 `VITE_GATEWAY_HMAC_KEY`
- 保留 Token 存储和传递逻辑

#### 3.2 登录流程不变
- 登录成功后保存 Token
- 所有请求携带 `Authorization: Bearer <token>`

---

### 4. 配置文件修改

#### 4.1 Gateway `.env`
```bash
# HMAC 配置（统一密钥）
HMAC_SECRET_KEY=your-hmac-secret-key-here
```

**说明**：
- Gateway 启动时会检查 Redis 中是否有 `config:hmac:gateway`
- 如果没有，会从 `.env` 读取 `HMAC_SECRET_KEY` 并写入 Redis
- 所有内部服务都使用这个密钥

#### 4.2 Admin `.env`
```bash
# Token 配置（用于生成 Token）
TOKEN_SECRET_KEY=your-token-secret-key-here

# HMAC 配置（统一密钥）
GATEWAY_HMAC_KEY=your-hmac-secret-key-here
```

**说明**：
- Admin 从 Redis 读取 `config:hmac:gateway` 验证签名
- `GATEWAY_HMAC_KEY` 作为初始值，会同步到 Redis

#### 4.3 前端 `.env`
```bash
VITE_API_BASE_URL=http://localhost:9000
# 移除 VITE_GATEWAY_HMAC_KEY
```

---

### 5. 数据库/Redis 清理

#### 5.1 删除各服务的独立 HMAC 密钥
```python
# 清理旧的独立密钥
redis.delete('config:hmac:admin-service')
redis.delete('config:hmac:user-service')
# 只保留统一密钥
redis.set('config:hmac:gateway', 'unified-key')
```

---

## 三、实施步骤

### Phase 1: Gateway 改造
1. ✅ 创建 Token 验证中间件
2. ✅ 连接 Redis/数据库验证 Token
3. ✅ 测试 Token 验证功能
4. ✅ 修改路由转发逻辑，透传用户信息

### Phase 2: Admin 改造
1. ✅ 移除 Token 验证中间件
2. ✅ 改为读取 Gateway 传递的用户信息
3. ✅ 测试权限检查逻辑
4. ✅ 使用统一 HMAC 密钥验证签名

### Phase 3: 前端/移动端适配
1. ✅ 移除 HMAC 密钥配置
2. ✅ 移除签名生成逻辑
3. ✅ 保留 Token 存储和传递
4. ✅ 测试登录和接口调用

### Phase 4: 清理和优化
1. ✅ 删除不需要的 HMAC 密钥
2. ✅ 更新文档
3. ✅ 性能测试

---

## 四、优势对比

### 改造前
- ❌ 前端/移动端需要配置 HMAC 密钥（安全风险）
- ❌ 白名单配置复杂
- ❌ 密钥管理混乱

### 改造后
- ✅ 前端/移动端只需处理 Token（标准做法）
- ✅ 无需白名单配置
- ✅ HMAC 只用于服务间通信（更安全）
- ✅ 架构清晰，职责分明

---

## 五、注意事项

### 5.1 Token 撤销机制

**优势**：Token 存储在 Redis/数据库，可以直接删除实现撤销

**登出接口（Admin）**：
```python
# admin/app/api/auth.py
@router.post("/api/auth/logout")
async def logout(request: Request):
    from app.services.token_service import TokenService
    
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=400, detail="Missing token")
    
    token = auth_header.split(" ")[1]
    
    # 删除 Token（立即失效）
    await TokenService.delete_token(token)
    
    return {"message": "Logged out successfully"}
```

**修改密码时撤销所有 Token**：
```python
# 删除用户所有 Token
await TokenService.delete_all_user_tokens(user_id)
```

### 5.2 其他注意事项

1. **Token 查询性能**：每次请求都要查 Redis，但 Redis 性能足够
2. **密钥安全**：`HMAC_SECRET_KEY` 需要妥善保管
3. **向后兼容**：改造期间需要考虑旧版本的兼容性
4. **HTTPS**：生产环境必须使用 HTTPS，防止 Token 被窃取

---

## 六、参考实现

### JWT 中间件示例
```python
# gateway/app/middleware/jwt_auth.py
import jwt
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

class JWTAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 检查是否在豁免路径
        if self._is_exempt(request.url.path):
            return await call_next(request)
        
        # 提取 Token
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Missing token")
        
        token = auth_header.split(" ")[1]
        
        # 验证 Token
        try:
            payload = jwt.decode(
                token, 
                settings.JWT_SECRET_KEY, 
                algorithms=[settings.JWT_ALGORITHM]
            )
            
            # 添加用户信息到请求头
            request.state.user_id = payload.get("user_id")
            request.state.user_role = payload.get("role")
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        return await call_next(request)
    
    def _is_exempt(self, path: str) -> bool:
        exempt_paths = ["/api/auth/", "/api/captcha/", "/healthz"]
        return any(path.startswith(p) for p in exempt_paths)
```

### Admin 读取用户信息示例
```python
# admin/app/middleware/service_auth.py
async def get_current_user(request: Request):
    user_id = request.headers.get("X-User-ID")
    user_role = request.headers.get("X-User-Role")
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Missing user info")
    
    return {
        "user_id": int(user_id),
        "role": user_role
    }
```
