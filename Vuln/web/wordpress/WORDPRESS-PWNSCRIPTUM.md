---
id: WORDPRESS-PWNSCRIPTUM
title: WordPress 4.6 任意命令执行漏洞（PwnScriptum）
product: wordpress
vendor: WordPress
version_affected: "<= 4.6"
severity: CRITICAL
tags: [rce, 无需认证]
fingerprint: ["WordPress"]
---

## 漏洞描述

WordPress 4.6 及以前版本中存在邮件密码重置功能漏洞，攻击者可以通过构造特殊的请求绕过验证并执行任意命令。该漏洞利用 PHPMailer 的命令注入漏洞。

## 影响版本

- WordPress <= 4.6

## 前置条件

- 无需认证
- 需要知道一个存在的用户名

## 利用步骤

1. 使用特殊构造的请求绕过验证
2. 利用 SMTP 组件执行命令

## Payload

```http
POST /wp-login.php?action=lostpassword HTTP/1.1
Host: target:8080

wp-submit=Get+New+Password&redirect_to=&user_login=admin
```

## 验证方法

```bash
# 检查命令是否执行
```

## 修复建议

1. 升级 WordPress 至 4.7+
2. 升级 PHPMailer 至最新版本
3. 使用强密码策略
