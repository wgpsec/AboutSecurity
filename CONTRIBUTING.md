# AboutSecurity 资源贡献规范

本文档定义了 `Tools/` 和 `Skills/` 目录下 YAML 文件的编写规范，供社区贡献者和 AI 参考。

---

## 目录结构

```
AboutSecurity/
├── Tools/                    # 外部工具声明式配置
│   ├── scan/                 # 资产探测类
│   ├── osint/                # 情报搜索类
│   ├── poc/                  # 漏洞扫描类
│   ├── brute/                # 爆破/Fuzz 类
│   ├── postexploit/          # 后渗透类
│   └── util/                 # 辅助工具类
├── Skills/                   # AI Agent 技能方法论
│   ├── recon/                # 侦察类 (5)
│   ├── exploit/              # 漏洞利用类 (26)
│   ├── ctf/                  # CTF 竞赛类 (5)
│   ├── postexploit/          # 后渗透类 (6)
│   ├── lateral/              # 内网渗透类 (3)
│   ├── cloud/                # 云环境类 (2)
│   └── general/              # 综合类 (4)
└── manifest.yaml
```

---

# 一、Tools 外部工具编写规范

## 1.1 概述

每个 YAML 文件声明一个外部命令行工具。Kitsune AI Agent 读取这些定义后，可自动调用对应工具并解析输出。

**核心原则**：定义好输入（parameters），Kitsune 才能正确调用；定义好输出（output + findings_mapping），Kitsune 才能正确入库。

## 1.2 文件命名

```
{工具名}.yaml
```

示例：`nmap-scan.yaml`、`subfinder.yaml`、`nuclei-custom.yaml`

## 1.3 完整字段说明

```yaml
# ============================================================
# 基本信息（必填）
# ============================================================
id: ext_工具名                  # 工具唯一标识，必须以 ext_ 开头
name: 工具显示名称               # 中文名，给用户看的
description: "工具功能描述"       # AI 用这段文字决定是否调用此工具，写清楚能做什么
homepage: "https://github.com/xxx/xxx"  # 工具官网或 GitHub 地址，方便用户了解和安装
category: scan                  # 分类，见下方枚举
binary: nmap                    # 可执行文件名（从 PATH 查找）
binary_path: ""                 # 可选：绝对路径，如 /usr/local/bin/nmap
version_cmd: "nmap --version"   # 可选：版本检测命令

# ============================================================
# 安装方式（推荐填写，便于工具管理页面一键复制安装命令）
# ============================================================
# 支持的安装方式：go / brew / pip / apt / docker / f8x / manual
# 至少填写一种，多填更好（覆盖不同平台/偏好）
install:
  go: "go install github.com/xxx/xxx@latest"      # Go 安装
  brew: "brew install xxx"                         # Homebrew (macOS)
  pip: "pip3 install xxx"                          # Python PyPI
  apt: "sudo apt install -y xxx"                   # Debian/Ubuntu
  docker: "docker pull xxx:latest"                 # Docker 镜像
  f8x: "-xxx"                                      # f8x 自动化安装脚本标志
  manual: "https://github.com/xxx/xxx/releases"    # 手动下载页面

# ============================================================
# 参数定义（必填，至少一个）
# ============================================================
# AI Agent 看到这些参数，并根据 description 决定传什么值
parameters:
  - name: target                # 参数名，Go 模板变量名
    type: string                # 类型：string / integer / boolean
    description: "扫描目标"      # AI 读这段来理解参数用途
    required: true              # 是否必填
  - name: ports
    type: string
    description: "端口范围"
    default: "1-10000"          # 可选：默认值，AI 不传时自动填入
    enum: ["syn", "tcp"]        # 可选：枚举约束，AI 只能从中选择

# ============================================================
# 命令模板（必填）
# ============================================================
# 使用 Go text/template 语法，每行一组参数
# 可用变量：所有 parameters 的 name + {{.OutputFile}} + {{.WorkDir}}
command_template: |
  -sS
  -p {{.ports}}
  -oG {{.OutputFile}}
  --open
  {{.target}}

# 实际执行的命令 = binary + command_template 渲染结果
# 例如: nmap -sS -p 1-10000 -oG /tmp/xxx/output.txt --open 192.168.1.0/24

# ============================================================
# 输出解析（必填）
# ============================================================
output:
  mode: file                    # stdout / file / json_file
  file_pattern: "{{.OutputFile}}" # mode=file 时的文件路径模板
  parser: line                  # 解析器类型，见 1.4 节

  # 解析器配置（按 parser 类型选其一）
  line:                         # parser: line 时
    skip_prefix: "#"            # 跳过以此开头的行
    skip_empty: true            # 跳过空行
    split: " "                  # 分隔符
    fields:                     # 按分隔后的索引映射字段名
      - name: host
        index: 0
      - name: port
        index: 1

# ============================================================
# 结果映射（必填）
# ============================================================
# 将解析出的每条记录映射为 Kitsune Finding 入库
findings_mapping:
  type: info                    # Finding 类型
  severity: info                # 严重程度：info / low / medium / high / critical
  target_field: host            # 哪个解析字段作为 Finding.Target
  detail_template: "{{.host}}:{{.port}} open"  # 详情模板

# ============================================================
# 约束条件（可选）
# ============================================================
constraints:
  timeout: 300s                 # 超时时间（Go duration 格式）
  requires_root: false          # 是否需要 root 权限
  max_concurrent: 2             # 最大并发数
  proxy_flag: "--proxy"         # 代理参数名（Kitsune 自动注入代理地址）
```

