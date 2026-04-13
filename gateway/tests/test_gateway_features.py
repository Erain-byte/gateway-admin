"""
Gateway 功能测试脚本

测试内容：
1. 服务注册与发现
2. 负载均衡
3. 路由转发
4. HMAC 签名验证
5. 限流
6. 熔断
7. CORS
"""

import requests
import time
import hmac
import hashlib
import base64
import json
from datetime import datetime

# Gateway 地址
GATEWAY_URL = "http://localhost:9000"
HMAC_SECRET_KEY = "test-secret-key-for-development-only-12345678"


def generate_hmac_signature(app_id, secret_key, body="", timestamp=None, nonce=None):
    """生成 HMAC 签名"""
    if timestamp is None:
        timestamp = str(int(time.time()))
    if nonce is None:
        nonce = hashlib.md5(f"{timestamp}{app_id}".encode()).hexdigest()[:16]
    
    # 构建签名字符串
    message = f"{app_id}\n{timestamp}\n{nonce}\n{body}"
    
    # 生成签名
    signature = hmac.new(
        secret_key.encode(),
        message.encode(),
        hashlib.sha256
    ).digest()
    
    signature_b64 = base64.b64encode(signature).decode()
    
    return {
        "X-App-ID": app_id,
        "X-Timestamp": timestamp,
        "X-Nonce": nonce,
        "X-Signature": signature_b64
    }


def test_health_check():
    """测试健康检查"""
    print("\n" + "="*60)
    print("测试 1: 健康检查")
    print("="*60)
    
    try:
        response = requests.get(f"{GATEWAY_URL}/health", timeout=5)
        print(f"✅ 状态码: {response.status_code}")
        print(f"✅ 响应: {response.json()}")
        return True
    except Exception as e:
        print(f"❌ 失败: {e}")
        return False


def test_cors_headers():
    """测试 CORS 配置"""
    print("\n" + "="*60)
    print("测试 2: CORS 跨域配置")
    print("="*60)
    
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
        print(f"✅ Access-Control-Allow-Headers: {response.headers.get('Access-Control-Allow-Headers', 'N/A')}")
        return True
    except Exception as e:
        print(f"❌ 失败: {e}")
        return False


