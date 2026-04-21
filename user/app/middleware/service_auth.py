"""
服务来源认证中间件

只允许以下来源访问 user 服务：
1. Gateway（通过 X-Forwarded-By Header + HMAC 签名标识）
2. 已在 Redis 中注册的内部服务（通过 X-Service-Name + HMAC 签名）

安全机制：
- 所有内部请求必须携带 HMAC 签名
- 签名密钥从配置读取（统一使用 config:hmac:gateway）
- 防止 Header 伪造和重放攻击
- 用户信息从 Header 读取（X-User-ID, X-User-Role）
"""
from typing import Optional, Set, List
import time
import hmac
import hashlib
from fastapi import Request
from sqlmodel import true
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from loguru import logger
from config.settings import settings
from utils.redis_pool import get_redis_pool
from app.utils.cache_manager import cache_manager
from app.utils.path_matcher import parse_public_paths, is_public_path


class ServiceAuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        redis = get_redis_pool()
        self.redis_instance = redis.get_instance() # Redis 实例，用于后续的 Redis 操作
        self.cache = cache_manager # 缓存管理器，用于后续的缓存操作
        #获取公开的路径
        self.public_paths = parse_public_paths(settings.PUBLIC_PATHS) # 获取公开的路径
        logger.info(f"Public paths loaded: {self.public_paths}")
        self.gateway_app_id = settings.GATEWAY_APP_ID # Gateway 的应用 ID
         # 缓存已注册的服务列表（性能优化）
        self._registered_services_cache: Set[str] = set()#缓存已注册的服务列表（性能优化）
        self._cache_ttl = 60  # 缓存 60 秒
        self._last_update = 0

    async def dispatch(self, request: Request, call_next):

        if is_public_path(request.path, self.public_paths):
            return await call_next(request) # 公开路径，直接访问
        # 获取请求来源信息
        client_host = request.client.host if request.client else None
        service_name_header=request.headers.get("X-Service-Name")
        forwarded_by = request.headers.get("X-Forwarded-By")

        if forwarded_by == "gateway":
            # Gateway 请求：使用统一密钥验证
            if await self._verify_hmac_signature(request):
               is_from_gateway = True
               logger.debug(f"Gateway access verified with valid signature")
                # 提取用户信息并添加到 request.state
               user_id = request.headers.get("X-User-ID") # 用户 ID
               user_role = request.headers.get("X-User-Role") # 用户角色
               user_permissions = request.headers.get("X-User-Permissions", "") # 用户权限
               if user_id:
                  request.state.user_id = int(user_id) # 用户 ID
                  request.state.user_role = user_role # 用户角色
                  request.state.user_permissions = [p.strip() for p in user_permissions.split(",") if p.strip()] if user_permissions else []
                  logger.debug(f"User info added to request state: user_id={user_id}, user_role={user_role}, user_permissions={user_permissions}")

            else:
               logger.warning(f"Invalid HMAC signature for gateway request from {client_host}")
               return JSONResponse(
                   status_code=403,
                   content={
                        "code": 403,
                        "message": "Forbidden: Invalid Gateway signature",
                        "data": None
                   }
               )

        elif service_name_header:
             # 内部服务请求：验证服务注册状态 + HMAC 签名
            if await self._is_from_registered_service(service_name_header, client_host): # 验证服务注册状态
                if await self._verify_hmac_signature(request, service_name_header): # 验证 HMAC 签名
                    is_from_registered_service = True # 内部服务请求验证成功
                    logger.debug(f"✅ Service '{service_name_header}' access verified with valid signature")
                else:
                   logger.warning(f"Invalid HMAC signature for registered service '{service_name_header}' from {client_host}")
                   return JSONResponse(
                       status_code=403,
                       content={
                            "code": 403,
                            "message": "Forbidden: Invalid service signature",
                            "data": None
                       }
                   )
            else:
               logger.warning(f"Service '{service_name_header}' not found for request from {client_host}")
               return JSONResponse(
                   status_code=403,
                   content={
                        "code": 403,
                        "message": "Forbidden: Service not found",
                        "data": None
                   }
               )
          # 最终安全检查：确保请求来自 Gateway 或已注册的服务
        if not (is_from_gateway or is_from_registered_service):
           logger.warning(f"Unauthorized access attempt from {client_host}")
           return JSONResponse(
               status_code=403,
               content={
                    "code": 403,
                    "message": "Forbidden: Unauthorized access",
                    "data": None
               }
           )
        # 记录请求来源
        if is_from_gateway:
            request.state.caller_source = "gateway" # 请求来源：Gateway
            request.state.caller_service = "gateway" # 请求来源：Gateway
            logger.debug(f"✅ Access allowed from Gateway to {request.url.path}")
        elif is_from_registered_service:
            request.state.caller_source = "internal_service"#   请求来源：内部服务
            request.state.caller_service = service_name_header # 请求来源：内部服务
            logger.debug(f"✅ Access allowed from {service_name_header} to {request.url.path}")

        return await call_next(request)

    def _is_public_endpoint(self, path: str) -> bool: # 判断是否是公开端点（不需要来源验证）

         return is_public_path(path, self.public_patterns)

    async def _verify_hmac_signature(self,request:Request)->bool:
        """
        验证 HMAC 签名

        Args:
            request: 请求对象

        Returns:
            bool: 是否验证通过
        """
         # 获取签名相关 Header
        signature = request.headers.get("X-Signature")# 签名
        timestamp = request.headers.get("X-Timestamp")# 时间戳
        #nonce = request.headers.get("X-Nonce")# 随机数
        if not all([signature, timestamp]):
            return False
        # 验证时间戳（防止重放攻击，5分钟有效期）
        try:
            timestamp = int(timestamp)
            if abs(time.time() - timestamp) > 300:
                return False
        except ValueError:
            logger.warning(f"Invalid timestamp format")
            return False
         # 使用统一的 Gateway HMAC 密钥（从 Redis 获取）
        hmac_key = await self.redis_instance.get(f"config:hmac:{self.gateway_app_id}") or self.cache.get(f"config:hmac:{self.gateway_app_id}")
        if not hmac_key:
            logger.warning(f"HMAC key not found for app ID: {self.gateway_app_id}")
            return False
        # 构建签名字符串（按顺序）
        method = request.method
        path = request.url.path
        message = f"{method}:{path}:{timestamp}"
         # 计算期望的签名
        expected_signature = hmac.new(
            hmac_key.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        # 比较签名（防止时序攻击）
        is_valid = hmac.compare_digest(signature, expected_signature)
        
        if not is_valid:
            logger.warning(f"Invalid signature from {service_name}")
        
        return is_valid

    async def _get_hmac_key(self, app_id: str, service_name: str) -> Optional[str]:
            pass
    async def _is_from_registered_service(
        self, 
        service_name: Optional[str], 
        client_host: Optional[str]
    )->bool:
        """验证服务是否已注册"""
        if not service_name:
            return False
         # 从缓存或注册中心获取已注册的服务列表
        registered_services = await self._get_registered_services(service_name)
        if not registered_services:
            logger.warning(f"No registered services found")
            return False
        # 检查服务名是否在注册列表中
        if service_name in registered_services:
            logger.debug(f"Service '{service_name}' is registered")
            return True
        else:
            logger.warning(f"Service '{service_name}' not found in registered services")
            return False
    async def _get_registered_services(self) -> Set[str]:
        """获取已注册的服务列表"""
        now = time.time()
        # 缓存未过期，直接返回
        if now - self._last_update < self._cache_ttl:
            return self._registered_services_cache
        
        # 从 Redis 获取（主要来源）
        service_names = set()
        if self.redis_instance is not None:
            try:
                keys = await self.redis_instance.keys("service:*:*")
                for key in keys:
                    if isinstance(key, bytes):
                        key = key.decode()
                    parts = key.split(":")
                    if len(parts) > 2:
                        service_name = parts[1]
                        # 排除自身
                        if service_name != settings.SERVICE_NAME:
                            service_names.add(service_name)
                logger.debug(f"Registered services from Redis: {service_names}")
            except Exception as e:
                logger.error(f"Error fetching registered services from Redis: {e}")
        
        # 更新缓存
        self._registered_services_cache = service_names
        self._last_update = now
        
        return service_names


    async def _verify_service_ip(self, service_name: str, client_host: str) -> bool:
        """验证服务的 IP 地址是否匹配注册信息
        Args:
            service_name: 服务名称
            client_host: 客户端 IP
        Returns:
            IP 是否匹配"""
        if self.redis_instance is not None:
            return True
        try:
           # 获取该服务的所有注册实例
            pattern = f"service:{service_name}:*"
            keys = await self.redis_instance.keys(pattern)
            for key in keys:
                instance_data = await self.redis.hgetall(key)
                if instance_data:
                    registered_ip = instance_data.get("ip")
                    if isinstance(registered_ip, bytes):
                        registered_ip = registered_ip.decode('utf-8')
                    
                    if registered_ip == client_host:
                        logger.debug(f"✅ IP verified: {client_host}")
                        return True
            
            logger.warning(f"IP verification failed for {service_name}: {client_host}")
            return False
        except Exception as e:
                logger.error(f"Error fetching service IP from Redis: {e}")
                return True  # 出错时不阻止请求（降级策略）
        
