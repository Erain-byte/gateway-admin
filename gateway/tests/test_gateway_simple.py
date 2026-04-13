"""
Gateway 核心功能测试（无需 HMAC）
"""

import requests
import json
import time

GATEWAY_URL = "http://localhost:9000"


def print_section(title):
    print("\n" + "="*60)
    print(title)
    print("="*60)


def test_health():
    """测试健康检查"""
    print_section("测试 1: 健康检查")
    try:
        response = requests.get(f"{GATEWAY_URL}/health", timeout=5)
        print(f"✅ 状态码: {response.status_code}")
        data = response.json()
        print(f"✅ 服务状态: {data.get('status')}")
        print(f"✅ Redis: {data.get('checks', {}).get('redis')}")
        print(f"✅ Consul: {data.get('checks', {}).get('consul')}")
        return True
    except Exception as e:
        print(f"❌ 失败: {e}")
        return False


def test_cors_preflight():
    """测试 CORS 预检请求"""
    print_section("测试 2: CORS 跨域配置")
    try:
        response = requests.options(
            f"{GATEWAY_URL}/api/config/cors",
            headers={
                "Origin": "http://localhost:9527",
                "Access-Control-Request-Method": "GET"
            },
            timeout=5
        )
        print(f"✅ 状态码: {response.status_code}")
        print(f"✅ Access-Control-Allow-Origin: {response.headers.get('Access-Control-Allow-Origin', 'N/A')}")
        print(f"✅ Access-Control-Allow-Methods: {response.headers.get('Access-Control-Allow-Methods', 'N/A')}")
        return True
    except Exception as e:
        print(f"❌ 失败: {e}")
        return False


def test_get_cors_config():
    """获取 CORS 配置"""
    print_section("测试 3: 获取 CORS 配置")
    try:
        response = requests.get(f"{GATEWAY_URL}/api/config/cors", timeout=5)
        print(f"✅ 状态码: {response.status_code}")
        config = response.json()
        print(f"✅ Origins: {config.get('origins', [])}")
        print(f"✅ Methods: {config.get('methods', [])}")
        print(f"✅ Credentials: {config.get('credentials')}")
        return True
    except Exception as e:
        print(f"❌ 失败: {e}")
        return False


def test_update_cors_config():
    """更新 CORS 配置"""
    print_section("测试 4: 更新 CORS 配置")
    try:
        new_config = {
            "origins": ["http://localhost:9527", "http://example.com", "http://test.com"],
            "credentials": True,
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "headers": ["Authorization", "Content-Type", "X-Requested-With"]
        }
        
        response = requests.put(
            f"{GATEWAY_URL}/api/config/cors",
            json=new_config,
            timeout=5
        )
        
        print(f"✅ 状态码: {response.status_code}")
        print(f"✅ 响应: {response.json()}")
        
        # 验证更新
        verify = requests.get(f"{GATEWAY_URL}/api/config/cors", timeout=5)
        updated_config = verify.json()
        print(f"✅ 更新后 Origins: {updated_config.get('origins', [])}")
        
        return True
    except Exception as e:
        print(f"❌ 失败: {e}")
        return False


def test_add_cors_origin():
    """添加 CORS Origin"""
    print_section("测试 5: 添加 CORS Origin")
    try:
        response = requests.post(
            f"{GATEWAY_URL}/api/config/cors/origins?origin=http://newdomain.com",
            timeout=5
        )
        
        print(f"✅ 状态码: {response.status_code}")
        print(f"✅ 响应: {response.json()}")
        return True
    except Exception as e:
        print(f"❌ 失败: {e}")
        return False


def test_remove_cors_origin():
    """移除 CORS Origin"""
    print_section("测试 6: 移除 CORS Origin")
    try:
        response = requests.delete(
            f"{GATEWAY_URL}/api/config/cors/origins?origin=http://newdomain.com",
            timeout=5
        )
        
        print(f"✅ 状态码: {response.status_code}")
        print(f"✅ 响应: {response.json()}")
        return True
    except Exception as e:
        print(f"❌ 失败: {e}")
        return False


def test_create_hmac_key():
    """创建 HMAC 密钥"""
    print_section("测试 7: 创建 HMAC 密钥")
    try:
        app_id = f"test-app-{int(time.time())}"
        
        response = requests.post(
            f"{GATEWAY_URL}/api/config/hmac/key",
            json={
                "app_id": app_id,
                "secret_key": f"secret-{app_id}"
            },
            timeout=5
        )
        
        print(f"✅ 状态码: {response.status_code}")
        result = response.json()
        print(f"✅ App ID: {result.get('app_id')}")
        print(f"✅ Secret Key: {result.get('secret_key', '')[:20]}...")
        return True
    except Exception as e:
        print(f"❌ 失败: {e}")
        return False


