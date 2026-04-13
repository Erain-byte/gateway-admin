"""
自动化集成测试 - 一键启动所有服务并运行测试

流程：
1. 检查 Gateway 是否运行
2. 启动 User Service
3. 等待服务注册
4. 运行前端模拟测试
5. 清理资源
"""

import subprocess
import time
import sys
import requests
import signal
import os


def print_section(title):
    print("\n" + "="*70)
    print(title)
    print("="*70)


def check_gateway_running():
    """检查 Gateway 是否运行"""
    print_section("步骤 1: 检查 Gateway 状态")
    
    try:
        response = requests.get("http://localhost:9000/health", timeout=3)
        if response.status_code == 200:
            print("✅ Gateway 正在运行")
            data = response.json()
            print(f"   状态: {data.get('status')}")
            print(f"   Redis: {data.get('checks', {}).get('redis')}")
            print(f"   Consul: {data.get('checks', {}).get('consul')}")
            return True
        else:
            print("❌ Gateway 响应异常")
            return False
    except Exception as e:
        print(f"❌ Gateway 未运行或无法访问: {e}")
        print("\n请先启动 Gateway:")
        print("  cd d:\\python_project\\gateway")
        print("  python main.py")
        return False


def start_user_service():
    """启动 User Service"""
    print_section("步骤 2: 启动 User Service")
    
    try:
        print("启动 test_user_service.py...")
        process = subprocess.Popen(
            [sys.executable, "test_user_service.py"],
            cwd=os.path.dirname(os.path.abspath(__file__)),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8'
        )
        
        # 等待服务启动
        print("等待服务启动...")
        time.sleep(3)
        
        # 检查服务是否就绪
        for i in range(10):
            try:
                response = requests.get("http://127.0.0.1:8001/health", timeout=2)
                if response.status_code == 200:
                    print("✅ User Service 已就绪")
                    return process
            except:
                time.sleep(1)
        
        print("❌ User Service 启动超时")
        process.terminate()
        return None
        
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        return None


def wait_for_service_registration():
    """等待服务注册到 Consul"""
    print_section("步骤 3: 等待服务注册")
    
    print("等待服务注册到 Consul...")
    for i in range(10):
        try:
            response = requests.get(
                "http://localhost:8500/v1/catalog/service/user-service",
                timeout=2
            )
            services = response.json()
            
            if services:
                print(f"✅ 服务已注册 ({len(services)} 个实例)")
                for svc in services:
                    print(f"   - {svc.get('ServiceID')}")
                return True
        except:
            pass
        
        time.sleep(1)
    
    print("⚠️  服务注册超时，继续测试...")
    return False


def run_frontend_tests():
    """运行前端模拟测试"""
    print_section("步骤 4: 运行前端模拟测试")
    
    try:
        result = subprocess.run(
            [sys.executable, "test_frontend_simulation.py"],
            cwd=os.path.dirname(os.path.abspath(__file__)),
            timeout=120
        )
        
        if result.returncode == 0:
            print("\n✅ 前端测试完成")
            return True
        else:
            print(f"\n⚠️  测试退出码: {result.returncode}")
            return False
            
    except subprocess.TimeoutExpired:
        print("\n❌ 测试超时")
        return False
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        return False


def cleanup(user_service_process):
    """清理资源"""
    print_section("步骤 5: 清理资源")
    
    if user_service_process:
        print("停止 User Service...")
        try:
            user_service_process.terminate()
            user_service_process.wait(timeout=5)
            print("✅ User Service 已停止")
        except:
            user_service_process.kill()
            print("✅ User Service 已强制停止")


def main():
    """主函数"""
    print("\n" + "#"*70)
    print("# Gateway 自动化集成测试")
    print("#"*70)
    print("\n此脚本将:")
    print("  1. 检查 Gateway 状态")
    print("  2. 启动 User Service")
    print("  3. 等待服务注册")
    print("  4. 运行完整的前端模拟测试")
    print("  5. 清理资源")
    
    input("\n按 Enter 开始测试...")
    
    user_service_process = None
    
    try:
        # 步骤 1: 检查 Gateway
        if not check_gateway_running():
            print("\n❌ 请先启动 Gateway")
            return
        
        # 步骤 2: 启动 User Service
        user_service_process = start_user_service()
        if not user_service_process:
            print("\n❌ User Service 启动失败")
            return
        
        # 步骤 3: 等待服务注册
        wait_for_service_registration()
        
        # 步骤 4: 运行测试
        run_frontend_tests()
        
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断测试")
    except Exception as e:
        print(f"\n❌ 测试过程中出错: {e}")
    finally:
        # 步骤 5: 清理
        cleanup(user_service_process)
        print("\n" + "="*70)
        print("测试完成！")
        print("="*70)


if __name__ == "__main__":
    main()
