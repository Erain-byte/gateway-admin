@echo off
chcp 65001 >nul
echo.
echo ========================================================================
echo Gateway 完整功能测试 - 快速启动
echo ========================================================================
echo.
echo 此脚本将:
echo   1. 检查 Consul 状态
echo   2. 检查 Redis 状态  
echo   3. 检查 Gateway 状态
echo   4. 启动 User Service
echo   5. 运行前端模拟测试
echo.
echo ------------------------------------------------------------------------
echo.

REM 检查 Consul
echo [1/5] 检查 Consul...
curl -s http://localhost:8500/v1/status/leader >nul 2>&1
if %errorlevel% equ 0 (
    echo     ✅ Consul 正在运行
) else (
    echo     ❌ Consul 未运行，请先启动 Consul
    echo        cd d:\python_project\consul
    echo        .\consul.exe agent -dev -data-dir="d:\python_project\consul\data"
    pause
    exit /b 1
)

REM 检查 Redis
echo [2/5] 检查 Redis...
redis-cli -a 123123 ping >nul 2>&1
if %errorlevel% equ 0 (
    echo     ✅ Redis 正在运行
) else (
    echo     ⚠️  Redis 可能未运行或密码错误
)

REM 检查 Gateway
echo [3/5] 检查 Gateway...
curl -s http://localhost:9000/health >nul 2>&1
if %errorlevel% equ 0 (
    echo     ✅ Gateway 正在运行
) else (
    echo     ❌ Gateway 未运行，请先启动 Gateway
    echo        cd d:\python_project\gateway
    echo        python main.py
    pause
    exit /b 1
)

echo.
echo ------------------------------------------------------------------------
echo.
echo [4/5] 准备启动 User Service...
echo.
echo 提示: User Service 将在新窗口中启动
echo       测试完成后请手动关闭该窗口
echo.
pause

REM 启动 User Service（新窗口）
start "User Service" cmd /k "cd /d %~dp0 && python test_user_service.py"

echo.
echo [5/5] 等待 User Service 启动...
timeout /t 5 /nobreak >nul

echo.
echo ------------------------------------------------------------------------
echo.
echo 运行前端模拟测试...
echo.
python test_frontend_simulation.py

echo.
echo ========================================================================
echo 测试完成！
echo ========================================================================
echo.
echo 提示:
echo   - User Service 仍在后台运行
echo   - 可以手动关闭 "User Service" 窗口
echo   - 查看 TESTING.md 了解更多测试选项
echo.
pause
