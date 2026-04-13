# Request/Response 处理对比指南

> 本文档详细对比 PHP、Go (Gin) 和 Python (FastAPI) 在 HTTP 请求处理和响应返回方面的差异，帮助开发者快速理解和迁移。

## 📋 目录

- [1. 获取请求数据](#1-获取请求数据)
- [2. 返回响应数据](#2-返回响应数据)
- [3. 完整示例：用户注册](#3-完整示例用户注册)
- [4. 核心差异总结](#4-核心差异总结)
- [5. 最佳实践](#5-最佳实践)

---

## 1. 获取请求数据

### 1.1 Query 参数（URL 参数）

#### PHP
```php
<?php
// URL: /users?id=1&name=john

$id = $_GET['id'] ?? null;           // 1
$name = $_GET['name'] ?? '';         // "john"
$page = intval($_GET['page'] ?? 1);  // 类型转换
```

#### Go (Gin)
```go
package main

import "github.com/gin-gonic/gin"

func GetUsers(c *gin.Context) {
    // URL: /users?id=1&name=john
    
    id := c.DefaultQuery("id", "0")        // "1" (string)
    name := c.Query("name")                 // "john"
    page := c.DefaultInt("page", 1)         // 1 (int)
    
    // 绑定到结构体
    type QueryParams struct {
        ID   int    `form:"id"`
        Name string `form:"name"`
    }
    var params QueryParams
    c.ShouldBindQuery(&params)
}
```

#### Python (FastAPI)
```python
from fastapi import FastAPI, Query
from typing import Optional

app = FastAPI()

@app.get("/users")
def get_users(
    id: Optional[int] = Query(None),
    name: str = Query(""),
    page: int = Query(1, ge=1),  # 自动验证 >= 1
):
    """
    获取用户列表
    
    FastAPI 自动完成：
    ✅ 类型转换（string → int）
    ✅ 默认值处理
    ✅ 范围验证
    """
    return {"id": id, "name": name, "page": page}
```

---

### 1.2 POST 表单数据（application/x-www-form-urlencoded）

#### PHP
```php
<?php
// 前端：<form method="POST">
//         <input name="email" value="test@example.com">
//         <input name="password" value="123456">
//       </form>

$email = $_POST['email'];              // "test@example.com"
$password = $_POST['password'];        // "123456"
$nickname = $_POST['nickname'] ?? 'Guest';  // 默认值
```

#### Go (Gin)
```go
func Login(c *gin.Context) {
    // 方式 1：逐个获取
    email := c.PostForm("email")
    password := c.PostForm("password")
    nickname := c.DefaultPostForm("nickname", "Guest")
    
    // 方式 2：绑定到结构体（推荐）
    type LoginForm struct {
        Email    string `form:"email" binding:"required,email"`
        Password string `form:"password" binding:"required,min=6"`
        Nickname string `form:"nickname" default:"Guest"`
    }
    
    var form LoginForm
    if err := c.ShouldBind(&form); err != nil {
        c.JSON(400, gin.H{"error": err.Error()})
        return
    }
}
```

#### Python (FastAPI)
```python
from fastapi import FastAPI, Form

app = FastAPI()

@app.post("/login")
def login(
    email: str = Form(...),                    # 必填
    password: str = Form(..., min_length=6),   # 必填，最小长度
    nickname: str = Form("Guest"),             # 可选，默认值
):
    """
    登录接口
    
    FastAPI 自动验证：
    ✅ 必填字段检查
    ✅ 最小长度验证
    ✅ 类型转换
    """
    return {
        "status": "ok",
        "email": email,
        "nickname": nickname
    }
```

---

### 1.3 JSON Body（application/json）

#### PHP
```php
<?php
// 前端：fetch('/api/users', {
//     method: 'POST',
//     headers: {'Content-Type': 'application/json'},
//     body: JSON.stringify({email: 'test@example.com', password: '123456'})
// })

// 手动解析
$json = json_decode(file_get_contents('php://input'), true);

if (!$json) {
    http_response_code(400);
    echo json_encode(['error' => 'Invalid JSON']);
    exit;
}

$email = $json['email'] ?? '';
$password = $json['password'] ?? '';

// 手动验证
if (!filter_var($email, FILTER_VALIDATE_EMAIL)) {
    http_response_code(400);
    echo json_encode(['error' => 'Invalid email']);
    exit;
}

if (strlen($password) < 6) {
    http_response_code(400);
    echo json_encode(['error' => 'Password too short']);
    exit;
}
```

#### Go (Gin)
```go
type UserCreate struct {
    Email    string `json:"email" binding:"required,email"`
    Password string `json:"password" binding:"required,min=6"`
    Age      int    `json:"age" binding:"omitempty,gte=0,lte=150"`
}

func CreateUser(c *gin.Context) {
    var user UserCreate
    
    // 自动解析 JSON + 验证
    if err := c.ShouldBindJSON(&user); err != nil {
        c.JSON(400, gin.H{"error": err.Error()})
        return
    }
    
    // 直接使用验证后的数据
    c.JSON(201, gin.H{
        "status": "ok",
        "email": user.Email,
    })
}
```

#### Python (FastAPI)
```python
from fastapi import FastAPI
from pydantic import BaseModel, EmailStr, Field
from typing import Optional

app = FastAPI()

class UserCreate(BaseModel):
    email: EmailStr                              # 自动验证邮箱格式
    password: str = Field(..., min_length=6)     # 必填，最小长度
    age: Optional[int] = Field(0, ge=0, le=150)  # 可选，范围验证

@app.post("/api/users", status_code=201)
def create_user(user: UserCreate):
    """
    创建用户
    
    FastAPI 自动完成：
    ✅ 解析 JSON
    ✅ 验证 email 格式
    ✅ 验证 password 长度
    ✅ 验证 age 范围
    ✅ 类型转换
    
    如果验证失败，自动返回 422 错误
    """
    return {
        "status": "ok",
        "email": user.email,
        "age": user.age
    }
```

---

### 1.4 文件上传（multipart/form-data）

#### PHP
```php
<?php
// 前端：<form enctype="multipart/form-data">
//         <input type="file" name="avatar">
//       </form>

$username = $_POST['username'];
$avatar = $_FILES['avatar'];

// 移动文件
$uploadPath = '/uploads/' . basename($avatar['name']);
move_uploaded_file($avatar['tmp_name'], $uploadPath);

echo json_encode([
    'status' => 'ok',
    'filename' => $avatar['name'],
    'path' => $uploadPath
]);
```

#### Go (Gin)
```go
func UploadFile(c *gin.Context) {
    username := c.PostForm("username")
    
    // 获取文件
    file, err := c.FormFile("avatar")
    if err != nil {
        c.JSON(400, gin.H{"error": "No file uploaded"})
        return
    }
    
    // 保存文件
    uploadPath := "./uploads/" + file.Filename
    c.SaveUploadedFile(file, uploadPath)
    
    c.JSON(200, gin.H{
        "status": "ok",
        "username": username,
        "filename": file.Filename,
    })
}
```

#### Python (FastAPI)
```python
from fastapi import FastAPI, File, UploadFile, Form
import shutil
import os

app = FastAPI()

@app.post("/upload")
def upload_file(
    username: str = Form(...),
    avatar: UploadFile = File(...),
):
    """上传文件"""
    
    # 保存文件
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)
    
    file_path = os.path.join(upload_dir, avatar.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(avatar.file, buffer)
    
    return {
        "status": "ok",
        "username": username,
        "filename": avatar.filename,
        "content_type": avatar.content_type,
    }
```

---

### 1.5 Headers 和 Cookies

#### PHP
```php
<?php
// Headers
$token = $_SERVER['HTTP_AUTHORIZATION'] ?? '';
$contentType = $_SERVER['CONTENT_TYPE'] ?? '';

// Cookies
$sessionId = $_COOKIE['session_id'] ?? '';

// Client IP
$ip = $_SERVER['REMOTE_ADDR'];
```

#### Go (Gin)
```go
func GetInfo(c *gin.Context) {
    // Headers
    token := c.GetHeader("Authorization")
    contentType := c.ContentType()
    
    // Cookies
    sessionId, _ := c.Cookie("session_id")
    
    // Client IP
    ip := c.ClientIP()
    
    c.JSON(200, gin.H{
        "token": token,
        "session_id": sessionId,
        "ip": ip,
    })
}
```

#### Python (FastAPI)
```python
from fastapi import FastAPI, Request, Header, Cookie
from typing import Optional

app = FastAPI()

@app.get("/info")
def get_info(
    request: Request,
    authorization: Optional[str] = Header(None),
    session_id: Optional[str] = Cookie(None),
):
    """获取请求信息"""
    
    # Client IP
    client_ip = request.client.host
    
    return {
        "token": authorization,
        "session_id": session_id,
        "ip": client_ip,
    }
```

---

## 2. 返回响应数据

### 2.1 JSON 响应

#### PHP
```php
<?php
header('Content-Type: application/json');
http_response_code(200);

echo json_encode([
    'code' => 200,
    'message' => 'Success',
    'data' => [
        'id' => 1,
        'name' => 'John'
    ]
]);
```

#### Go (Gin)
```go
c.JSON(200, gin.H{
    "code": 200,
    "message": "Success",
    "data": gin.H{
        "id": 1,
        "name": "John",
    },
})
```

#### Python (FastAPI)
```python
@app.get("/users/{user_id}")
def get_user(user_id: int):
    """
    直接返回字典，FastAPI 自动：
    ✅ 设置 Content-Type: application/json
    ✅ 序列化为 JSON
    ✅ 设置状态码 200
    """
    return {
        "code": 200,
        "message": "Success",
        "data": {
            "id": user_id,
            "name": "John"
        }
    }
```

---

### 2.2 自定义状态码和 Headers

#### PHP
```php
<?php
http_response_code(201);
header('Content-Type: application/json');
header('X-Custom-Header: my-value');
header('Location: /users/123');

echo json_encode(['status' => 'created']);
```

#### Go (Gin)
```go
c.JSON(201, gin.H{
    "status": "created",
})
c.Header("X-Custom-Header", "my-value")
c.Redirect(301, "/users/123")
```

#### Python (FastAPI)
```python
from fastapi import Response

@app.post("/users", status_code=201)
def create_user(response: Response):
    """创建用户"""
    
    # 设置自定义 Header
    response.headers["X-Custom-Header"] = "my-value"
    response.headers["Location"] = "/users/123"
    
    return {"status": "created"}
```

---

### 2.3 错误响应

#### PHP
```php
<?php
// 404 Not Found
http_response_code(404);
echo json_encode(['error' => 'User not found']);

// 400 Bad Request
http_response_code(400);
echo json_encode(['error' => 'Invalid input']);

// 500 Internal Server Error
http_response_code(500);
echo json_encode(['error' => 'Server error']);
```

#### Go (Gin)
```go
// 404
c.JSON(404, gin.H{"error": "User not found"})

// 400
c.JSON(400, gin.H{"error": "Invalid input"})

// 500
c.JSON(500, gin.H{"error": "Server error"})
```

#### Python (FastAPI)
```python
from fastapi import HTTPException

# 404
raise HTTPException(status_code=404, detail="User not found")

# 400
raise HTTPException(status_code=400, detail="Invalid input")

# 500
raise HTTPException(status_code=500, detail="Server error")
```

---

### 2.4 重定向

#### PHP
```php
<?php
header('Location: /dashboard');
exit;
```

#### Go (Gin)
```go
c.Redirect(301, "/dashboard")
```

#### Python (FastAPI)
```python
from fastapi.responses import RedirectResponse

@app.get("/old-page")
def redirect_old():
    return RedirectResponse(url="/dashboard", status_code=301)
```

---

### 2.5 文件下载

#### PHP
```php
<?php
header('Content-Type: application/pdf');
header('Content-Disposition: attachment; filename="report.pdf"');
readfile('/path/to/report.pdf');
```

#### Go (Gin)
```go
c.FileAttachment("/path/to/report.pdf", "report.pdf")
```

#### Python (FastAPI)
```python
from fastapi.responses import FileResponse

@app.get("/download")
def download_file():
    return FileResponse(
        path="/path/to/report.pdf",
        filename="report.pdf",
        media_type="application/pdf"
    )
```

---

## 3. 完整示例：用户注册

### PHP 实现
```php
<?php
// register.php
header('Content-Type: application/json');

// 1. 只接受 POST
if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    echo json_encode(['error' => 'Method not allowed']);
    exit;
}

// 2. 获取 JSON 数据
$json = json_decode(file_get_contents('php://input'), true);

if (!$json) {
    http_response_code(400);
    echo json_encode(['error' => 'Invalid JSON']);
    exit;
}

// 3. 手动验证
if (!isset($json['email']) || !isset($json['password'])) {
    http_response_code(400);
    echo json_encode(['error' => 'Missing required fields']);
    exit;
}

$email = filter_var($json['email'], FILTER_VALIDATE_EMAIL);
if (!$email) {
    http_response_code(400);
    echo json_encode(['error' => 'Invalid email']);
    exit;
}

$password = $json['password'];
if (strlen($password) < 8) {
    http_response_code(400);
    echo json_encode(['error' => 'Password too short']);
    exit;
}

// 4. 业务逻辑
try {
    $pdo = new PDO('mysql:host=localhost;dbname=test', 'root', 'password');
    
    // 检查邮箱是否存在
    $stmt = $pdo->prepare("SELECT id FROM users WHERE email = ?");
    $stmt->execute([$email]);
    if ($stmt->fetch()) {
        http_response_code(409);
        echo json_encode(['error' => 'Email already exists']);
        exit;
    }
    
    // 插入用户
    $hashedPassword = password_hash($password, PASSWORD_BCRYPT);
    $stmt = $pdo->prepare("INSERT INTO users (email, password) VALUES (?, ?)");
    $stmt->execute([$email, $hashedPassword]);
    
    $userId = $pdo->lastInsertId();
    
    // 5. 返回成功
    http_response_code(201);
    header('Location: /users/' . $userId);
    echo json_encode([
        'code' => 201,
        'message' => 'User created',
        'data' => ['id' => $userId, 'email' => $email]
    ]);
    
} catch (PDOException $e) {
    http_response_code(500);
    echo json_encode(['error' => 'Database error']);
}
```

---

### Go (Gin) 实现
```go
package main

import (
    "net/http"
    "github.com/gin-gonic/gin"
    "gorm.io/gorm"
)

type UserCreate struct {
    Email    string `json:"email" binding:"required,email"`
    Password string `json:"password" binding:"required,min=8"`
}

type UserResponse struct {
    ID    uint   `json:"id"`
    Email string `json:"email"`
}

func RegisterUser(db *gorm.DB) gin.HandlerFunc {
    return func(c *gin.Context) {
        var userCreate UserCreate
        
        // 1. 自动解析 JSON + 验证
        if err := c.ShouldBindJSON(&userCreate); err != nil {
            c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
            return
        }
        
        // 2. 检查邮箱是否存在
        var existingUser User
        if err := db.Where("email = ?", userCreate.Email).First(&existingUser).Error; err == nil {
            c.JSON(http.StatusConflict, gin.H{"error": "Email already exists"})
            return
        }
        
        // 3. 创建用户
        hashedPassword, _ := bcrypt.GenerateFromPassword([]byte(userCreate.Password), bcrypt.DefaultCost)
        newUser := User{
            Email:    userCreate.Email,
            Password: string(hashedPassword),
        }
        
        if err := db.Create(&newUser).Error; err != nil {
            c.JSON(http.StatusInternalServerError, gin.H{"error": "Database error"})
            return
        }
        
        // 4. 返回成功
        c.Header("Location", fmt.Sprintf("/users/%d", newUser.ID))
        c.JSON(http.StatusCreated, UserResponse{
            ID:    newUser.ID,
            Email: newUser.Email,
        })
    }
}
```

---

### Python (FastAPI) 实现
```python
from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel, EmailStr, Field
from sqlmodel import SQLModel, Field, Session, create_engine, select
import bcrypt

app = FastAPI()
engine = create_engine("mysql+pymysql://root:password@localhost/test")

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)

class UserResponse(BaseModel):
    id: int
    email: str

class User(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    email: str
    password: str

@app.post("/register", status_code=201)
def register_user(
    user_data: UserCreate,
    response: Response
):
    """
    用户注册
    
    FastAPI 自动完成：
    ✅ 解析 JSON
    ✅ 验证 email 格式
    ✅ 验证 password 长度
    ✅ 类型转换
    
    如果验证失败，自动返回 422
    """
    
    with Session(engine) as session:
        # 1. 检查邮箱是否存在
        existing_user = session.exec(
            select(User).where(User.email == user_data.email)
        ).first()
        
        if existing_user:
            raise HTTPException(
                status_code=409,
                detail="Email already exists"
            )
        
        # 2. 创建用户
        hashed_password = bcrypt.hashpw(
            user_data.password.encode(),
            bcrypt.gensalt()
        ).decode()
        
        new_user = User(
            email=user_data.email,
            password=hashed_password
        )
        session.add(new_user)
        session.commit()
        session.refresh(new_user)
        
        # 3. 设置响应头
        response.headers["Location"] = f"/users/{new_user.id}"
        
        # 4. 返回响应
        return UserResponse(
            id=new_user.id,
            email=new_user.email
        )
```

---

## 4. 核心差异总结

### 4.1 代码量对比

| 功能 | PHP | Go (Gin) | Python (FastAPI) |
|------|-----|----------|------------------|
| **获取 Query 参数** | `$_GET['id']` | `c.Query("id")` | `id: int = Query()` |
| **获取 JSON Body** | `json_decode(...)` | `c.ShouldBindJSON()` | `user: UserCreate` |
| **数据验证** | 手动 if/else | Struct Tag | Pydantic Model |
| **返回 JSON** | `echo json_encode()` | `c.JSON()` | `return {}` |
| **错误处理** | 手动 `http_response_code()` | `c.JSON(400, ...)` | `raise HTTPException()` |
| **自动文档** | ❌ 需要 Swagger | ❌ 需要 Swagger | ✅ 自动生成 |
| **类型安全** | ❌ 动态类型 | ✅ 强类型 | ⚠️ 可选类型提示 |

---

### 4.2 性能对比

| 指标 | PHP | Go (Gin) | Python (FastAPI) |
|------|-----|----------|------------------|
| **并发能力** | 低（每请求一进程） | 极高（goroutine） | 高（async/await） |
| **内存占用** | 中 | 低 | 中 |
| **启动速度** | 快 | 极快 | 快 |
| **开发效率** | 高 | 中 | 高 |
| **学习曲线** | 平缓 | 陡峭 | 中等 |

---

### 4.3 适用场景

| 语言 | 优势 | 劣势 | 适用场景 |
|------|------|------|---------|
| **PHP** | 部署简单、生态成熟 | 并发差、性能低 | 传统 Web 应用、CMS |
| **Go** | 高性能、高并发 | 代码冗长、学习曲线陡 | 微服务、高并发系统 |
| **Python** | 开发快、生态广 | 性能一般、GIL 限制 | API 服务、AI、数据分析 |

---

## 5. 最佳实践

### 5.1 PHP 最佳实践

✅ **使用框架**：Laravel、Symfony  
✅ **启用 OPcache**：提升性能  
✅ **使用 Composer**：管理依赖  
✅ **避免全局变量**：使用依赖注入  

❌ **不要**：直接使用 `$_GET/$_POST`，使用框架的 Request 对象  
❌ **不要**：手动拼接 SQL，使用 ORM 或 Query Builder  

---

### 5.2 Go 最佳实践

✅ **使用 Struct Tag**：自动验证和绑定  
✅ **错误处理**：始终检查 `err != nil`  
✅ **接口抽象**：便于测试和解耦  
✅ **Context 传递**：控制超时和取消  

❌ **不要**：忽略错误  
❌ **不要**：使用全局变量存储状态  

---

### 5.3 Python 最佳实践

✅ **使用 Pydantic**：自动验证和序列化  
✅ **类型提示**：提高代码可读性和 IDE 支持  
✅ **异步编程**：提升并发性能  
✅ **依赖注入**：FastAPI 的核心特性  

❌ **不要**：过度使用全局变量  
❌ **不要**：阻塞异步函数（使用 `await`）  

---

## 📚 参考资料

- [PHP 官方文档](https://www.php.net/manual/zh/)
- [Gin Framework](https://gin-gonic.com/docs/)
- [FastAPI 官方文档](https://fastapi.tiangolo.com/)
- [Pydantic 文档](https://docs.pydantic.dev/)

---

**文档版本**: v1.0  
**最后更新**: 2026-04-13  
**维护者**: Development Team
