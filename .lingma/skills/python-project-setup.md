---
name: python-project-setup
description: 为新 Python 项目设置标准结构、配置文件和开发环境
version: 1.0.0
tags: [python, setup, project, initialization]
---

# Python 项目初始化 Skill

## 触发条件

当用户请求：
- "创建一个新的 Python 项目"
- "初始化 Python 项目结构"
- "设置 Python 开发环境"
- "搭建 Python 项目框架"

## 执行步骤

### 1. 询问项目信息

首先向用户确认：
- 项目名称
- 项目类型（Web API、CLI 工具、库、数据分析等）
- Python 版本要求
- 是否需要虚拟环境
- 主要依赖包

### 2. 创建项目结构

根据项目类型创建标准目录结构：

**Web API 项目**:
```
project_name/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py
│   ├── services/
│   │   ├── __init__.py
│   │   └── business_logic.py
│   └── utils/
│       ├── __init__.py
│       └── helpers.py
├── tests/
│   ├── __init__.py
│   ├── unit/
│   └── integration/
├── config/
│   ├── __init__.py
│   └── settings.py
├── docs/
├── scripts/
├── .env
├── .env.example
├── .gitignore
├── requirements.txt
├── README.md
└── pyproject.toml
```

**CLI 工具项目**:
```
project_name/
├── src/
│   └── project_name/
│       ├── __init__.py
│       ├── cli.py
│       └── commands/
├── tests/
├── .gitignore
├── setup.py
├── requirements.txt
└── README.md
```

### 3. 创建配置文件

#### .gitignore
```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
venv/
env/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo

# Environment variables
.env

# Testing
.pytest_cache/
.coverage
htmlcov/

# Logs
*.log
logs/
```

#### .env.example
```env
# Application
APP_NAME=My Project
DEBUG=true
HOST=0.0.0.0
PORT=8000

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/dbname

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=

# Secret Keys
SECRET_KEY=change-me-in-production
```

#### requirements.txt
```txt
# Core dependencies
fastapi>=0.100.0
uvicorn[standard]>=0.23.0
pydantic>=2.0.0
pydantic-settings>=2.0.0

# Database
sqlalchemy>=2.0.0
alembic>=1.12.0

# Redis
redis>=5.0.0

# Utilities
python-dotenv>=1.0.0
loguru>=0.7.0

# Testing
pytest>=7.4.0
pytest-asyncio>=0.21.0
httpx>=0.25.0

# Code quality
black>=23.7.0
flake8>=6.1.0
mypy>=1.5.0
```

#### pyproject.toml (可选，现代 Python 项目)
```toml
[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.backends._legacy:_Backend"

[project]
name = "project-name"
version = "0.1.0"
description = "Project description"
requires-python = ">=3.10"
dependencies = [
    "fastapi>=0.100.0",
    "uvicorn[standard]>=0.23.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "black>=23.7.0",
    "mypy>=1.5.0",
]
```

### 4. 创建基础代码文件

#### app/main.py
```python
"""
应用主入口
"""
from fastapi import FastAPI
from loguru import logger


app = FastAPI(
    title="Project Name",
    description="Project description",
    version="0.1.0"
)


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
```

#### config/settings.py
```python
"""
应用配置
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "My Project"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    DATABASE_URL: str = "sqlite:///./test.db"
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    
    SECRET_KEY: str = "change-me"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )


settings = Settings()
```

### 5. 创建 README.md

```markdown
# Project Name

项目描述

## 功能特性

- 特性 1
- 特性 2

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，填写正确的配置
```

### 运行项目

```bash
python -m app.main
```

访问 http://localhost:8000

## 开发

### 运行测试

```bash
pytest
```

### 代码格式化

```bash
black .
flake8
```

## 项目结构

```
project/
├── app/          # 应用代码
├── tests/        # 测试代码
├── config/       # 配置文件
└── docs/         # 文档
```

## License

MIT
```

### 6. 创建测试框架

#### tests/conftest.py
```python
"""
Pytest 配置
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    """创建测试客户端"""
    return TestClient(app)
```

#### tests/test_main.py
```python
"""
主应用测试
"""


def test_root(client):
    """测试根路径"""
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()


def test_health(client):
    """测试健康检查"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
```

### 7. 设置虚拟环境（如果需要）

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 8. 初始化 Git 仓库

```bash
git init
git add .
git commit -m "Initial commit: Project setup"
```

## 输出检查清单

完成项目初始化后，确认以下内容：

- [ ] 项目目录结构已创建
- [ ] .gitignore 文件已配置
- [ ] .env.example 文件已创建
- [ ] requirements.txt 已生成
- [ ] 基础代码文件已创建
- [ ] README.md 已编写
- [ ] 测试框架已设置
- [ ] Git 仓库已初始化

## 后续建议

1. **添加 CI/CD 配置**
   - GitHub Actions
   - GitLab CI

2. **添加 Docker 支持**
   - Dockerfile
   - docker-compose.yml

3. **添加文档**
   - API 文档（Swagger/OpenAPI）
   - 开发文档

4. **配置代码质量工具**
   - pre-commit hooks
   - CI 中的自动化检查

## 示例对话

**用户**: "帮我创建一个 FastAPI 项目，名为 user-service"

**Agent**: 
1. 确认项目信息
2. 创建目录结构
3. 生成所有配置文件
4. 创建基础代码
5. 提供启动说明

**输出**:
```
✅ 项目 user-service 已创建成功！

📁 项目结构:
user-service/
├── app/
├── tests/
├── config/
└── ...

🚀 快速开始:
1. cd user-service
2. cp .env.example .env
3. pip install -r requirements.txt
4. python -m app.main

📖 查看 README.md 了解更多
```
