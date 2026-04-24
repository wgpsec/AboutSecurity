# AboutSecurity 资源贡献规范

本文档定义了 `skills/` 和 `Vuln/` 目录下文件的编写规范，供社区贡献者和 AI 参考。

---

## 目录结构

```
AboutSecurity/
├── skills/                   # AI Agent 技能方法论
│   ├── recon/                # 侦察类
│   ├── exploit/              # 漏洞利用类
│   │   ├── network-service/  # 网络服务渗透方法论
│   │   │   ├── smb-pentesting/
│   │   │   ├── ftp-pentesting/
│   │   │   └── ... (19 services total)
│   │   ├── binary/           # 二进制漏洞利用方法论
│   │   │   ├── binary-exploitation-methodology/
│   │   │   └── binary-exploitation-tools/
│   │   └── web-method/       # Web 通用攻击方法论
│   ├── ctf/                  # CTF 竞赛类
│   ├── postexploit/          # 后渗透类
│   ├── lateral/              # 内网渗透/横向移动类
│   ├── cloud/                # 云环境类
│   ├── evasion/              # 免杀/检测对抗类
│   ├── malware/              # 恶意软件分析
│   ├── dfir/                 # 取证对抗（红队视角）
│   ├── threat-intel/         # 威胁情报与 APT 模拟
│   ├── tool/                 # 工具使用方法论
│   ├── general/              # 综合类
│   ├── ai-security/          # AI 安全（模型攻击）
│   ├── mobile/               # 移动应用渗透
│   │   ├── android-app-pentesting/
│   │   ├── ios-pentesting/
│   │   └── ios-exploiting/
│   ├── hardware/             # 硬件/物理安全渗透
│   │   └── firmware-analysis/
│   └── code-audit/           # 源码审计类（白盒）
│       ├── php/              # PHP 代码审计
│       ├── java/             # Java 代码审计（预留）
│       └── dotnet/           # .NET 代码审计（预留）
├── Vuln/                     # 结构化漏洞库（按产品分类）
│   ├── ai/                   # AI 相关产品
│   ├── cloud/                # 云平台
│   ├── middleware/            # 中间件（最多）
│   ├── network/              # 网络设备
│   └── web/                  # Web 应用
```
```

---

# Skills 技能方法论编写规范

## 1 概述

每个 Skill 是一个独立目录，包含一个 `SKILL.md` 文件。SKILL.md 使用 **YAML 前言 + Markdown 正文** 的格式，正文是方法论驱动的渗透指南，而非工具调用列表。

AI Agent 通过 `description` 字段匹配用户意图，读取正文作为上下文指导执行。

**核心原则**：
- **description 是触发器** — Agent 通过 description 决定是否加载此 Skill，务必写清楚触发场景
- **正文是方法论** — 教 Agent "怎么思考"，而非机械地列出工具调用步骤
- **解释 why** — 说明为什么用某种方法，而非写死 MUST/NEVER 规则
- **不使用模板变量** — `{{target}}` 等占位符不会被替换，不要使用

## 2 目录结构

```
skills/                           # 三级路径（维护者视角）
├── recon/                        # 侦察类
│   └── recon-full/
│       └── SKILL.md
├── exploit/                      # 漏洞利用类
│   ├── web-method/               # Web 通用方法论（注入/XSS/SSRF...）
│   ├── advanced/                 # 高级利用技术
│   ├── auth/                     # 认证相关攻击
│   ├── network-service/          # 网络服务渗透方法论（按端口/协议）
│   │   ├── smb-pentesting/
│   │   ├── ftp-pentesting/
│   │   └── ... (19 services total)
│   └── binary/                   # 二进制漏洞利用方法论
│       ├── binary-exploitation-methodology/
│       └── binary-exploitation-tools/
├── ctf/                          # CTF 竞赛类
├── postexploit/                  # 后渗透类（含产品后渗透技战术）
├── lateral/                      # 内网渗透/横向移动类
├── cloud/                        # 云环境类
├── evasion/                      # 免杀/检测对抗类
├── malware/                      # 恶意软件分析与开发
├── dfir/                         # 取证对抗（红队视角）
├── threat-intel/                 # 威胁情报与 APT 模拟
├── tool/                         # 工具使用方法论
├── general/                      # 综合类
├── ai-security/                  # AI 安全（模型攻击）
├── mobile/                       # 移动应用渗透
│   ├── android-app-pentesting/
│   ├── ios-pentesting/
│   └── ios-exploiting/
├── hardware/                     # 硬件/物理安全渗透
│   └── firmware-analysis/
└── code-audit/                   # 源码审计类（白盒）
    ├── php/                      # PHP 代码审计
    ├── java/                     # Java 代码审计（预留）
    └── dotnet/                   # .NET 代码审计（预留）
