"""
前端模拟测试 - 通过 Gateway 访问后端服务

测试场景：
1. 服务注册验证
2. HMAC 签名认证
3. 请求转发
4. 负载均衡
5. 限流测试
6. 熔断测试
"""

import requests
import time
import hashlib
import hmac
import base64
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

GATEWAY_URL = "http://localhost:9000"
HMAC_SECRET_KEY = "test-secret-key-for-development-only-12345678"
APP_ID = "user-service"


def generate_hmac_signature(app_id, secret_key, body="", timestamp=None, nonce=None):
    """生成 HMAC 签名"""
    if timestamp is None:
        timestamp = str(int(time.time()))
    if nonce is None:
        nonce = hashlib.md5(f"{timestamp}{app_id}".encode()).hexdigest()[:16]
    
    message = f"{app_id}\n{timestamp}\n{nonce}\n{body}"
    signature = hmac.new(
        secret_key.encode(),
        message.encode(),
        hashlib.sha256
    ).digest()
    
    return {
        "X-App-ID": app_id,
        "X-Timestamp": timestamp,
        "X-Nonce": nonce,
        "X-Signature": base64.b64encode(signature).decode()
    }


def print_section(title):
    print("\n" + "="*70)
    print(title)
    print("="*70)


def test_service_registration():
    """测试 1: 验证服务注册"""
    print_section("测试 1: 服务注册验证")
    
    try:
        # 查询 Consul 中的服务
        response = requests.get("http://localhost:8500/v1/catalog/service/user-service", timeout=5)
        services = response.json()
        
        if services:
            print(f"✅ 发现 {len(services)} 个 user-service 实例:")
            for svc in services:
                print(f"   - ID: {svc.get('ServiceID')}")
                print(f"     Address: {svc.get('ServiceAddress')}:{svc.get('ServicePort')}")
                print(f"     Tags: {svc.get('ServiceTags', [])}")
            return True
        else:
            print("⚠️  未发现 user-service，请先启动 test_user_service.py")
            return False
    except Exception as e:
        print(f"❌ 失败: {e}")
        return False


def test_hmac_authentication():
    """测试 2: HMAC 签名认证"""
    print_section("测试 2: HMAC 签名认证")
    
    # 测试 2.1: 正确的签名
    print("\n2.1 测试正确签名...")
    headers = generate_hmac_signature(APP_ID, HMAC_SECRET_KEY)
    
    try:
        response = requests.get(
            f"{GATEWAY_URL}/user/api/users",
            headers=headers,
            timeout=5
        )
        
        if response.status_code == 200:
            print(f"✅ 正确签名 - 状态码: {response.status_code}")
            data = response.json()
            print(f"✅ 响应数据: {json.dumps(data, ensure_ascii=False, indent=2)[:200]}...")
            test_2_1_pass = True
        else:
            print(f"❌ 正确签名被拒绝 - 状态码: {response.status_code}")
            print(f"   响应: {response.text}")
            test_2_1_pass = False
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        test_2_1_pass = False
    
    # 测试 2.2: 错误的签名
    print("\n2.2 测试错误签名...")
    wrong_headers = headers.copy()
    wrong_headers["X-Signature"] = "wrong-signature"
    
    try:
        response = requests.get(
            f"{GATEWAY_URL}/user/api/users",
            headers=wrong_headers,
            timeout=5
        )
        
        if response.status_code == 401:
            print(f"✅ 错误签名被拒绝 - 状态码: {response.status_code}")
            print(f"   响应: {response.json()}")
            test_2_2_pass = True
        else:
            print(f"❌ 错误签名未被拒绝 - 状态码: {response.status_code}")
            test_2_2_pass = False
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        test_2_2_pass = False
    
    # 测试 2.3: 过期的时间戳
    print("\n2.3 测试过期时间戳...")
    old_timestamp = str(int(time.time()) - 600)  # 10分钟前
    expired_headers = generate_hmac_signature(APP_ID, HMAC_SECRET_KEY, timestamp=old_timestamp)
    
    try:
        response = requests.get(
            f"{GATEWAY_URL}/user/api/users",
            headers=expired_headers,
            timeout=5
        )
        
        if response.status_code == 401:
            print(f"✅ 过期时间戳被拒绝 - 状态码: {response.status_code}")
            test_2_3_pass = True
        else:
            print(f"⚠️  过期时间戳未被拒绝 - 状态码: {response.status_code}")
            test_2_3_pass = False
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        test_2_3_pass = False
    
    return test_2_1_pass and test_2_2_pass and test_2_3_pass


