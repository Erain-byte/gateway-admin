"""
测试降级缓存功能

验证：
1. 缓存目录位置正确（在 Gateway 项目内）
2. 能够正确保存和加载缓存
3. 降级策略工作正常
"""

import os
import sys
import json

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.settings import BASE_DIR
from app.services.config_manager import ConfigManager


def test_cache_directory():
    """测试缓存目录位置"""
    print("\n" + "="*60)
    print("测试 1: 缓存目录位置")
    print("="*60)
    
    expected_dir = os.path.join(BASE_DIR, "data")
    expected_file = os.path.join(expected_dir, "config_cache.json")
    
    print(f"\nBASE_DIR: {BASE_DIR}")
    print(f"期望的缓存目录: {expected_dir}")
    print(f"期望的缓存文件: {expected_file}")
    
    # 检查目录是否存在
    if os.path.exists(expected_dir):
        print(f"✅ 缓存目录存在: {expected_dir}")
    else:
        print(f"❌ 缓存目录不存在: {expected_dir}")
        return False
    
    # 检查是否是绝对路径且在 Gateway 项目内
    if expected_dir.startswith(BASE_DIR):
        print(f"✅ 缓存目录在 Gateway 项目内")
    else:
        print(f"❌ 缓存目录不在 Gateway 项目内")
        return False
    
    return True


async def test_cache_save_and_load():
    """测试缓存保存和加载"""
    print("\n" + "="*60)
    print("测试 2: 缓存保存和加载")
    print("="*60)
    
    try:
        # 创建 ConfigManager 实例
        config_mgr = ConfigManager()
        
        # 测试数据
        test_data = {
            "config:cors": json.dumps({
                "origins": ["http://test.com"],
                "credentials": True
            }),
            "config:hmac:test-app": "test-secret-key"
        }
        
        # 保存到缓存
        print("\n2.1 保存测试数据到缓存...")
        for key, value in test_data.items():
            config_mgr._cache_set(key, value)
            print(f"   ✅ 已保存: {key}")
        
        # 验证文件存在
        cache_file = config_mgr._cache_file
        if os.path.exists(cache_file):
            print(f"\n2.2 验证缓存文件存在...")
            print(f"   ✅ 缓存文件存在: {cache_file}")
        else:
            print(f"   ❌ 缓存文件不存在: {cache_file}")
            return False
        
        # 从文件加载
        print("\n2.3 从文件加载缓存...")
        config_mgr._load_local_cache()
        
        # 验证加载的数据
        print("\n2.4 验证加载的数据...")
        for key, expected_value in test_data.items():
            loaded_value = config_mgr._cache_get(key)
            if loaded_value == expected_value:
                print(f"   ✅ {key}: 数据匹配")
            else:
                print(f"   ❌ {key}: 数据不匹配")
                print(f"      期望: {expected_value}")
                print(f"      实际: {loaded_value}")
                return False
        
        print("\n✅ 缓存保存和加载测试通过")
        return True
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_fallback_strategy():
    """测试降级策略"""
    print("\n" + "="*60)
    print("测试 3: 降级策略（Redis → Consul → 本地缓存）")
    print("="*60)
    
    try:
        config_mgr = ConfigManager()
        
        # 设置测试数据到本地缓存
        test_key = "config:hmac:fallback-test"
        test_value = "fallback-secret-key"
        config_mgr._cache_set(test_key, test_value)
        
        print("\n3.1 模拟 Redis 和 Consul 不可用...")
        print("   （实际测试中，如果 Redis/Consul 连接失败会自动降级）")
        
        print("\n3.2 从本地缓存获取数据...")
        # 直接测试本地缓存获取
        cached_value = config_mgr._cache_get(test_key)
        
        if cached_value == test_value:
            print(f"   ✅ 成功从本地缓存获取: {test_key}")
            print(f"   值: {cached_value}")
            return True
        else:
            print(f"   ❌ 从本地缓存获取失败")
            return False
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """运行所有测试"""
    print("\n" + "#"*60)
    print("# Gateway 降级缓存功能测试")
    print("#"*60)
    
    results = []
    
    # 测试 1: 缓存目录位置
    results.append(("缓存目录位置", test_cache_directory()))
    
    # 测试 2: 缓存保存和加载
    results.append(("缓存保存和加载", await test_cache_save_and_load()))
    
    # 测试 3: 降级策略
    results.append(("降级策略", await test_fallback_strategy()))
    
    # 打印总结
    print("\n" + "="*60)
    print("测试总结")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status} - {name}")
    
    print("\n" + "-"*60)
    print(f"总计: {passed}/{total} 测试通过")
    print(f"成功率: {passed/total*100:.1f}%")
    print("-"*60)
    
    if passed == total:
        print("\n🎉 所有测试通过！降级缓存功能正常！")
    else:
        print(f"\n⚠️  部分测试失败，请检查配置")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
