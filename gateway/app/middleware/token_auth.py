"""
Token 验证中间件

验证客户端传来的 Token，提取用户信息并添加到请求头
"""

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from loguru import logger

from config.settings import settings
from app.services.discovery import ServiceDiscovery


class TokenAuthMiddleware(BaseHTTPMiddleware):
    """Token 验证中间件"""
    
    def __init__(self, app):
        super().__init__(app)
        self._system_whitelist = None  # 缓存系统白名单
    
    async def _get_system_whitelist(self) -> list:
        """从 Redis 获取系统级白名单（带缓存）"""
        if self._system_whitelist is not None:
            return self._system_whitelist
        
        try:
            from app.utils.redis_manager import get_redis_manager
            redis = get_redis_manager()
            
            whitelist_data = await redis.get("config:gateway:system_whitelist")
            
            if whitelist_data:
                import json
                self._system_whitelist = json.loads(whitelist_data)
            else:
                # 如果 Redis 中没有，使用空列表（不应该发生）
                logger.warning("System whitelist not found in Redis")
                self._system_whitelist = []
        except Exception as e:
            logger.error(f"Failed to load system whitelist: {e}")
            self._system_whitelist = []
        
        return self._system_whitelist
    
    async def dispatch(self, request: Request, call_next):
        # 允许 OPTIONS 请求（CORS 预检）
        if request.method == "OPTIONS":
            return await call_next(request)
        
        # 检查是否在豁免路径
        if await self._is_exempt(request.url.path):
            return await call_next(request)
        
        # 提取 Token
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            logger.warning(f"Missing token: {request.url.path}, headers: {dict(request.headers)}")
            raise HTTPException(status_code=401, detail="Missing authentication token")
        
        token = auth_header.split(" ")[1]
        
        # 验证 Token（查询 Redis/数据库）
        try:
            user_info = await self._verify_token(token)
            
            if not user_info:
                logger.warning(f"Invalid token: {token[:20]}...")
                raise HTTPException(status_code=401, detail="Invalid or expired token")
            
            # 添加用户信息到请求 state（供后续使用）
            request.state.user_id = user_info.get("user_id")
            request.state.user_role = user_info.get("role")
            request.state.user_permissions = user_info.get("permissions", [])
            
            logger.debug(f"Token verified for user: {user_info.get('user_id')}")
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Token verification error: {e}")
            raise HTTPException(status_code=500, detail="Token verification failed")
        
        return await call_next(request)
    
    async def _verify_token(self, token: str) -> dict | None:
        """
        验证 Token 有效性
        
        Args:
            token: Token 字符串
            
        Returns:
            用户信息字典，如果 Token 无效返回 None
        """
        try:
            from app.utils.redis_manager import get_redis_manager
            redis = get_redis_manager()
            
            # 从 Redis 查询 Token
            token_key = f"token:{token}"
            token_data = await redis.get(token_key)
            
            if not token_data:
                return None
            
            # 解析 Token 数据（JSON 格式）
            import json
            user_info = json.loads(token_data)
            
            return user_info
            
        except Exception as e:
            logger.error(f"Failed to verify token: {e}")
            return None
    
    async def _is_exempt(self, path: str) -> bool:
        """
        检查路径是否在豁免列表中（公开接口，不需要 Token）
        
        Args:
            path: 请求路径
            
        Returns:
            是否豁免
        """
        # 1. 获取系统级白名单（从 Redis）
        system_whitelist = await self._get_system_whitelist()
        if any(path.startswith(p) for p in system_whitelist):
            return True
        
        # 2. 去掉服务名前缀，获取实际路径
        parts = path.strip("/").split("/", 1)
        if len(parts) < 2:
            return False
        
        actual_path = "/" + parts[1]  # 例如：/admin-service/api/auth/login -> /api/auth/login
        
        # 3. 检查所有已注册服务的白名单
        try:
            from app.utils.redis_manager import get_redis_manager
            redis = get_redis_manager()
            
            # 从 Redis 获取所有服务实例
            service_keys = await redis.keys("service:*")
            
            for key in service_keys:
                service_data = await redis.get(key)
                if service_data:
                    import json
                    service = json.loads(service_data)
                    # 从 metadata 中获取白名单
                    whitelist = service.get("metadata", {}).get("global_whitelist", [])
                    if isinstance(whitelist, list):
                        for pattern in whitelist:
                            # 支持通配符匹配
                            if pattern.endswith("/*"):
                                prefix = pattern[:-1]  # /api/auth/* -> /api/auth/
                                if actual_path.startswith(prefix):
                                    return True
                            elif actual_path == pattern:
                                return True
        except Exception as e:
            logger.error(f"Failed to check service whitelist: {e}")
        
        return False