## 1.4 四种输出解析器

### line — 按行分割（最常用）

适用于每行一条结果、字段用固定分隔符隔开的输出。

```yaml
output:
  parser: line
  line:
    skip_prefix: "#"          # 跳过注释行
    skip_empty: true
    split: ","                # 分隔符：空格、逗号、制表符等
    fields:
      - { name: ip, index: 0 }
      - { name: port, index: 1 }
      - { name: service, index: 2 }
```

若不配置 `line` 子项，则每行整体作为一个 `target` 字段。

### json — JSON 输出

适用于工具输出 JSON 格式（如 httpx -json、nuclei -json）。

```yaml
output:
  parser: json
  json:
    results_path: "results"   # JSON 数组路径（点分隔），如 "data.hosts"
    fields:
      - { name: host, path: "host" }
      - { name: port, path: "port" }
      - { name: url, path: "url" }
```

### regex — 正则提取

适用于非结构化输出，需要用正则捕获关键信息。

```yaml
output:
  parser: regex
  regex:
    pattern: 'Found open port (\d+)/tcp on (\S+)'
    groups: [port, host]      # 按捕获组顺序命名
```

### grepable — nmap -oG 专用

```yaml
output:
  parser: grepable
  grepable:
    host_regex: 'Host:\s+(\S+)'
    port_regex: '(\d+)/open'
```

## 1.5 category 枚举

| 值 | 说明 | 示例工具 |
|---|---|---|
| `scan` | 资产探测 | nmap, masscan, rustscan |
| `osint` | 情报搜索 | subfinder, amass, theHarvester |
| `poc` | 漏洞扫描 | nuclei, xray |
| `brute` | 爆破/Fuzz | dirsearch, ffuf, hydra |
| `postexploit` | 后渗透 | linpeas, winpeas |
| `util` | 辅助工具 | curl, jq, whatweb |

## 1.6 command_template 模板语法

使用 Go `text/template`，支持条件判断：

```yaml
command_template: |
  {{if eq .scan_type "syn"}}-sS{{else if eq .scan_type "udp"}}-sU{{else}}-sT{{end}}
  -p {{.ports}}
  {{if .wordlist}}-w {{.wordlist}}{{end}}
  -o {{.OutputFile}}
  {{.target}}
```

**内置变量**（无需在 parameters 中定义）：
- `{{.OutputFile}}` — Kitsune 自动创建的临时输出文件路径
- `{{.WorkDir}}` — Kitsune 自动创建的临时工作目录