```

每个技能一个目录。内容较多的技能使用 `references/` 子目录存放深度参考材料（见 2.3 节）。

### 三级路径 vs 二级路径

本仓库维护时使用三级路径 `skills/<category>/<name>/SKILL.md`，便于按攻击阶段分类管理。

AI Agent 实际使用时通过 `sync-claude-skills.sh` 扁平化为二级路径 `.claude/skills/<name>/SKILL.md`，所有 skill 在同一层级，Agent 通过 `description` 字段匹配触发，**不存在跨分类跳转**。

```
维护者视角:  skills/exploit/web-method/sql-injection-methodology/SKILL.md
Agent 视角:  .claude/skills/sql-injection-methodology/SKILL.md  (软链接)
```

### 为什么 `tool/` 是独立分类

工具类 skill 不按攻击阶段划分，而是独立存放，原因：

1. **多用途工具避免重复**：如 nuclei 可用于指纹扫描、漏洞扫描、DAST、本地文件扫描。若在每个引用 nuclei 的 skill 中重复写使用方法，维护成本极高
2. **模型知识截止**：AI 模型对新版本工具的参数不了解，需要专门的 skill 文档补充最新用法
3. **运行时透明**：sync-skills.sh 将 tool/ 和其他分类一起扁平化，Agent 不感知分类层级

### exploit/ 子分类说明

exploit/ 下按攻击性质进一步分组（仅影响维护者视角，Agent 不感知）：

| 子目录 | 说明 | 典型 skill |
|--------|------|-----------|
| `web-method/` | Web 通用攻击方法论 | sql-injection, xss, ssrf, ssti, file-upload |
| `advanced/` | 高级利用技术 | http-smuggling, race-condition, prototype-pollution, supply-chain |
| `auth/` | 认证/授权类攻击 | jwt-attack, oauth-sso, idor, cors-misconfiguration |
| `network-service/` | 网络服务渗透方法论 | smb-pentesting, ftp-pentesting, dns-pentesting |
| `binary/` | 二进制漏洞利用方法论 | binary-exploitation-methodology, binary-exploitation-tools |

## 3 Progressive Disclosure 三级加载机制

加载 Skill 时采用**渐进式披露**策略，避免一次性加载过多内容消耗 token：

```
┌─────────────────────────────────────────────────────────┐
│  L1: Metadata（始终加载）                                │
│  ← name + description + tags                            │
│  ← Agent 据此决定是否需要此 Skill                        │
├─────────────────────────────────────────────────────────┤
│  L2: SKILL.md 正文（触发后加载，<500 行）                 │
│  ← 精简索引：决策树 + Phase 概要 + 速查表                │
│  ← 包含 → 读 references/xxx.md 指针                     │
├─────────────────────────────────────────────────────────┤
│  L3: references/ 子文件（按需加载）                       │
│  ← Agent 仅在需要深入某个方向时读取对应文件               │
│  ← 完整 payload、详细命令、绕过清单、脚本模板             │
└─────────────────────────────────────────────────────────┘
```

### 为什么需要三级加载

| 问题 | 旧模式（单文件 500+ 行） | 三级加载 |
|------|--------------------------|----------|
| Token 消耗 | Agent 每次加载全部内容 | L2 仅加载索引，L3 按需读取 |
| 信噪比 | 大量不相关细节干扰 Agent 决策 | 索引帮助 Agent 快速定位方向 |
| 可维护性 | 单文件膨胀难以维护 | 模块化，各文件职责清晰 |

### SKILL.md 编写规则（L2 层）

**行数限制：< 500 行**（超过 500 行必须拆分到 references/）

SKILL.md 应该是一个**精简索引**，包含：

1. **深入参考链接**（紧跟标题后）
   ```markdown
   ## 深入参考
   - 详细 payload 和绕过技术 → 读 [references/xxx.md](references/xxx.md)
   ```

2. **Phase 概要**（保留决策树和关键命令，移除冗长列表）
   ```markdown
   ## Phase 2: 提权决策树
   ​```
   当前权限？
   ├─ 已是 root → 跳到 Phase 3
   ├─ 普通用户 → 按优先级：
   │   1. sudo -l → GTFOBins 提权
   │   2. find / -perm -4000 → SUID 提权
   详细命令 → 读 references/linux-privesc-cred.md
   ​```
   ```

3. **速查表**（保留在 SKILL.md 中，Agent 高频使用）
4. **→ 读 references/ 指针**（替代冗长内容块）

### references/ 编写规则（L3 层）

| 规则 | 说明 |
|------|------|
| 文件命名 | 语义化英文短横线，如 `injection-bypass.md`、`crypto-techniques.md` |
| 文件数量 | 1-3 个为宜，不宜过多（Agent 需要决定读哪个） |
| 内容类型 | 完整 payload 清单、详细命令、绕过技术、脚本模板、CVE 表格 |
| 独立可读 | 每个文件应有标题，独立阅读时能理解上下文 |
| 无需前言 | references/ 文件不需要 YAML frontmatter |

### ⛔必读 标记使用规范

`⛔必读` 标记表示 Agent **加载此 Skill 后必须立即读取**的 reference 文件。滥用此标记会导致 Agent 一次性加载大量内容，消耗 token 且降低信噪比。

**标记原则**：

| 情况 | 标记方式 | 说明 |
|------|----------|------|
| 每次使用此 Skill 都需要的通用知识 | ⛔**必读** | 如 `response-analysis.md`（54行）、`flag-extraction.md`（59行） |
| 确认具体漏洞类型后才需要的深入内容 | **按需**（不标 ⛔） | 如 "发现 SQL 注入 → 读 server-side.md" |
| 特定技术栈才需要的参考 | **按需**（不标 ⛔） | 如 "遇到 JWT → 读 auth-jwt.md" |

**反模式**：
- ❌ 所有 reference 都标 ⛔必读 — 等于回到单文件模式，Progressive Disclosure 失效
- ❌ 索引型 Skill（如总方法论）的所有子领域文件标必读 — Agent 无法判断轻重缓急

**正确做法**：
- 按需 reference 在 SKILL.md 中按场景分组，注明触发条件（如"识别到注入类漏洞时读取"）
- ⛔必读 仅用于体量小（<500行）且普遍适用的文件
- 索引型 Skill 的 Phase 决策表应引导 Agent 去读**对应的专门 Skill**（如 `sql-injection-methodology`），而非自己的 reference

### 拆分判断标准

```
SKILL.md 行数？
├─ < 500 行 → ✅ 不需要拆分
├─ > 500 行 → ❌ 必须拆分到 references/
```

**哪些内容应该留在 SKILL.md**：
- YAML 前言（name/description/metadata）
- 深入参考链接
- Phase 概述和决策树
- 最常用的 3-5 条速查命令
- 注意事项

**哪些内容应该移到 references/**：
- 完整的 payload/字段/绕过清单（超过 10 条）
- 详细的利用脚本（超过 5 行的代码块）
- 特定技术的深度解释（如 Padding Oracle 原理）
- CVE 利用要点表格
- Windows/Linux 命令大全

### 示例对比

**❌ 拆分前**（SKILL.md 150+ 行）：
```markdown
## Phase 3: sudo 提权
sudo vim → :!/bin/bash
sudo find → sudo find / -exec /bin/bash \;
sudo python3 → sudo python3 -c 'import os; os.system("/bin/bash")'
sudo awk → sudo awk 'BEGIN {system("/bin/bash")}'
sudo env → sudo env /bin/bash
sudo less → !/bin/bash
sudo nmap → sudo nmap --interactive → !sh
... （还有 20 条）
```

**✅ 拆分后**（SKILL.md 65 行 + references/linux-privesc-cred.md）：
```markdown
## Phase 2: 提权决策树
sudo 速查：`vim → :!bash` | `find → -exec bash` | `NOPASSWD: ALL → sudo su`
→ 完整 sudo/SUID/cron/capabilities 命令 → 读 references/linux-privesc-cred.md
```

## 4 SKILL.md 格式

```markdown
---
name: skill-name
description: "一段详细的、带触发场景的描述。当遇到 X 情况、发现 Y 特征、需要做 Z 测试时使用。覆盖 A、B、C 方面"
metadata:
  tags: "tag1,tag2,tag3,关键词"
  category: "分类名"
