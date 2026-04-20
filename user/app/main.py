###
# 用户服务
##
from fastapi import FastAPI, Response
from config.settings import settings, BASE_DIR
from contextlib import asynccontextmanager
from fastapi.responses import JSONResponse
from loguru import logger
from app.utils.redis_pool import get_redis_pool
from app.utils.datbase_pool import db_manager
from app.utils.httpx_pool import httpx_pool 
from app.services.register_service import register_service
#redis_pool = RedisPool()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    logger.info("User service starting...")
    
    # 初始化数据库
    try:
        db_manager.init()
        logger.info("Database initialized")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
    
    # 预检查 Redis 连接
    redis_pool = get_redis_pool()
    try:
        redis = redis_pool.get_instance()
        await redis.ping()
        logger.info("Redis connected successfully")
    except Exception as e:
        logger.warning(f"Redis connection failed: {e}")

    # 初始化 HTTPX
    try:
        await httpx_pool.init()
        logger.info("Httpx initialized")
    except Exception as e:
        logger.warning(f"Httpx initialization failed: {e}")   

    #注册到Gateway
    try:
        await register_service.register()
        logger.info("Registered to Gateway")
    except Exception as e:
        logger.error(f"Failed to register to Gateway: {e}")
    yield
    
    # 关闭时
    logger.info("User service shutting down...")
    
    # 注销服务（需要在关闭 HTTPX 之前）
    try:
        await register_service.unregister()
        logger.info("Unregistered from Gateway")
    except Exception as e:
        logger.error(f"Failed to unregister from Gateway: {e}")
    
    # 关闭数据库
    try:
        db_manager.close_all()
        await db_manager.close_all_async()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Failed to close database: {e}")
    
    # 关闭 Redis
    try:
        await redis_pool.close()
        logger.info("Redis connection closed")
    except Exception as e:
        logger.error(f"Failed to close Redis: {e}")
    # 关闭 HTTPX
    try:
        await httpx_pool.close()
        logger.info("Httpx closed")
    except Exception as e:
        logger.error(f"Failed to close Httpx: {e}")

app = FastAPI(
    title=settings.APP_NAME,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION,
    lifespan=lifespan
)


@app.get("/healthz")
async def health_check():
    """健康检查端点"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
          "app.main:app",
            host=settings.HOST,
            port=settings.PORT,
            reload=settings.is_debug,
    )
    # log.info(f"{settings.APP_NAME} started at {settings.HOST}:{settings.PORT}")