## 1.7 完整示例

<details>
<summary>subfinder — 子域名发现</summary>

```yaml
id: ext_subfinder
name: Subfinder 子域名发现
description: "使用 subfinder 被动发现子域名，速度快、覆盖广，适合大规模侦察"
homepage: "https://github.com/projectdiscovery/subfinder"
category: scan
binary: subfinder
version_cmd: "subfinder -version"
install:
  go: "go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest"
  brew: "brew install subfinder"

parameters:
  - name: target
    type: string
    description: "目标域名"
    required: true

command_template: |
  -d {{.target}}
  -silent
  -o {{.OutputFile}}

output:
  mode: file
  file_pattern: "{{.OutputFile}}"
  parser: line

findings_mapping:
  type: info
  severity: info
  target_field: target
  detail_template: "subdomain: {{.target}}"

constraints:
  timeout: 120s
```
</details>

<details>
<summary>nuclei — 漏洞扫描（JSON 输出）</summary>

```yaml
id: ext_nuclei
name: Nuclei 漏洞扫描
description: "使用 nuclei 进行基于模板的漏洞扫描，支持数千个 CVE 和暴露检测模板"
homepage: "https://github.com/projectdiscovery/nuclei"
category: poc
binary: nuclei
version_cmd: "nuclei -version"
install:
  go: "go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest"
  brew: "brew install nuclei"

parameters:
  - name: target
    type: string
    description: "扫描目标 URL"
    required: true
  - name: severity
    type: string
    description: "严重等级过滤"
    default: "low,medium,high,critical"
    enum: ["info", "low", "medium", "high", "critical", "low,medium,high,critical"]
  - name: tags
    type: string
    description: "模板标签过滤（如 cve,exposed）"

command_template: |
  -u {{.target}}
  -severity {{.severity}}
  {{if .tags}}-tags {{.tags}}{{end}}
  -jsonl
  -o {{.OutputFile}}
  -silent

output:
  mode: file
  file_pattern: "{{.OutputFile}}"
  parser: json
  json:
    fields:
      - { name: host, path: "host" }
      - { name: template_id, path: "template-id" }
      - { name: severity, path: "info.severity" }
      - { name: name, path: "info.name" }
      - { name: matched_at, path: "matched-at" }

findings_mapping:
  type: vulnerability
  severity: medium
  target_field: host
  detail_template: "[{{.severity}}] {{.name}} ({{.template_id}}) at {{.matched_at}}"

constraints:
  timeout: 600s
  max_concurrent: 1
```
</details>

<details>
<summary>ffuf — Web Fuzz</summary>

```yaml
id: ext_ffuf
name: ffuf Web Fuzz
description: "使用 ffuf 进行高速 Web 路径和参数 Fuzz"
homepage: "https://github.com/ffuf/ffuf"
category: brute
binary: ffuf
version_cmd: "ffuf -V"
install:
  go: "go install github.com/ffuf/ffuf/v2@latest"
  brew: "brew install ffuf"

parameters:
  - name: target
    type: string
    description: "目标 URL，用 FUZZ 标记注入点，如 http://example.com/FUZZ"
    required: true
  - name: wordlist
    type: string
    description: "字典文件路径"
    required: true
  - name: filter_code
    type: string
    description: "过滤 HTTP 状态码"
    default: "404"

command_template: |
  -u {{.target}}
  -w {{.wordlist}}
  -fc {{.filter_code}}
  -o {{.OutputFile}}
  -of json
  -s

output:
  mode: file
  file_pattern: "{{.OutputFile}}"
  parser: json
  json:
    results_path: "results"
    fields:
      - { name: url, path: "url" }
      - { name: status, path: "status" }
      - { name: length, path: "length" }
      - { name: words, path: "words" }

findings_mapping:
  type: info
  severity: info
  target_field: url
  detail_template: "{{.url}} [{{.status}}] length={{.length}}"

constraints:
  timeout: 300s
  max_concurrent: 2
```
</details>