---

# 技能标题

简要说明这个技能解决什么问题、为什么需要它。

## Phase 1: 第一阶段

### 1.1 子步骤
具体方法论内容...
决策表、判断条件、攻击向量...

## Phase 2: 第二阶段
...

## 注意事项
- 关键提醒和常见陷阱
```

## 5 字段说明

### 前言字段

| 字段 | 必填 | 说明 |
|------|------|------|
| `name` | ✅ | 技能唯一标识，英文短横线命名，与目录名一致 |
| `description` | ✅ | **最重要的字段**。详细描述触发场景和覆盖范围（见 2.5） |
| `metadata.tags` | ✅ | 逗号分隔的标签，包含中英文关键词便于搜索 |
| `metadata.category` | ✅ | 分类名（见 2.6） |

### 正文要求

- **< 500 行**（超过需拆分到 `references/`，见 2.3 Progressive Disclosure）
- **方法论驱动**：写决策树、判断条件、攻击策略，而非工具调用清单
- **渐进式披露**：先概述，再分阶段深入
- **包含实际命令示例**：用代码块展示，但作为方法论的一部分而非机械步骤
- **交叉引用**：用反引号引用其他技能名，如 `参考 \`jwt-attack-methodology\` 技能`

## 6 description 写法

Description 是 Agent 选择技能的**唯一依据**，必须"主动推销"：

