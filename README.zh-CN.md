[English](README.md) | 中文文档

# AboutSecurity

渗透测试知识库，以 AI Agent 可执行的格式沉淀安全方法论。

## 核心模块

**Skills/** — 184 个技能方法论，覆盖侦察到后渗透全链路

- `cloud/` — 云环境（Docker逃逸、K8s攻击链、AWS IAM、阿里云、腾讯云、Serverless）
- `ctf/` — CTF竞赛（Web解题、逆向、PWN、密码学、取证、AI/ML）
- `dfir/` — 取证对抗（内存取证与反取证、磁盘取证与反取证、日志逃逸）
- `evasion/` — 免杀对抗（C2框架、Shellcode生成、安全研究）
- `exploit/` — 漏洞利用（60+skills，按子分类组织）
  - `web-method/` — Web 通用方法论（注入、XSS、SSRF、SSTI、文件上传、反序列化、WAF绕过…）
  - `product-vuln/` — 特定产品漏洞方法论（Nacos、Jenkins、Grafana、GeoServer、中间件…）
  - `advanced/` — 高级利用（HTTP走私、竞态条件、供应链攻击、OT/ICS、加密攻击）
  - `auth/` — 认证授权（JWT、OAuth/SSO、IDOR、CORS、CSRF、Cookie分析）
- `general/` — 综合（报告生成、供应链审计、移动后端API）
- `lateral/` — 横向移动（AD域攻击、NTLM中继、数据库横向、Kerberoasting、ACL滥用）
- `malware/` — 恶意软件（样本分析方法论、C2 Beacon配置提取、沙箱逃逸实现）
- `postexploit/` — 后渗透（Linux/Windows提权、持久化、凭据窃取）
- `recon/` — 侦察（子域名枚举、被动信息收集、JS API提取）
- `threat-intel/` — 威胁情报（IOC对抗、APT模拟、威胁猎杀规避）
- `ai-security/` — AI 安全（Prompt 注入、模型越狱、Prompt 泄露、Agent 攻击链）
- `code-audit/` — 代码审计（PHP 8-Skill 体系、Java 8-Skill 体系，覆盖注入/文件/序列化/认证/框架/利用链）
- `tool/` — 工具使用（fscan、nuclei、sqlmap、msfconsole、ffuf、hashcat）

**Dic/** — 字典库（全小写连字符命名，每目录带 `_meta.yaml` 元数据）

- `auth/` — 用户名/密码（含复杂度规则密码、WPA、拼音姓名）
- `network/` — DNS服务器、排除IP段
- `port/` — 按服务分类的爆破字典（mysql、redis、ssh 等 19 种）
- `regular/` — 通用字典（数字、字母、地址、关键词）
- `web/` — Web 目录、API参数、中间件、上传绕过、Webshell、HTTP头

**Payload/** — 攻击载荷（全小写连字符命名，每目录带 `_meta.yaml` 元数据）

- `sqli/`、`xss/`、`ssrf/`、`xxe/`、`lfi/`、`rce/`、`upload/`、`cors/`、`hpp/`、`format/`、`ssi/`、`email/`、`access-bypass/`、`prompt-injection/`

**Vuln/** — 600+ 条漏洞库，按产品分类的结构化漏洞数据

- `ai/` — AI 相关（ComfyUI、Dify、LangFlow、AnythingLLM 等）
- `cloud/` — 云平台（AWS API Gateway 等）
- `middleware/` — 中间件（ActiveMQ、Nacos、Grafana、Jenkins、RocketMQ 等 394 条）
- `network/` — 网络设备（路由器、交换机等）
- `web/` — Web 应用（1Panel、WordPress、OFBiz 等）

**Tools/** — 外部工具声明式配置（程序化编排框架使用）

- `scan/`、`fuzz/`、`osint/`、`poc/`、`brute/`、`postexploit/`
- 详见 [Tools/README.md](./Tools/README.md)

> **Tools/ vs skills/tool/ 的区别**：`Tools/` 下的 YAML 是面向**程序化工具编排框架**的结构化接口定义（参数类型、命令模板、输出解析器），适合自动化引擎调用；`skills/tool/` 下的 SKILL.md 是面向 **LLM Agent** 的自然语言方法论（何时用、怎么选参数、结果怎么判断）。如果你只使用 Claude Code 等 LLM Agent，关注 `skills/tool/` 即可。

> **skills/exploit/product-vuln/ vs Vuln/ 的区别**：两者针对同一产品但定位不同。`product-vuln/` 下的 Skill 是**方法论层**——攻击决策树、多 CVE 优先级编排、后利用技巧（提权/持久化/凭据提取）；`Vuln/` 下的条目是**数据层**——每条漏洞的影响版本、PoC 代码、具体利用步骤。简单来说：**Skill 告诉你"怎么打"，Vuln 告诉你"用什么打"**。AI 会先读 Skill 了解整体攻击面，再调 Vuln 拿具体 PoC 去执行。

## 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/your-org/AboutSecurity.git
```

### 2. 同步 Skills 到你的项目

```bash
# 将 184 安全技能同步到你的工作项目中
cd AboutSecurity
./scripts/sync-claude-skills.sh --target /path/to/your-project

# 效果：在目标项目下生成 .claude/skills/<skill-name>/ 软链接
# Claude Code 在该项目中工作时即可自动识别和调用这些技能
```

> 不传 `--target` 则同步到 AboutSecurity 仓库自身（适合直接在本仓库中使用 Agent）。新增或删除 skill 后重新执行一次即可。

### 3. 使用字典与 Payload

字典和 Payload 不需要 sync，在 Agent 对话中直接引用路径即可：

```
"用 /path/to/AboutSecurity/Dic/auth/ 下的字典爆破目标 SSH"
"加载 /path/to/AboutSecurity/Payload/xss/ 的 payload 列表做 fuzz 测试"
```

Agent 通过 Read / Glob 工具直接读取这些文件，只需提供正确的仓库路径。

<details>
<summary><b>概念补充（新手可读）：什么是 Skill？为什么需要同步？</b></summary>

- **Skill** = 一份结构化方法论文件（`SKILL.md`），告诉 AI Agent "遇到 X 场景该怎么做"
- Claude Code 只识别 `.claude/skills/<name>/SKILL.md` 这种扁平结构
- 本仓库按分类嵌套组织（如 `skills/exploit/web-method/sql-injection/SKILL.md`），sync 脚本负责创建软链接实现 嵌套 → 扁平 映射
- 同步后 Agent 会根据对话上下文**自动匹配并加载**相关 Skill，无需手动指定

</details>

### 4. 通过 MCP 服务使用（context1337）(强烈推荐)

如果你希望通过 AI 助手（Claude Code、Cursor、Claude Desktop 等）**自然语言搜索和调用**本仓库的全部资源，可以部署 [context1337](https://github.com/wgpsec/context1337) —— 一个独立的 MCP 资源服务，将 AboutSecurity 从文件仓库转变为可消费的 API（类似 context7，但专为安全领域打造）。

```bash
git clone https://github.com/wgpsec/context1337.git
cd context1337
make run   # 一条命令：克隆数据 + 构建索引 + 启动服务
```

启动后将 MCP 服务添加到你的 AI 工具：

```bash
# Claude Code
claude mcp add aboutsecurity --transport http http://localhost:8088/mcp
```

之后即可用自然语言查询：「搜索 SQL 注入相关资源」「列出所有 XSS payload」「查找 Apache 高危漏洞」等。详见 [context1337 README](https://github.com/wgpsec/context1337)。

---

## 项目 skills 介绍

[skills/README.md](./skills/README.md) 详细介绍了项目的 skills 分类架构、格式规范、Benchmark 测试流程。

## Dic/Payload 命名规范

### 目录命名
- 全小写，连字符分隔：`file-backup/`、`api-param/`、`prompt-injection/`

### 文件命名
- 全英文、小写、连字符分隔
- 无 `Fuzz_` 前缀（历史遗留已清理）
- 示例：`password-top100.txt`、`xss-tag-event-full.txt`、`complex-8char-upper-lower-digit.txt`

### `_meta.yaml` 元数据

每个包含数据文件的目录都有一个 `_meta.yaml`，为 AI 搜索提供结构化元数据：

```yaml
category: auth                     # 顶层分类
subcategory: password              # 子分类（可选）
description: "常见弱口令及按复杂度规则生成的密码字典集合"
tags: "password,弱口令,爆破,brute-force,login,credential"

files:
  - name: top100.txt
    lines: 100
    description: "最常见的100个弱口令"
    usage: "登录爆破初筛、快速验证默认口令"
    tags: "top100,common,weak,弱口令"
```

`description` 和 `usage` 使用中文，`tags` 中英双语。新增字典/payload 文件时，同步更新对应的 `_meta.yaml`。

## 贡献

提交前阅读 [CONTRIBUTING.md](./CONTRIBUTING.md)，包括 Skill 格式规范、Vuln 漏洞库编写规范、references 编写要求、benchmark 测试流程。

## 参考

- https://github.com/anthropics/skills/blob/main/skills/skill-creator/SKILL.md
- https://github.com/ljagiello/ctf-skills
- https://github.com/JDArmy/Evasion-SubAgents
- https://github.com/teamssix/twiki
- https://github.com/yaklang/hack-skills
- https://github.com/mukul975/Anthropic-Cybersecurity-Skills
- https://github.com/Pa55w0rd/secknowledge-skill
- https://github.com/0xShe/PHP-Code-Audit-Skill
- https://github.com/RuoJi6/java-audit-skills
