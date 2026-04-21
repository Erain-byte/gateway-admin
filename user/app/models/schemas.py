"""
数据库模型
"""
from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field


class User(SQLModel, table=True):
    """用户表"""
    __tablename__ = "users"  # type: ignore
    
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(max_length=50, unique=True, index=True)
    password_hash: str = Field(max_length=255)
    nickname: Optional[str] = Field(default=None, max_length=50)
    email: Optional[str] = Field(default=None, max_length=100)
    phone: Optional[str] = Field(default=None, max_length=20)
    avatar: Optional[str] = Field(default=None, max_length=255)
    status: int = Field(default=1)  # 1: 正常, 0: 禁用
    last_login_time: Optional[datetime] = None
    last_login_ip: Optional[str] = Field(default=None, max_length=50)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class UserProfile(SQLModel, table=True):
    """用户扩展信息表"""
    __tablename__ = "user_profiles"  # type: ignore
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", unique=True, index=True)
    gender: Optional[int] = Field(default=None)  # 0: 未知, 1: 男, 2: 女
    birthday: Optional[datetime] = None
    address: Optional[str] = Field(default=None, max_length=255)
    bio: Optional[str] = Field(default=None, max_length=500)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class UserToken(SQLModel, table=True):
    """用户 Token 表"""
    __tablename__ = "user_tokens"  # type: ignore
    
    id: Optional[int] = Field(default=None, primary_key=True)
    token: str = Field(max_length=64, unique=True, index=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    device: Optional[str] = Field(default=None, max_length=50)
    ip: Optional[str] = Field(default=None, max_length=50)
    expires_at: datetime
    created_at: datetime = Field(default_factory=datetime.now)
