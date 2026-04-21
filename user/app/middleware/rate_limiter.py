"""
限流中间件

基于滑动窗口算法的 Redis 限流实现
支持降级策略：Redis 不可用时自动放行
"""
import time
from typing import Callable, Optional
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from loguru import logger