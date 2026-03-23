---
name: red-team-assessment
description: "红队评估全流程方法论。当需要对目标执行端到端的安全评估（被动侦察→主动侦察→漏洞发现→利用验证→报告输出）时使用。适用于外网打点、安全评估项目、定期渗透测试。本技能是流程编排——具体漏洞利用技术引用其他专项 skills"
metadata:
  tags: "red-team,assessment,渗透测试,安全评估,全流程,外网打点,automation,pentest"
  difficulty: "hard"
  icon: "🔴"
  category: "综合"
---

# 红队评估全流程方法论

本技能是渗透测试的**总流程编排**——不包含具体漏洞利用技术（那些在 exploit/ 的各专项 skill 中），而是指导你按正确的顺序、用正确的策略推进整个评估。

## Phase 1: 被动侦察（零接触）

在不触碰目标的情况下收集情报：

1. **OSINT 搜索引擎**（参考 `passive-recon` 技能）
   - `osint_fofa` / `osint_quake` / `osint_hunter` 三引擎交叉搜索
   - 目标：IP/域名资产清单、暴露的服务、技术栈

2. **公开信息收集**
   - GitHub/GitLab 搜索组织名和域名（可能泄露源码/凭据）
   - 招聘信息分析（泄露技术栈和内部系统）
   - SSL 证书透明度日志（发现子域名）

**产出**：初始资产清单 + 技术栈概览

## Phase 2: 主动侦察

基于被动侦察结果，有针对性地主动探测（参考 `recon-full` 技能）：

1. **子域名枚举** — `scan_dns`
2. **端口扫描** — `scan_port`（聚焦高价值端口）
3. **存活检测** — `scan_urlive`（确认 HTTP 服务）
4. **指纹识别** — `scan_finger`（技术栈 → 决定攻击方向）
5. **目录爆破** — `brute_dir`（发现隐藏入口）

**产出**：完整资产地图（域名+IP+端口+技术栈+隐藏路径）

## Phase 3: 漏洞发现

### 3.1 自动化扫描
- `poc_web` — Nuclei POC 全量扫描
- `poc_default_login` — 默认口令检测

### 3.2 手动测试（按资产类型）
对每个 Web 应用，根据技术栈选择专项测试：

| 发现 | 测试方向 | 参考技能 |
|------|----------|----------|
| 登录页面 | SQL注入、弱密码 | `sql-injection-methodology`, `default-cred-sweep` |
| 搜索/查询功能 | SQL注入、XSS | `sql-injection-methodology`, `xss-methodology` |
| 文件上传 | 文件上传绕过 | `file-upload-methodology` |
| API 端点 | IDOR、认证绕过 | `api-fuzz`, `idor-methodology` |
| 模板渲染 | SSTI | `ssti-methodology` |
| JWT Token | JWT 攻击 | `jwt-attack-methodology` |
| Java 应用 | 反序列化 | `java-deserialization-methodology` |

### 3.3 关键决策
- **广度优先**：先对所有资产做快速扫描，标记所有可能的入口
- **深度攻击**：选择最有可能突破的 2-3 个入口做深入测试
- 不要在一个点上卡太久——3-5 轮无进展就换方向

## Phase 4: 漏洞利用与验证

发现漏洞后，进行利用验证：
1. 确认漏洞可利用（PoC 验证）
2. 评估影响范围（数据泄露 / RCE / 权限提升）
3. 如获得 shell → 执行后渗透（参考 `post-exploit-linux` / `post-exploit-windows`）
4. 记录完整的利用步骤（复现用）

## Phase 5: 报告输出

参考 `report-generate` 技能生成正式报告。

**关键原则**：
- 发现按风险等级排序（严重 > 高 > 中 > 低 > 信息）
- 每个发现必须有：描述、影响、复现步骤、修复建议
- 管理层摘要用非技术语言
- 附录包含工具列表和详细技术数据

## 时间分配建议
| 阶段 | 时间占比 |
|------|----------|
| 被动+主动侦察 | 20% |
| 漏洞发现 | 30% |
| 利用验证 | 35% |
| 报告 | 15% |