## 1.8 检查清单

提交 Tool YAML 前，请确认：

- [ ] `id` 以 `ext_` 开头，全局唯一
- [ ] `description` 清楚说明工具能做什么（AI 据此决定是否调用）
- [ ] `homepage` 填写工具的 GitHub 地址或官网，方便用户了解和安装
- [ ] `install` 至少填写一种安装方式（go/brew/pip/apt/docker/f8x/manual）
- [ ] 至少有一个 `required: true` 的 `target` 参数
- [ ] `command_template` 渲染后是合法的命令行
- [ ] `output.parser` 与工具实际输出格式匹配
- [ ] `findings_mapping.detail_template` 引用的字段在解析器中存在
- [ ] `binary` 是工具的实际可执行文件名
- [ ] 在本机安装该工具后实际测试通过

---

# 二、Skills 技能方法论编写规范

## 2.1 概述

每个 Skill 是一个独立目录，包含一个 `SKILL.md` 文件。SKILL.md 使用 **YAML 前言 + Markdown 正文** 的格式，正文是方法论驱动的渗透指南，而非工具调用列表。

Kitsune Agent 通过 `description` 字段匹配用户意图，读取正文作为上下文指导执行。

**核心原则**：
- **description 是触发器** — Agent 通过 description 决定是否加载此 Skill，务必写清楚触发场景
- **正文是方法论** — 教 Agent "怎么思考"，而非机械地列出工具调用步骤
- **解释 why** — 说明为什么用某种方法，而非写死 MUST/NEVER 规则
- **不使用模板变量** — `{{target}}` 等占位符不会被替换，不要使用

## 2.2 目录结构

```
Skills/
├── recon/                    # 侦察类
│   └── recon-full/
│       └── SKILL.md
├── exploit/                  # 漏洞利用类
│   └── sql-injection-methodology/
│       └── SKILL.md
├── ctf/                      # CTF 竞赛类
├── postexploit/              # 后渗透类
├── lateral/                  # 内网渗透类
├── cloud/                    # 云环境类
└── general/                  # 综合类
```

每个技能一个目录（将来可在目录内添加 `references/` 补充材料）。

## 2.3 SKILL.md 格式

```markdown
---
name: skill-name
description: "一段详细的、带触发场景的描述。当遇到 X 情况、发现 Y 特征、需要做 Z 测试时使用。覆盖 A、B、C 方面"
metadata:
  tags: "tag1,tag2,tag3,关键词"
  difficulty: "easy|medium|hard"
  icon: "🔍"
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

## 2.4 字段说明

### 前言字段

| 字段 | 必填 | 说明 |
|------|------|------|
| `name` | ✅ | 技能唯一标识，英文短横线命名，与目录名一致 |
| `description` | ✅ | **最重要的字段**。详细描述触发场景和覆盖范围（见 2.5） |
| `metadata.tags` | ✅ | 逗号分隔的标签，包含中英文关键词便于搜索 |
| `metadata.difficulty` | ✅ | `easy` / `medium` / `hard` |
| `metadata.icon` | 可选 | Emoji 图标 |
| `metadata.category` | ✅ | 分类名（见 2.6） |

### 正文要求

- **< 500 行**（超过说明需要拆分）
- **方法论驱动**：写决策树、判断条件、攻击策略，而非工具调用清单
- **渐进式披露**：先概述，再分阶段深入
- **包含实际命令示例**：用代码块展示，但作为方法论的一部分而非机械步骤
- **交叉引用**：用反引号引用其他技能名，如 `参考 \`jwt-attack-methodology\` 技能`

## 2.5 description 写法

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

## 2.6 category 枚举

