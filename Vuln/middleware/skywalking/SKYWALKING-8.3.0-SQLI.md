---
id: SKYWALKING-8.3.0-SQLI
title: Apache SkyWalking SQL注入漏洞
product: skywalking
vendor: Apache
version_affected: "<= 8.3.0"
severity: HIGH
tags: [sqli, 无需认证]
fingerprint: ["Apache SkyWalking", "SkyWalking"]
---

## 漏洞描述

Apache SkyWalking 是一款应用性能监控（APM）工具。在 <= 8.3.0 版本中存在 SQL 注入漏洞，攻击者可以通过构造恶意请求获取数据库敏感信息。

## 影响版本

- Apache SkyWalking <= 8.3.0

## 前置条件

- 无需认证
- 需要能够访问 SkyWalking Web UI 或 API

## 利用步骤

1. 找到 SQL 注入点
2. 构造恶意 SQL payload

## Payload

```bash
# 示例 SQL 注入
sqlmap -u "http://target:8080/graphql" --data='{"query":"..."}' --level=3
```

## 验证方法

```bash
# 使用 sqlmap 检测
sqlmap -u "http://target:8080/graphql" --batch --dbs
```

## 修复建议

1. 升级 Apache SkyWalking 至 8.3.1+
2. 对用户输入进行严格过滤
3. 使用参数化查询
