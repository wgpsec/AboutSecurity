---
name: apt-emulation
description: "APT 模拟与情报驱动红队方法论。基于已知 APT 组织的 TTP（MITRE ATT&CK）设计红队行动计划。当需要模拟特定威胁组织、设计高仿真攻击演练、或根据威胁情报制定攻击策略时使用"
metadata:
  tags: "apt,emulation,mitre,attack,red-team,adversary,ttp,威胁模拟,APT模拟,紫队"
  category: "threat-intel"
  mitre_attack: "TA0001-TA0011"
---

# APT 模拟与情报驱动红队

> **目标**：不是随机攻击，而是模拟真实威胁者的完整攻击链，检验组织防御能力

## ⛔ 深入参考

- 主流 APT 组织 TTP 速查表 → [references/apt-ttp-matrix.md](references/apt-ttp-matrix.md)
- 攻击模拟框架与资源 → [references/emulation-frameworks.md](references/emulation-frameworks.md)

---

## Phase 1: 威胁情报收集 — 选择模拟目标

### 1.1 确定相关威胁组织

```
根据目标行业选择 APT：
├─ 金融 → APT38 (Lazarus), FIN7, Carbanak
├─ 政府/国防 → APT29 (Cozy Bear), APT28 (Fancy Bear), Turla
├─ 能源/工控 → Sandworm, Dragonfly, Triton
├─ 科技/通信 → APT41 (Double Dragon), Salt Typhoon
├─ 医疗 → APT10 (Stone Panda), FIN12
└─ 跨行业 → Lazarus, APT41, FIN7
```

### 1.2 情报来源

```
TTP 情报获取：
├─ MITRE ATT&CK Groups → attack.mitre.org/groups/
├─ 厂商报告 → Mandiant/CrowdStrike/Kaspersky APT 报告
├─ CISA Advisory → 美国网络安全局公告
├─ Threat Intelligence 平台 → MISP/OpenCTI/AlienVault OTX
└─ 学术研究 → APT Deception Papers
```

## Phase 2: TTP 映射与攻击计划

### 2.1 攻击链设计模板

```
模拟 APT29 (Cozy Bear) 示例：

Initial Access:
├─ T1566.001 - Spearphishing with ISO attachment
└─ T1566.002 - Link to watering hole site

Execution:
├─ T1059.001 - PowerShell
└─ T1204.002 - User opens malicious file

Persistence:
├─ T1547.001 - Registry Run Keys
└─ T1053.005 - Scheduled Task

Privilege Escalation:
└─ T1548.002 - UAC Bypass

Defense Evasion:
├─ T1027.005 - Indicator Removal (obfuscation)
├─ T1055.012 - Process Hollowing
└─ T1497.001 - Sandbox evasion

Credential Access:
├─ T1003.001 - LSASS Memory
└─ T1558.003 - Kerberoasting

Discovery:
├─ T1087 - Account Discovery
└─ T1018 - Remote System Discovery

Lateral Movement:
├─ T1021.006 - WinRM
└─ T1550.002 - Pass the Hash

Collection:
└─ T1560.001 - Archive via Utility (7z)

Exfiltration:
└─ T1041 - Exfil over C2 Channel (HTTPS)
```

### 2.2 行动约束（Rules of Engagement）

```
⛔ 模拟前必须确认：
├─ 书面授权（高管签字）
├─ 范围定义（in-scope / out-of-scope 系统）
├─ 紧急联系人（发现真实入侵时）
├─ 停止条件（影响业务时）
├─ 时间窗口
└─ 数据处理规则（不外传真实敏感数据）
```

## Phase 3: 攻击执行

### 3.1 基础设施搭建

```
匹配目标 APT 的基础设施特征：
├─ APT29 → HTTPS C2, 合法域名伪装, 云服务作为 redirector
├─ APT28 → 多层代理, VPN 节点, 一次性基础设施
├─ Lazarus → 被入侵的合法网站作跳板, 自定义 C2 协议
└─ FIN7 → 大规模钓鱼基础设施, Carbanak/Cobalt Strike
```

### 3.2 工具选择映射

| APT 组织 | 实际工具 | 红队模拟替代 |
|----------|---------|-------------|
| APT29 | SUNBURST, EnvyScout | Cobalt Strike + 自定义 loader |
| APT28 | X-Agent, X-Tunnel | Sliver + 自定义隧道 |
| Lazarus | BLINDINGCAN, DRATzarus | Havoc + 自定义后门 |
| FIN7 | GRIFFON, BIRDDOG | Cobalt Strike + BAT2EXE |
| APT41 | ShadowPad, Winnti | PlugX loader 仿写 |

### 3.3 执行节奏

```
模拟真实 APT 的时间模式：
├─ Day 1-3: 侦察 + 钓鱼投递
├─ Day 4-7: 初始立足点 + 持久化
├─ Day 7-14: 内网枚举 + 权限提升
├─ Day 14-21: 横向移动 + 目标定位
├─ Day 21-28: 数据收集 + 外传
└─ ⛔ 不要一天完成所有阶段 → 不符合真实 APT 节奏

Sleep 模式：
├─ 工作时间操作（匹配 APT 时区）
├─ 非工作时间 Beacon 保持 sleep
├─ 模拟节假日暂停（APT 也有假期）
└─ 被检测到部分基础设施 → 评估是否暂停
```

## Phase 4: 检测差距分析

### 4.1 记录每步检测状态

```
| 攻击步骤 | MITRE ID | 执行成功 | 被检测 | 被阻止 | 备注 |
|----------|----------|---------|--------|--------|------|
| 钓鱼投递 | T1566.001 | ✓ | ✗ | ✗ | 邮件网关未检出 |
| PS 执行 | T1059.001 | ✓ | ✓ | ✗ | EDR 告警但未阻止 |
| 持久化 | T1053.005 | ✓ | ✗ | ✗ | 无 Sysmon 规则 |
| LSASS dump | T1003.001 | ✗ | ✓ | ✓ | Credential Guard |
| 横向 PTH | T1550.002 | ✓ | ✓ | ✗ | 检测延迟 4h |
```

### 4.2 输出报告结构

```
报告框架：
├─ 执行摘要（给管理层）
├─ 威胁情报基础（模拟的 APT 背景）
├─ 攻击链时间线（每步操作+时间）
├─ 检测覆盖率矩阵（检测/遗漏比例）
├─ 关键发现（高风险漏洞）
├─ 建议修复措施（按优先级）
└─ ATT&CK Navigator 热力图（覆盖 vs 缺口）
```

## 资源与工具

| 资源 | 用途 |
|------|------|
| MITRE ATT&CK Navigator | 可视化 TTP 覆盖 |
| Atomic Red Team | 原子化攻击测试 |
| MITRE CALDERA | 自动化攻击模拟 |
| Red Canary Reports | 年度威胁报告 |
| ATT&CK Evaluations | 厂商检测能力对比 |
| Threat Actor Playbooks (SCYTHE) | 预制攻击剧本 |

## 关联技能

- **红队评估** → `/skill:red-team-assessment`
- **C2 免杀方法论** → `/skill:c2-evasion-methodology`
- **IOC 分析与对抗** → `/skill:ioc-analysis`
- **社会工程** → `/skill:social-engineering`
