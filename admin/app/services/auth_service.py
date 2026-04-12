"""
认证服务
"""
from datetime import datetime
from typing import Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.schemas import Admin
from app.services.password_service import password_service
from app.services.token_service import token_service


class AuthService:
    
    @staticmethod
    async def login(
        username: str,
        password: str,
        session: AsyncSession,
        device: Optional[str] = None,
        ip: Optional[str] = None
    ) -> Tuple[bool, str, Optional[dict]]:
        """
        登录（异步）
        Returns: (是否成功, 错误信息/Token, 用户信息)
        """
        stmt = select(Admin).where(Admin.username == username)
        result = await session.execute(stmt)
        admin = result.scalar_one_or_none()
        
        if not admin:
            return False, "用户名或密码错误", None
        
        if admin.status != 1:
            return False, "账号已被禁用", None
        
        if not password_service.verify(password, admin.password_hash):
            return False, "用户名或密码错误", None
        
        # 更新登录信息
        admin.last_login_time = datetime.now()
        admin.last_login_ip = ip
        session.add(admin)
        await session.commit()
        
        # 创建 Token（异步）
        token = await token_service.create_token(admin, device, ip)
        
        return True, token, {
            "id": admin.id,
            "username": admin.username,
            "nickname": admin.nickname
        }
    
    @staticmethod
    async def verify_token(token: str) -> Optional[dict]:
        """验证 Token（异步）"""
        return await token_service.verify_token(token)
    
    @staticmethod
    async def logout(token: str) -> bool:
        """登出（异步）"""
        return await token_service.delete_token(token)


auth_service = AuthService()