❌ **差的 description**：
```
"SQL 注入测试"
```

✅ **好的 description**：
```
"SQL 注入漏洞检测与利用全流程。当发现用户输入被拼接到数据库查询、
搜索/登录/排序功能可能存在注入点、或需要从注入获取数据库内容时使用。
覆盖联合注入、报错注入、布尔盲注、时间盲注、堆叠注入，以及 WAF 绕过策略"
```

要点：
1. **一句话说明是什么**
2. **列出触发场景**（"当...时使用"）
3. **列出覆盖范围**（"覆盖 X、Y、Z"）

## 7 category 枚举

| 目录 | category 值 | 说明 |
|------|-------------|------|
| `recon/` | recon | 资产发现、信息收集、OSINT、社工 |
| `exploit/` | exploit | Web 漏洞方法论、注入、文件操作、认证绕过、高级利用 |
| `ctf/` | ctf | CTF 竞赛专用方法论、Flag 搜索 |
| `postexploit/` | postexploit | 提权、持久化、凭据收集 |
| `lateral/` | lateral | AD 攻击、内网侦察、多层网络穿透 |
| `cloud/` | cloud | 云元数据利用、IAM 审计、云提权、容器逃逸 |
| `evasion/` | evasion | C2 免杀、Shellcode 加载器、检测对抗 |
| `malware/` | malware | 恶意软件分析、C2 Beacon 提取、沙箱逃逸 |
| `dfir/` | dfir | 取证对抗（内存/磁盘/日志）— 红队视角 |
| `threat-intel/` | threat-intel | IOC 对抗、APT 模拟、威胁猎杀规避 |
| `tool/` | tool | 独立工具使用方法论（nuclei/sqlmap/hashcat 等） |
| `general/` | general | 红队评估、报告生成、供应链审计 |
| `ai-security/` | ai-security | 模型安全、Prompt 注入、AI 基础设施攻击 |
| `code-audit/` | code-audit | 白盒源码审计（PHP/Java/.NET 等语言） |
| `exploit/network-service/` | exploit | 按端口/协议的网络服务渗透方法论（SMB/FTP/SMTP/DNS/LDAP 等） |
| `mobile/` | mobile | 移动应用渗透（Android/iOS） |
| `hardware/` | hardware | 硬件/物理安全渗透 |