| 目录 | category 值 | 说明 |
|------|-------------|------|
| `recon/` | 侦察 | 资产发现、信息收集、OSINT、社工 |
| `exploit/` | 漏洞利用 | Web 漏洞方法论、注入、文件操作、认证绕过 |
| `ctf/` | CTF | CTF 竞赛专用方法论、Flag 搜索 |
| `postexploit/` | 后渗透 | 提权、持久化、凭据收集、横向移动 |
| `lateral/` | 内网渗透 | AD 攻击、内网侦察、多层网络穿透 |
| `cloud/` | 云环境 | 云元数据利用、IAM 审计、云提权 |
| `general/` | 综合 | 红队评估、报告生成、供应链审计 |

## 2.7 正文写作要点

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

## 2.8 完整示例

<details>
<summary>XSS 方法论（简化示例）</summary>

```markdown
---
name: xss-methodology
description: "XSS 跨站脚本漏洞检测与利用。当发现用户输入被回显到页面、
需要测试反射型/存储型/DOM 型 XSS、或需要绕过 WAF/CSP 时使用"
metadata:
  tags: "xss,cross-site-scripting,反射型,存储型,dom,csp绕过"
  difficulty: "medium"
  icon: "💉"
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

## 2.9 检查清单

提交 Skill 前，请确认：

- [ ] 目录名与 `name` 字段一致
- [ ] `description` 包含触发场景和覆盖范围（不只是功能名称）
- [ ] `tags` 包含中英文关键词
- [ ] `category` 是规范的枚举值
- [ ] 正文 < 500 行
- [ ] 正文是方法论（有决策树/判断条件），不是工具调用清单
- [ ] 没有使用 `{{target}}` 等模板变量
- [ ] 有交叉引用到相关技能（如适用）
- [ ] `difficulty` 与实际复杂度匹配

---

# 三、提交流程

1. Fork 本仓库
2. 在对应目录创建 YAML 文件
3. 按上述规范检查清单自查
4. 提交 PR，标题格式：`[Tool] 添加 xxx` 或 `[Skill] 添加 xxx`

---

# 四、Skill 质量基准测试

## 4.1 概述

每个 Skill 可以包含 `evals/evals.json` 定义测试场景，用于衡量 Skill 对 AI Agent 的实际帮助程度。

基准测试通过 A/B 对比实现：
- **with_skill**: Agent 加载 Skill 内容后回答
- **without_skill**: Agent 不加载 Skill（baseline）回答
- 对比两组的断言通过率、耗时、token 用量

## 4.2 evals.json 格式

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

## 4.3 运行基准测试

```bash
# 测试单个 Skill
python scripts/bench-skill.py --skill Skills/exploit/sql-injection-methodology

# 多次运行（方差分析）
python scripts/bench-skill.py --skill Skills/exploit/sql-injection-methodology --runs 3

# 测试所有有 evals 的 Skills
python scripts/bench-skill.py --all

# 使用 LLM 评分（更准确，但消耗 token）
python scripts/grade_eval.py --workspace benchmarks/sql-injection-methodology/iteration-xxx
```

需要安装 Claude CLI (`claude -p`)。输出保存到 `benchmarks/<skill-name>/` 目录。

## 4.4 输出格式

兼容 skill-creator 的 benchmark.json schema：
- `benchmark.json` — 结构化数据（pass_rate, timing, tokens, delta）
- `benchmark.md` — 人类可读的对比报告
- 每个 run 的 `grading.json` — 逐条断言评估结果

可直接使用 skill-creator 的 `generate_review.py` 在浏览器中查看结果。

---

# 五、常见问题

**Q: 工具输出没有固定格式怎么办？**
A: 使用 `parser: regex` 用正则提取关键信息，或使用 `mode: stdout` + `parser: line` 逐行处理。

**Q: 工具需要 root 权限怎么标注？**
A: 在 `constraints.requires_root: true` 标注，同时在 `description` 中说明。

**Q: 一个工具有多种使用场景，写几个 YAML？**
A: 建议拆成多个，如 `nmap-scan.yaml`（端口扫描）、`nmap-vuln.yaml`（漏洞脚本扫描），各有不同的 parameters 和 command_template。

**Q: Skill 的 prompt 可以引用外部工具吗？**
A: 可以。直接写 `ext_xxx` 工具名，Agent 会自动调用。