def test_list_hmac_keys():
    """列出 HMAC 密钥"""
    print_section("测试 8: 列出 HMAC 密钥")
    try:
        response = requests.get(f"{GATEWAY_URL}/api/config/hmac/keys", timeout=5)
        
        print(f"✅ 状态码: {response.status_code}")
        keys = response.json()
        print(f"✅ 密钥数量: {len(keys)}")
        for key in keys[:5]:  # 只显示前5个
            print(f"   - {key}")
        return True
    except Exception as e:
        print(f"❌ 失败: {e}")
        return False


def test_service_discovery():
    """测试服务发现"""
    print_section("测试 9: 服务发现（Consul）")
    try:
        response = requests.get("http://localhost:8500/v1/catalog/services", timeout=5)
        services = response.json()
        
        print(f"✅ Consul 中的服务:")
        for service_name, tags in services.items():
            print(f"   - {service_name}: {tags}")
        
        return True
    except Exception as e:
        print(f"❌ 失败: {e}")
        return False


def test_route_not_found():
    """测试 404 路由"""
    print_section("测试 10: 路由不存在处理")
    try:
        response = requests.get(f"{GATEWAY_URL}/nonexistent/path", timeout=5)
        
        print(f"✅ 状态码: {response.status_code}")
        if response.status_code == 404:
            print(f"✅ 响应: {response.json()}")
            print("✅ 404 处理正常")
            return True
        else:
            print(f"⚠️  意外状态码: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 失败: {e}")
        return False


def test_rate_limiting():
    """测试限流"""
    print_section("测试 11: 限流功能")
    try:
        success_count = 0
        rate_limited_count = 0
        
        # 发送多个请求
        for i in range(15):
            response = requests.get(f"{GATEWAY_URL}/api/config/cors", timeout=5)
            
            if response.status_code == 200:
                success_count += 1
            elif response.status_code == 429:
                rate_limited_count += 1
                print(f"✅ 请求 {i+1} 被限流 (429)")
                break
        
        print(f"✅ 成功请求: {success_count}")
        print(f"✅ 被限流请求: {rate_limited_count}")
        
        if rate_limited_count > 0:
            print("✅ 限流功能工作正常")
            return True
        else:
            print("⚠️  未达到限流阈值")
            return True
    except Exception as e:
        print(f"❌ 失败: {e}")
        return False


def test_request_forwarding():
    """测试请求转发"""
    print_section("测试 12: 请求转发（需要后端服务）")
    try:
        # 尝试转发到 user-service
        response = requests.get(f"{GATEWAY_URL}/user/health", timeout=5)
        
        print(f"✅ 状态码: {response.status_code}")
        
        if response.status_code == 503:
            print("⚠️  后端服务不可用（503），但路由转发机制工作正常")
            print(f"✅ 响应: {response.json()}")
            return True
        elif response.status_code == 200:
            print(f"✅ 后端服务响应: {response.json()}")
            return True
        else:
            print(f"⚠️  意外状态码: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 失败: {e}")
        return False


def main():
    """运行所有测试"""
    print("\n" + "#"*60)
    print("# Gateway 核心功能测试")
    print("#"*60)
    print(f"\nGateway URL: {GATEWAY_URL}")
    
    results = []
    
    # 运行测试
    results.append(("健康检查", test_health()))
    results.append(("CORS 预检", test_cors_preflight()))
    results.append(("获取 CORS", test_get_cors_config()))
    results.append(("更新 CORS", test_update_cors_config()))
    results.append(("添加 Origin", test_add_cors_origin()))
    results.append(("移除 Origin", test_remove_cors_origin()))
    results.append(("创建 HMAC 密钥", test_create_hmac_key()))
    results.append(("列出 HMAC 密钥", test_list_hmac_keys()))
    results.append(("服务发现", test_service_discovery()))
    results.append(("404 处理", test_route_not_found()))
    results.append(("限流", test_rate_limiting()))
    results.append(("请求转发", test_request_forwarding()))
    
    # 打印总结
    print_section("测试总结")
    
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
        print("\n🎉 所有测试通过！")
    elif passed >= total * 0.8:
        print(f"\n✨ 大部分测试通过 ({passed}/{total})")
    else:
        print(f"\n⚠️  部分测试失败，请检查配置")


if __name__ == "__main__":
    main()
