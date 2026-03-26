---
name: cloud-iam-audit
description: "云 IAM 权限审计与提权。当获取了云平台凭据（AWS AK/SK、Azure SPN、GCP SA）需要评估权限范围和提权路径时使用。覆盖 AWS/Azure/GCP 的 IAM 策略分析、常见提权路径（PassRole、AssumeRole、Lambda 提权）、跨账号攻击、CloudTrail 规避"
metadata:
  tags: "cloud,iam,audit,privilege,escalation,aws,azure,gcp,提权,权限,凭据,PassRole"
  difficulty: "hard"
  icon: "🔒"
  category: "云环境"
---

# 云 IAM 权限审计与提权方法论

IAM 权限就是攻击面——一个过度授权的策略比一个 RCE 漏洞更危险。

## ⛔ 深入参考（必读）

- ⛔**必读** 需要 AWS 5 条提权路径详细命令、高价值数据搜索、CloudTrail 隐蔽性 → `read_skill(id="cloud-iam-audit", path="references/aws-escalation.md")`

---

## Phase 1: 凭据识别与身份确认

| 凭据 | 格式 | 来源 |
|------|------|------|
| AWS AK/SK | `AKIA...` (20字符) | 配置文件、环境变量、元数据 |
| AWS 临时凭据 | `ASIA...` + SessionToken | IMDS、STS AssumeRole |
| Azure SPN | client_id + client_secret + tenant_id | 配置文件 |
| GCP SA Key | JSON 文件含 `private_key` | 服务账号密钥文件 |

```bash
aws sts get-caller-identity    # AWS: 我是谁
az account show                # Azure
gcloud auth list               # GCP
```

## Phase 2: 权限枚举

```bash
# 列出策略
aws iam list-attached-user-policies --user-name <user>
aws iam list-attached-role-policies --role-name <role>

# 暴力枚举（被拒绝时）
aws s3 ls 2>&1
aws ec2 describe-instances 2>&1
aws iam list-users 2>&1
aws lambda list-functions 2>&1
```

### 权限等级速查
| 能做的操作 | 提权可能 |
|------------|----------|
| sts:GetCallerIdentity 仅此 | 低 |
| s3:GetObject | 中（可能找到更多凭据） |
| iam:List*, iam:Get* | 中（可分析提权路径） |
| iam:CreateUser/AttachPolicy | **高**（直接提权） |
| iam:PassRole + lambda/ec2:* | **高**（间接提权） |
| sts:AssumeRole | **高**（跳到更高权限角色） |

## Phase 3: 提权决策树

```
当前权限？
├─ 能操作 IAM（CreatePolicy/AttachPolicy）→ 直接提权
├─ 有 PassRole + Lambda/EC2 → 间接提权（创建服务挂高权限 Role）
├─ 有 AssumeRole → 角色链跳转
├─ 只有数据读取 → 找更多凭据（S3/Secrets/Lambda 代码/User-Data）
└─ 详细命令 → `read_skill(id="cloud-iam-audit", path="references/aws-escalation.md")`
```

## 注意事项
- 云凭据提权核心：能操作 **IAM 本身** 才能提权
- 临时凭据有过期时间，优先用长期 AK/SK 或创建后门 Access Key
- 跨账号 Trust Policy 是关键审计点

## 提权路径
- PassRole + Lambda：lambda invoke 执行函数中嵌入提权代码
- 权限枚举工具：enumerate-iam、Pacu 等自动化工具扫描可利用权限
