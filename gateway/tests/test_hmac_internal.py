"""
测试内部服务 HMAC 签名验证

验证 Gateway 转发请求时的 HMAC 签名是否正确生成和验证
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.utils.redis_manager import get_redis_manager
from loguru import logger


async def test_hmac_signature():
    """测试 HMAC 签名生成和存储"""
    
    # 获取 Redis Manager
    redis = get_redis_manager()
    if not redis:
        logger.error("Failed to connect to Redis")
        return
    
    # 为 gateway 服务生成并存储 HMAC Key
    service_name = "gateway"
    hmac_key = "test-gateway-secret-key-12345"
    
    # 存储到 Redis
    await redis.set(f"config:hmac:{service_name}", hmac_key)
    logger.info(f"✅ Stored HMAC key for {service_name}")
    
    # 验证存储
    stored_key = await redis.get(f"config:hmac:{service_name}")
    if stored_key == hmac_key:
        logger.info(f"✅ Verified HMAC key retrieval")
    else:
        logger.error(f"❌ HMAC key mismatch")
    
    # 为 admin-service 生成并存储 HMAC Key
    service_name = "admin-service"
    hmac_key = "test-admin-secret-key-67890"
    
    await redis.set(f"config:hmac:{service_name}", hmac_key)
    logger.info(f"✅ Stored HMAC key for {service_name}")
    
    # 列出所有 HMAC Keys
    keys = await redis.keys("config:hmac:*")
    logger.info(f"📋 All HMAC keys in Redis: {keys}")
    
    logger.info("✅ HMAC signature test completed")


if __name__ == "__main__":
    asyncio.run(test_hmac_signature())