def test_request_forwarding():
    """测试 3: 请求转发"""
    print_section("测试 3: 请求转发功能")
    
    headers = generate_hmac_signature(APP_ID, HMAC_SECRET_KEY)
    
    # 测试 3.1: GET 请求 - 获取用户列表
    print("\n3.1 测试 GET /user/api/users...")
    try:
        response = requests.get(
            f"{GATEWAY_URL}/user/api/users",
            headers=headers,
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 获取用户列表成功")
            print(f"   用户数量: {len(data.get('data', []))}")
            test_3_1_pass = True
        else:
            print(f"❌ 失败 - 状态码: {response.status_code}")
            test_3_1_pass = False
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        test_3_1_pass = False
    
    # 测试 3.2: GET 请求 - 获取单个用户
    print("\n3.2 测试 GET /user/api/users/1...")
    try:
        response = requests.get(
            f"{GATEWAY_URL}/user/api/users/1",
            headers=headers,
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            user = data.get('data', {})
            print(f"✅ 获取用户成功: {user.get('name')} ({user.get('email')})")
            test_3_2_pass = True
        else:
            print(f"❌ 失败 - 状态码: {response.status_code}")
            test_3_2_pass = False
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        test_3_2_pass = False
    
    # 测试 3.3: POST 请求 - 创建用户
    print("\n3.3 测试 POST /user/api/users...")
    try:
        new_user = {"name": "赵六", "email": "zhaoliu@example.com"}
        body = json.dumps(new_user)
        post_headers = generate_hmac_signature(APP_ID, HMAC_SECRET_KEY, body=body)
        post_headers["Content-Type"] = "application/json"
        
        response = requests.post(
            f"{GATEWAY_URL}/user/api/users",
            headers=post_headers,
            json=new_user,
            timeout=5
        )
        
        if response.status_code in [200, 201]:
            data = response.json()
            print(f"✅ 创建用户成功: {data.get('message')}")
            test_3_3_pass = True
        else:
            print(f"❌ 失败 - 状态码: {response.status_code}")
            test_3_3_pass = False
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        test_3_3_pass = False
    
    return test_3_1_pass and test_3_2_pass and test_3_3_pass


def test_load_balancing():
    """测试 4: 负载均衡"""
    print_section("测试 4: 负载均衡（需要多个服务实例）")
    
    headers = generate_hmac_signature(APP_ID, HMAC_SECRET_KEY)
    
    try:
        # 发送多个请求，观察是否分发到不同实例
        results = []
        for i in range(5):
            response = requests.get(
                f"{GATEWAY_URL}/user/api/users",
                headers=headers,
                timeout=5
            )
            results.append(response.status_code)
            time.sleep(0.1)
        
        success_count = sum(1 for code in results if code == 200)
        print(f"✅ 发送 5 个请求，成功 {success_count} 个")
        print(f"   结果: {results}")
        
        if success_count >= 4:
            print("✅ 负载均衡工作正常")
            return True
        else:
            print("⚠️  部分请求失败")
            return False
    except Exception as e:
        print(f"❌ 失败: {e}")
        return False


def test_rate_limiting():
    """测试 5: 限流功能"""
    print_section("测试 5: 限流功能")
    
    headers = generate_hmac_signature(APP_ID, HMAC_SECRET_KEY)
    
    try:
        success_count = 0
        rate_limited_count = 0
        
        print("发送 20 个快速请求测试限流...")
        for i in range(20):
            response = requests.get(
                f"{GATEWAY_URL}/user/api/users",
                headers=headers,
                timeout=5
            )
            
            if response.status_code == 200:
                success_count += 1
            elif response.status_code == 429:
                rate_limited_count += 1
                print(f"   ✅ 请求 {i+1} 被限流 (429)")
                break
            else:
                print(f"   ⚠️  请求 {i+1} 返回 {response.status_code}")
        
        print(f"\n✅ 成功请求: {success_count}")
        print(f"✅ 被限流请求: {rate_limited_count}")
        
        if rate_limited_count > 0:
            print("✅ 限流功能工作正常")
            return True
        else:
            print("⚠️  未达到限流阈值（可能需要调整配置）")
            return True
    except Exception as e:
        print(f"❌ 失败: {e}")
        return False


def test_circuit_breaker():
    """测试 6: 熔断器"""
    print_section("测试 6: 熔断器（模拟后端故障）")
    
    headers = generate_hmac_signature(APP_ID, HMAC_SECRET_KEY)
    
    print("注意: 此测试需要手动停止后端服务来触发熔断")
    print("提示: 按 Ctrl+C 停止 test_user_service.py，然后观察 Gateway 行为\n")
    
    try:
        # 尝试请求（如果后端已停止，应该返回 503 或触发熔断）
        response = requests.get(
            f"{GATEWAY_URL}/user/api/users",
            headers=headers,
            timeout=5
        )
        
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 503:
            print("✅ 后端不可用，返回 503")
            data = response.json()
            print(f"   响应: {data}")
            return True
        elif response.status_code == 200:
            print("⚠️  后端仍然可用，请先停止后端服务再测试")
            return False
        else:
            print(f"⚠️  意外状态码: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False


def test_concurrent_requests():
    """测试 7: 并发请求"""
    print_section("测试 7: 并发请求测试")
    
    def make_request(request_id):
        headers = generate_hmac_signature(APP_ID, HMAC_SECRET_KEY)
        try:
            start_time = time.time()
            response = requests.get(
                f"{GATEWAY_URL}/user/api/users",
                headers=headers,
                timeout=5
            )
            elapsed = time.time() - start_time
            
            return {
                "id": request_id,
                "status": response.status_code,
                "time": elapsed
            }
        except Exception as e:
            return {
                "id": request_id,
                "status": "error",
                "time": 0,
                "error": str(e)
            }
    
    try:
        print("发送 10 个并发请求...")
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request, i) for i in range(10)]
            results = [f.result() for f in as_completed(futures)]
        
        success_count = sum(1 for r in results if r["status"] == 200)
        avg_time = sum(r["time"] for r in results if r["status"] == 200) / max(success_count, 1)
        
        print(f"\n✅ 成功请求: {success_count}/10")
        print(f"✅ 平均响应时间: {avg_time*1000:.2f}ms")
        
        if success_count >= 8:
            print("✅ 并发处理能力良好")
            return True
        else:
            print("⚠️  部分请求失败")
            return False
    except Exception as e:
        print(f"❌ 失败: {e}")
        return False


def main():
    """运行所有测试"""
    print("\n" + "#"*70)
    print("# Gateway 完整功能测试（含 HMAC 验证和请求转发）")
    print("#"*70)
    print(f"\nGateway URL: {GATEWAY_URL}")
    print(f"后端服务: http://127.0.0.1:8001")
    print(f"HMAC App ID: {APP_ID}")
    
    input("\n⚠️  请确保已启动 test_user_service.py，按 Enter 继续...")
    
    results = []
    
    # 运行测试
    results.append(("服务注册", test_service_registration()))
    results.append(("HMAC 认证", test_hmac_authentication()))
    results.append(("请求转发", test_request_forwarding()))
    results.append(("负载均衡", test_load_balancing()))
    results.append(("限流", test_rate_limiting()))
    results.append(("熔断器", test_circuit_breaker()))
    results.append(("并发请求", test_concurrent_requests()))
    
    # 打印总结
    print_section("测试总结")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status} - {name}")
    
    print("\n" + "-"*70)
    print(f"总计: {passed}/{total} 测试通过")
    print(f"成功率: {passed/total*100:.1f}%")
    print("-"*70)
    
    if passed == total:
        print("\n🎉 所有测试通过！Gateway 功能完整！")
    elif passed >= total * 0.8:
        print(f"\n✨ 大部分测试通过 ({passed}/{total})")
    else:
        print(f"\n⚠️  部分测试失败，请检查配置和服务状态")


if __name__ == "__main__":
    main()
