# -*- coding: utf-8 -*-
"""
数据库初始化脚本
运行: python init_db.py
"""
import sys
import os
import asyncio

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.utils.datbase_pool import db_manager


async def create_db_and_tables():
    """创建数据库表（异步）"""
    # 必须先导入所有模型，这样 SQLModel.metadata 才会包含表定义
    from app.models.schemas import User, UserProfile, UserToken
    
    await db_manager.create_tables_async()
    print("✅ 数据库表创建完成")


async def init_default_data():
    """初始化默认数据（异步）"""
    from app.models.schemas import User
    from sqlalchemy import select
    
    async with db_manager._get_async_session()() as session:
        # 检查是否已有测试用户
        result = await session.execute(select(User).where(User.username == "testuser"))
        user = result.scalar_one_or_none()
        if not user:
            # 这里需要密码哈希服务，暂时使用明文占位
            user = User(
                username="testuser",
                password_hash="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/8KzKz2O",  # bcrypt hash of "123456"
                nickname="测试用户",
                email="test@example.com",
                status=1
            )
            session.add(user)
            await session.commit()
            print("✅ 默认测试用户已创建 (username: testuser, password: 123456)")
        else:
            print("ℹ️  测试用户已存在")


async def main():
    print("="*60)
    print("开始初始化 User 数据库")
    print("="*60)
    
    # 1. 初始化数据库连接池
    print("\n[1/2] 初始化数据库连接池...")
    db_manager.init()
    print("✅ 数据库连接池已初始化")
    
    # 2. 创建表结构
    print("\n[2/2] 创建数据库表...")
    await create_db_and_tables()
    
    # 3. 初始化默认数据
    print("\n[可选] 初始化默认数据...")
    await init_default_data()
    
    print("\n" + "="*60)
    print("数据库初始化完成!")
    print("="*60)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"\n❌ 初始化失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
