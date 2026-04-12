# Gateway API - HTTPS 配置指南

## 🔒 启用 HTTPS

### 方法 1：使用 Let's Encrypt（推荐，免费）

#### 1. 安装 Certbot

```bash
# Ubuntu/Debian
sudo apt-get install certbot

# CentOS/RHEL
sudo yum install certbot
```

#### 2. 获取证书

```bash
#  standalone 模式（需要停止网关）
sudo certbot certonly --standalone -d your-domain.com

# 或使用 webroot 模式（无需停止服务）
sudo certbot certonly --webroot -w /var/www/html -d your-domain.com
```

证书将保存在：
- `/etc/letsencrypt/live/your-domain.com/fullchain.pem`
- `/etc/letsencrypt/live/your-domain.com/privkey.pem`

#### 3. 配置 Gateway

编辑 `.env` 文件：

```bash
HTTPS_ENABLED=true
SSL_CERT_PATH=/etc/letsencrypt/live/your-domain.com/fullchain.pem
SSL_KEY_PATH=/etc/letsencrypt/live/your-domain.com/privkey.pem
SSL_VERIFY=true
```

#### 4. 自动续期

```bash
# 添加到 crontab
sudo crontab -e

# 每月1号凌晨3点检查并续期
0 3 1 * * certbot renew --quiet && systemctl restart gateway
```

---

### 方法 2：使用自签名证书（仅开发环境）

```bash
# 生成自签名证书
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes

# 配置 .env
HTTPS_ENABLED=true
SSL_CERT_PATH=./cert.pem
SSL_KEY_PATH=./key.pem
SSL_VERIFY=false  # ⚠️ 生产环境不要设置为 false
```

⚠️ **警告**：自签名证书会导致浏览器安全警告，仅用于开发测试。

---

### 方法 3：使用商业 SSL 证书

1. 从证书提供商购买证书（如 DigiCert、Comodo）
2. 下载证书文件（通常包含 `.crt` 和 `.key`）
3. 配置 `.env`：

```bash
HTTPS_ENABLED=true
SSL_CERT_PATH=/path/to/your_domain.crt
SSL_KEY_PATH=/path/to/your_domain.key
SSL_CA_BUNDLE=/path/to/ca_bundle.crt  # 如果需要中间证书
SSL_VERIFY=true
```

---

### 方法 4：通过反向代理（Nginx）

如果不想在 Gateway 中直接配置 HTTPS，可以使用 Nginx 作为反向代理：

#### 1. 安装 Nginx

```bash
sudo apt-get install nginx
```

#### 2. 配置 Nginx

```nginx
# /etc/nginx/sites-available/gateway
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    # SSL 优化配置
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    location / {
        proxy_pass http://localhost:9000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket 支持
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

#### 3. 启用配置

```bash
sudo ln -s /etc/nginx/sites-available/gateway /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

#### 4. Gateway 配置

保持 Gateway 使用 HTTP：

```bash
HTTPS_ENABLED=false
PORT=9000
```

---

## 🧪 验证 HTTPS 配置

### 1. 启动服务

```bash
python main.py
```

应该看到日志：

```
✅ HTTPS 已启用 - 证书: /path/to/cert.pem
INFO:     Started server process [xxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on https://0.0.0.0:9000 (Press CTRL+C to quit)
```

### 2. 测试连接

```bash
# 测试 HTTPS
curl -k https://localhost:9000/health

# 预期响应
{"status":"healthy","service":"gateway"}
```

### 3. 在线检测

访问 [SSL Labs](https://www.ssllabs.com/ssltest/) 输入你的域名进行完整检测。

---

## ⚠️ 常见问题

### 问题 1：证书权限错误

```
PermissionError: [Errno 13] Permission denied: '/etc/letsencrypt/...'
```

**解决方法**：

```bash
# 调整证书权限
sudo chmod 644 /etc/letsencrypt/live/your-domain.com/fullchain.pem
sudo chmod 600 /etc/letsencrypt/live/your-domain.com/privkey.pem

# 或将用户添加到 ssl-cert 组
sudo usermod -a -G ssl-cert $USER
```

### 问题 2：端口被占用

```
OSError: [Errno 98] Address already in use
```

**解决方法**：

```bash
# 检查哪个进程占用了 443 端口
sudo lsof -i :443

# 停止冲突的服务
sudo systemctl stop apache2  # 如果使用 Apache
```

### 问题 3：混合内容警告

浏览器提示 "Mixed Content" 错误。

**原因**：HTTPS 页面加载了 HTTP 资源。

**解决方法**：
- 确保所有静态资源使用 HTTPS
- 在 HTML 中添加 `<meta http-equiv="Content-Security-Policy" content="upgrade-insecure-requests">`

---

## 📊 性能优化

### 启用 HTTP/2

在 `.env` 中启用：

```bash
HTTP_HTTP2_ENABLED=true
```

### SSL 会话缓存

添加 Nginx 配置（如果使用反向代理）：

```nginx
ssl_session_cache shared:SSL:10m;
ssl_session_timeout 10m;
```

### OCSP Stapling

```nginx
ssl_stapling on;
ssl_stapling_verify on;
resolver 8.8.8.8 8.8.4.4 valid=300s;
resolver_timeout 5s;
```

---

## 🔐 安全最佳实践

1. **定期更新证书**：设置自动续期
2. **禁用旧协议**：只允许 TLSv1.2 和 TLSv1.3
3. **使用强加密套件**：避免使用 RC4、DES 等弱加密
4. **启用 HSTS**：

```nginx
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
```

5. **监控证书过期**：使用工具如 [Certificate Expiry Monitor](https://certificate.expiry.monitor/)

---

## 📚 更多信息

- [Let's Encrypt 官方文档](https://letsencrypt.org/docs/)
- [Mozilla SSL Configuration Generator](https://ssl-config.mozilla.org/)
- [SSL Labs 测试工具](https://www.ssllabs.com/ssltest/)