## 8 正文写作要点

### 方法论 vs 工具列表

❌ **工具调用列表**（不要这样写）：
```markdown
1. 使用 scan_dns 扫描子域名
2. 使用 scan_port 扫描端口
3. 使用 poc_web 扫描漏洞
4. 使用 memory_save 保存结果
```

✅ **方法论驱动**（应该这样写）：
```markdown
## Phase 1: 攻击面发现
先确定注入点类型——URL 参数、POST 表单、HTTP Header、Cookie 都可能是入口。
判断方法：在参数值后加单引号 `'`，观察响应变化：
- 报错（含 SQL 语法错误） → 报错注入
- 页面内容变化但无报错 → 布尔盲注
- 无任何变化 → 尝试时间盲注 `sleep(5)`
```

### 使用决策表

当有多个分支时，用表格让 Agent 快速判断：

```markdown
| 发现 | 技术 | 下一步 |
|------|------|--------|
| 报错含 MySQL 语法 | MySQL | UNION SELECT + information_schema |
| 报错含 ORA- | Oracle | UNION SELECT FROM dual |
| 响应时间差异 | 通用 | 时间盲注 benchmark/sleep |
```

### 交叉引用其他技能

```markdown
如果发现 JWT Token，参考 `jwt-attack-methodology` 进行 Token 攻击。
获取 shell 后，参考 `post-exploit-linux` 或 `post-exploit-windows` 进行后渗透。
```

## 9 完整示例

<details>
<summary>XSS 方法论（简化示例）</summary>

```markdown
---
name: xss-methodology
description: "XSS 跨站脚本漏洞检测与利用。当发现用户输入被回显到页面、
需要测试反射型/存储型/DOM 型 XSS、或需要绕过 WAF/CSP 时使用"
metadata:
  tags: "xss,cross-site-scripting,反射型,存储型,dom,csp绕过"
  category: "漏洞利用"
---

# XSS 检测与利用方法论

## Phase 1: 注入点定位
找到用户输入回显的位置，判断上下文：
| 回显位置 | Payload 方向 |
|----------|-------------|
| HTML 标签之间 | `<script>alert(1)</script>` |
| HTML 属性值内 | `" onmouseover="alert(1)` |
| JS 代码内 | `';alert(1)//` |
| URL 参数回显 | 反射型 XSS |

## Phase 2: 类型确认
- 输入立即回显 → 反射型
- 输入后在其他页面出现 → 存储型
- 仅在前端 JS 处理 → DOM 型（查看 document.location 等 source）

## Phase 3: 绕过策略
...（WAF 绕过、CSP 绕过、编码绕过）