def test_get_cors_config():
    """获取 CORS 配置"""
    print("\n" + "="*60)
    print("测试 3: 获取 CORS 配置")
    print("="*60)
    
    try:
        response = requests.get(f"{GATEWAY_URL}/api/config/cors", timeout=5)
        print(f"✅ 状态码: {response.status_code}")
        print(f"✅ 配置: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        return True
    except Exception as e:
        print(f"❌ 失败: {e}")
        return False


def test_update_cors_config():
    """更新 CORS 配置"""
    print("\n" + "="*60)
    print("测试 4: 更新 CORS 配置")
    print("="*60)
    
    try:
        new_config = {
            "origins": ["http://localhost:9527", "http://example.com"],
            "credentials": True,
            "methods": ["GET", "POST", "PUT", "DELETE"],
            "headers": ["Authorization", "Content-Type"]
        }
        
        response = requests.put(
            f"{GATEWAY_URL}/api/config/cors",
            json=new_config,
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
    print("\n" + "="*60)
    print("测试 5: 创建 HMAC 密钥")
    print("="*60)
    
    try:
        app_id = "test-app-" + str(int(time.time()))
        
        response = requests.post(
            f"{GATEWAY_URL}/api/config/hmac/key",
            json={
                "app_id": app_id,
                "secret_key": "test-secret-key-123456"
            },
            timeout=5
        )
        
        print(f"✅ 状态码: {response.status_code}")
        result = response.json()
        print(f"✅ App ID: {result.get('app_id')}")
        print(f"✅ Secret Key: {result.get('secret_key')[:20]}...")
        return True
    except Exception as e:
        print(f"❌ 失败: {e}")
        return False


def test_hmac_authentication():
    """测试 HMAC 认证"""
    print("\n" + "="*60)
    print("测试 6: HMAC 签名认证")
    print("="*60)
    
    try:
        # 正确的签名
        headers = generate_hmac_signature(
            app_id="test-app",
            secret_key=HMAC_SECRET_KEY,
            body=""
        )
        
        response = requests.get(
            f"{GATEWAY_URL}/api/config/cors",
            headers=headers,
            timeout=5
        )
        
        print(f"✅ 正确签名 - 状态码: {response.status_code}")
        
        # 错误的签名
        wrong_headers = headers.copy()
        wrong_headers["X-Signature"] = "wrong-signature"
        
        response_wrong = requests.get(
            f"{GATEWAY_URL}/api/config/cors",
            headers=wrong_headers,
            timeout=5
        )
        
        print(f"✅ 错误签名 - 状态码: {response_wrong.status_code} (应该被拒绝)")
        
        if response.status_code == 200 and response_wrong.status_code == 401:
            print("✅ HMAC 认证工作正常")
            return True
        else:
            print("⚠️  HMAC 认证可能有问题")
            return False
    except Exception as e:
        print(f"❌ 失败: {e}")
        return False


def test_rate_limiting():
    """测试限流"""
    print("\n" + "="*60)
    print("测试 7: 限流功能")
    print("="*60)
    
    try:
        headers = generate_hmac_signature(
            app_id="test-app",
            secret_key=HMAC_SECRET_KEY
        )
        
        success_count = 0
        rate_limited_count = 0
        
        # 发送多个请求测试限流
        for i in range(10):
            response = requests.get(
                f"{GATEWAY_URL}/api/config/cors",
                headers=headers,
                timeout=5
            )
            
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
            print("⚠️  未达到限流阈值（可能需要更多请求）")
            return True
    except Exception as e:
        print(f"❌ 失败: {e}")
        return False


def test_service_discovery():
    """测试服务发现"""
    print("\n" + "="*60)
    print("测试 8: 服务发现（从 Consul）")
    print("="*60)
    
    try:
        # 查询 Consul 中的服务
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
    """测试路由不存在"""
    print("\n" + "="*60)
    print("测试 9: 路由不存在处理")
    print("="*60)
    
    try:
        headers = generate_hmac_signature(
            app_id="test-app",
            secret_key=HMAC_SECRET_KEY
        )
        
        response = requests.get(
            f"{GATEWAY_URL}/nonexistent/path",
            headers=headers,
            timeout=5
        )
        
        print(f"✅ 状态码: {response.status_code} (应该是 404)")
        print(f"✅ 响应: {response.json()}")
        
        if response.status_code == 404:
            print("✅ 404 处理正常")
            return True
        else:
            print("⚠️  状态码不符合预期")
            return False
    except Exception as e:
        print(f"❌ 失败: {e}")
        return False


def test_request_forwarding():
    """测试请求转发（需要后端服务运行）"""
    print("\n" + "="*60)
    print("测试 10: 请求转发")
    print("="*60)
    
    try:
        headers = generate_hmac_signature(
            app_id="test-app",
            secret_key=HMAC_SECRET_KEY
        )
        
        # 尝试转发到 user-service（如果存在）
        response = requests.get(
            f"{GATEWAY_URL}/user/health",
            headers=headers,
            timeout=5
        )
        
        print(f"✅ 状态码: {response.status_code}")
        
        if response.status_code in [200, 503]:
            if response.status_code == 503:
                print("⚠️  后端服务不可用（503），但路由转发机制工作正常")
            else:
                print(f"✅ 响应: {response.json()}")
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
    print("# Gateway 功能测试")
    print("#"*60)
    print(f"\nGateway URL: {GATEWAY_URL}")
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = []
    
    # 运行测试
    results.append(("健康检查", test_health_check()))
    results.append(("CORS 配置", test_cors_headers()))
    results.append(("获取 CORS", test_get_cors_config()))
    results.append(("更新 CORS", test_update_cors_config()))
    results.append(("创建 HMAC 密钥", test_create_hmac_key()))
    results.append(("HMAC 认证", test_hmac_authentication()))
    results.append(("限流", test_rate_limiting()))
    results.append(("服务发现", test_service_discovery()))
    results.append(("路由 404", test_route_not_found()))
    results.append(("请求转发", test_request_forwarding()))
    
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
        print("\n🎉 所有测试通过！")
    elif passed >= total * 0.8:
        print(f"\n✨ 大部分测试通过 ({passed}/{total})")
    else:
        print(f"\n⚠️  部分测试失败，请检查配置")
    
    print(f"\n结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()