## 注意事项
- 存储型 XSS 风险最高（影响所有访问者）
- DOM XSS 服务端看不到 payload，需要分析前端 JS
```
</details>

## 10 检查清单

提交 Skill 前，请确认：

- [ ] 目录名与 `name` 字段一致
- [ ] `description` 包含触发场景和覆盖范围（不只是功能名称）
- [ ] `tags` 包含关键词
- [ ] `category` 是规范的枚举值
- [ ] 正文 < 500 行
- [ ] 正文是方法论（有决策树/判断条件），不是工具调用清单
- [ ] 超过 500 行的内容已拆分到 `references/` 子目录，SKILL.md 中有 `→ 读 references/xxx.md` 指针
- [ ] `references/` 文件命名语义化（如 `injection-bypass.md`），独立可读
- [ ] ⛔必读 标记仅用于体量小且普遍适用的 reference，非所有文件都标必读（见 2.3 ⛔必读标记规范）
- [ ] 没有使用 `{{target}}` 等模板变量
- [ ] 有交叉引用到相关技能（如适用）

---

# Vuln 漏洞库编写规范

## 1 概述

每条漏洞是一个 Markdown 文件，使用 **YAML 前言 + Markdown 正文** 的格式。每个文件对应一个具体漏洞（通常是一个 CVE/CNVD 编号），提供可直接使用的利用信息。

**与 Skill 的定位区别**：
- **Vuln（本节）**= 数据层，回答"用什么打"——影响版本、PoC 代码、具体利用步骤
- **Skill（`skills/postexploit/`）**= 后渗透层，回答"进去之后怎么搞"——提权、持久化、凭据提取、横向移动

**如何选择写 Skill 还是 Vuln：**

| 你要写的内容 | 应该放在 | 示例 |
|-------------|---------|------|
| 某个 CVE 的具体 PoC 和利用步骤 | `Vuln/<category>/<product>/` | CVE-2024-23897 Jenkins 任意文件读取的 PoC |
| 获取权限后的后利用（提权、凭据提取、持久化、横向移动） | `skills/postexploit/*-tactics/` | Harbor 拿到 admin 后创建 Robot Account 持久化、篡改镜像供应链攻击 |

简单判断：**如果内容围绕一个 CVE 编号展开，写 Vuln；如果内容围绕一个产品展开（尤其涉及后利用），写 Skill。**

## 2 目录结构

```
Vuln/
├── ai/                       # AI 相关产品
│   ├── comfyui/
│   │   ├── CVE-2025-67303.md
│   │   └── CVE-2026-22777.md
│   └── dify/
│       └── DIFY-SSRF-RCE.md
├── cloud/                    # 云平台
├── middleware/                # 中间件（ActiveMQ、Nacos、Jenkins 等）
│   ├── nacos/
│   │   ├── CVE-2021-29441.md
│   │   ├── CVE-2021-29442.md
│   │   ├── NACOS-AUTH-BYPASS.md
│   │   └── NACOS-DESER-RCE.md
│   └── ...
├── network/                  # 网络设备
└── web/                      # Web 应用
```

### 目录规则

- **一级目录**按攻击面分类：`ai/`、`cloud/`、`middleware/`、`network/`、`web/`
- **二级目录**按产品名（小写连字符）：`nacos/`、`grafana/`、`jenkins/`
- **文件名**用漏洞 ID 大写：`CVE-2021-29441.md`；无 CVE 编号的用 `产品-漏洞类型` 格式：`NACOS-DESER-RCE.md`

### 分类选择

| 一级目录 | 什么产品放这里 | 示例 |
|----------|--------------|------|
| `ai/` | AI/ML 平台、LLM 应用 | ComfyUI、Dify、LangFlow、AnythingLLM |
| `cloud/` | 云服务、云原生基础设施 | AWS API Gateway、K8s |
| `middleware/` | 中间件、数据库、消息队列、CI/CD | Nacos、ActiveMQ、Jenkins、Grafana、Redis |
| `network/` | 路由器、交换机、VPN、防火墙 | 安恒网关、Ivanti |
| `web/` | Web 应用、CMS、管理面板 | WordPress、1Panel、OFBiz |

边界模糊时（如 Harbor 既是中间件也是云原生），优先放 `middleware/`。

## 3 文件格式

### YAML 前言（必填）

```yaml
---
id: CVE-2021-29441                    # 漏洞 ID（CVE/CNVD 编号或自定义 ID）
title: Nacos认证绕过漏洞              # 中文标题，简明描述漏洞
product: nacos                         # 产品名（小写，与目录名一致）
vendor: Alibaba                        # 厂商名
version_affected: "<1.4.1"             # 影响版本范围
severity: HIGH                         # 严重性：CRITICAL / HIGH / MEDIUM / LOW
tags: [auth_bypass, 无需认证]          # 标签数组，中英文混合
fingerprint: ["Nacos"]                 # 指纹关键词数组，用于产品识别
---
```

### 字段说明

| 字段 | 必填 | 类型 | 说明 |
|------|------|------|------|
| `id` | ✅ | string | CVE/CNVD 编号，或自定义 `产品-漏洞类型` 格式（如 `NACOS-DESER-RCE`） |
| `title` | ✅ | string | 中文标题，格式：`产品名+漏洞类型+（CVE编号）` |
| `product` | ✅ | string | 产品名小写，与二级目录名一致 |
| `vendor` | ✅ | string | 厂商/组织名 |
| `version_affected` | ✅ | string | 影响版本范围，如 `"<1.4.1"`、`"<=5.18.2"`、`"2.0.0-2.3.5"` |
| `severity` | ✅ | enum | `CRITICAL` / `HIGH` / `MEDIUM` / `LOW`（必须大写） |
| `tags` | ✅ | array | 漏洞特征标签：`rce`、`auth_bypass`、`sqli`、`ssrf`、`deserialization`、`无需认证`、`需要认证` 等 |
| `fingerprint` | 推荐 | array | 产品指纹关键词，用于自动匹配（如 HTTP 响应中的特征字符串） |

### severity 选择标准

| 级别 | 条件 |
|------|------|
| `CRITICAL` | 无需认证 + RCE，或无需认证 + 完整数据泄露 |
| `HIGH` | 需要认证的 RCE，或无需认证的敏感信息泄露/权限绕过 |
| `MEDIUM` | 需要特定条件的利用，或信息泄露范围有限 |
| `LOW` | 影响较小，利用条件苛刻 |

## 4 正文结构

按以下章节顺序编写，章节名用二级标题（`##`）：

```markdown
## 漏洞描述

简明描述漏洞原理，2-3 句话。说明攻击者能做什么，为什么能做到。

## 影响版本

- 产品名 < x.y.z
- 产品名 x.a.b - x.c.d

## 前置条件

- 是否需要认证
- 需要访问哪些端口/接口
- 其他利用条件

## 利用步骤

按顺序描述利用过程，每步一个编号。保持简洁，
复杂的 payload 放在下方的 Payload 章节。

## Payload

实际可用的 PoC 代码，用代码块标注语言类型。
优先提供 curl/Python，便于直接复制使用。

## 验证方法

如何确认漏洞已成功利用。

## 修复建议

升级版本、配置缓解措施等（可选但推荐）。
```

### 正文要求

- **可直接使用**：Payload 应该是复制即用的，不要用 `<替换为你的IP>` 这种占位，用 `target`、`ATTACKER_IP` 等一眼能看出需要替换的通用占位词
- **语言标注**：代码块标注语言（`bash`、`python`、`http`、`sql`）
- **一个文件一个漏洞**：不要在一个文件里写多个不相关的 CVE。同一产品的关联漏洞链（如认证绕过 + RCE）可以在一个文件里写组合利用
- **不写方法论**：不要写"先扫描端口，再判断版本"这种流程。方法论属于 Skill，Vuln 只写这个漏洞本身的 PoC

## 5 完整示例

```markdown
---
id: CVE-2021-29441
title: Nacos认证绕过漏洞（CVE-2021-29441）
product: nacos
vendor: Alibaba
version_affected: "<1.4.1"
severity: HIGH
tags: [auth_bypass, 无需认证]
fingerprint: ["Nacos"]
---

## 漏洞描述

Nacos 1.4.1 之前的版本中，服务端检查请求头 User-Agent 是否为
Nacos-Server，匹配则跳过认证。攻击者设置该请求头即可访问所有 API。

## 影响版本

- Nacos < 1.4.1

## 前置条件

- 无需认证
- 只需添加 `User-Agent: Nacos-Server` 头

## 利用步骤

1. 发送带伪造 User-Agent 头的 GET 请求列出用户
2. 发送 POST 请求创建新用户
3. 使用创建的用户登录控制台

## Payload

​```http
# 列出所有用户
GET /nacos/v1/auth/users?pageNo=1&pageSize=9 HTTP/1.1
Host: target:8848
User-Agent: Nacos-Server

# 创建新用户
POST /nacos/v1/auth/users?username=vulhub&password=vulhub HTTP/1.1
Host: target:8848
User-Agent: Nacos-Server
​```

## 验证方法

​```bash
# 使用创建的账号登录 http://target:8848/nacos/
# 账号: vulhub / vulhub
​```

## 修复建议

1. 升级 Nacos 至 1.4.1+
2. 移除 User-Agent 认证绕过的特殊处理
3. 对所有 API 接口启用认证
```

## 6 检查清单

提交 Vuln 前，请确认：

- [ ] 文件放在正确的分类目录下（`Vuln/<category>/<product>/`）
- [ ] 文件名为漏洞 ID 大写（`CVE-2021-29441.md`）或 `产品-漏洞类型` 格式
- [ ] YAML 前言包含所有必填字段（id、title、product、vendor、version_affected、severity、tags）
- [ ] `severity` 为大写枚举值（CRITICAL/HIGH/MEDIUM/LOW）
- [ ] `product` 与二级目录名一致
- [ ] 正文包含：漏洞描述、影响版本、前置条件、利用步骤、Payload
- [ ] Payload 是可直接使用的代码（标注了语言类型）
- [ ] 一个文件只写一个漏洞（关联漏洞链除外）
- [ ] 没有写方法论内容（方法论属于 Skill）

---

# 提交流程

1. Fork 本仓库
2. 在对应目录下创建文件，遵循上述规范
3. 按对应的检查清单（Skill 第 10 节 / Vuln 第 6 节）自查
4. 若新增分类，需同步更新 `CONTRIBUTING.md` 中的目录结构和 category 枚举
5. 提交 PR，标题格式：`[Skill] 添加 xxx` 或 `[Vuln] 添加 xxx`

---

# Skill 质量基准测试

## 1 概述

每个 Skill 可以包含 `evals/evals.json` 定义测试场景，用于衡量 Skill 对 AI Agent 的实际帮助程度。

基准测试通过 A/B 对比实现：
- **with_skill**: Agent 加载 Skill 内容后回答
- **without_skill**: Agent 不加载 Skill（baseline）回答
- 对比两组的断言通过率、耗时、token 用量

## 2 evals.json 格式

```json
{
  "skill_name": "sql-injection-methodology",
  "evals": [
    {
      "id": 1,
      "name": "sqli-detection-basic",
      "prompt": "你在测试一个 Web 应用...",
      "expected_output": "系统化的 SQL 注入检测流程",
      "expectations": [
        "UNION SELECT|UNION 注入|联合查询",
        "时间盲注|SLEEP|BENCHMARK|time-based",
        "布尔盲注|Boolean|1=1"
      ]
    }
  ]
}
```

**expectations 格式**：
- 用 `|` 分隔关键词替代项（满足任一即通过）
- 示例：`"UNION SELECT|联合查询"` → 输出包含 "UNION SELECT" 或 "联合查询" 即通过

## 3 运行基准测试

```bash
# 测试单个 Skill
python scripts/bench-skill.py --skill skills/exploit/sql-injection-methodology

# 多次运行（方差分析）
python scripts/bench-skill.py --skill skills/exploit/sql-injection-methodology --runs 3

# 测试所有有 evals 的 Skills
python scripts/bench-skill.py --all

# 使用 LLM 评分（更准确，但消耗 token）
python scripts/grade_eval.py --workspace benchmarks/sql-injection-methodology/iteration-xxx
```

需要安装 Claude CLI (`claude -p`)。输出保存到 `benchmarks/<skill-name>/` 目录。

## 4 输出格式

兼容 skill-creator 的 benchmark.json schema：
- `benchmark.json` — 结构化数据（pass_rate, timing, tokens, delta）
- `benchmark.md` — 人类可读的对比报告
- 每个 run 的 `grading.json` — 逐条断言评估结果

可直接使用 skill-creator 的 `generate_review.py` 在浏览器中查看结果。

---

# 常见问题

**Q: Skill 的 prompt 可以引用外部工具吗？**
A: 可以。在正文中写 `xxx` 工具名，当消费端程序实现工具自动调用后，Agent 即可自动匹配并执行对应工具。（此功能依赖消费入口程序实现，当前阶段仅作为 Skill 编写约定。）

---
