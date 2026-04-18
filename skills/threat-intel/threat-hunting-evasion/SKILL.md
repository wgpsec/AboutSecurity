---
name: threat-hunting-evasion
description: "威胁猎杀原理与规避方法论。理解蓝队如何主动猎杀（Hypothesis-driven / IOC-driven / Analytics-driven），红队如何设计行为使自己不被猎杀到。当需要评估自身操作是否可被威胁猎杀发现时使用"
metadata:
  tags: "threat-hunting,detection,evasion,sigma,yara,hypothesis,威胁猎杀,规避,检测规则"
  category: "threat-intel"
  mitre_attack: "T1562,T1070,T1036,T1027,T1055"
---

# 威胁猎杀原理与规避

> **红队必须理解猎手的思维方式才能不被猎到**

## ⛔ 深入参考

- Sigma/YARA 规则分析与绕过 → [references/detection-rules-bypass.md](references/detection-rules-bypass.md)
- 主流 EDR 检测逻辑分析 → [references/edr-detection-logic.md](references/edr-detection-logic.md)

---

## Part A: 威胁猎杀方法论（蓝队视角）

### 三种猎杀范式

```
1. 假设驱动（Hypothesis-driven）
   "如果 APT29 入侵我们，他们会用 PowerShell 下载器"
   → 搜索: EventID 4104 + "IEX" + "DownloadString"

2. IOC 驱动（IOC-driven）
   "威胁情报显示这个 IP 是 C2"
   → 搜索: 所有连接到该 IP 的主机

3. 分析驱动（Analytics-driven）
   "正常用户不会在凌晨 3 点执行 whoami"
   → 搜索: 异常时间 + 侦察命令组合
```

### 常见猎杀查询（你需要绕过的）

```
# Sigma 规则示例

# 1. 可疑 PowerShell 下载
title: Suspicious PowerShell Download
detection:
  selection:
    EventID: 4104
    ScriptBlockText|contains:
      - 'IEX'
      - 'Invoke-Expression'
      - 'DownloadString'
      - 'Net.WebClient'

# 2. LSASS 访问
title: LSASS Memory Access
detection:
  selection:
    EventID: 10
    TargetImage: 'C:\Windows\System32\lsass.exe'
    GrantedAccess|contains:
      - '0x1010'
      - '0x1410'

# 3. 异常父子进程
title: Suspicious Parent-Child
detection:
  selection:
    ParentImage|endswith: '\outlook.exe'
    Image|endswith:
      - '\cmd.exe'
      - '\powershell.exe'
      - '\mshta.exe'

# 4. 枚举命令组合（5分钟内执行3+侦察命令）
title: Reconnaissance Commands
detection:
  selection:
    CommandLine|contains:
      - 'whoami'
      - 'net user'
      - 'net group'
      - 'ipconfig'
      - 'systeminfo'
    timeframe: 5m
    condition: selection | count() >= 3
```

### 猎杀数据源

| 数据源 | 猎杀目标 |
|--------|---------|
| Sysmon | 进程创建/注入/网络/文件 |
| PowerShell Logging | 脚本执行内容 |
| Windows Security | 认证/权限/策略 |
| DNS Logs | C2 域名/DGA/隧道 |
| Proxy/Firewall | 异常外连/大量传输 |
| EDR Telemetry | 行为链 |
| NetFlow | 流量模式异常 |
| LDAP Logs | AD 枚举 |

---

## Part B: 红队视角 — 规避威胁猎杀

### 策略 1: 不匹配已知检测规则

```
分析 Sigma 仓库公开规则 → 确保你的操作不命中

常见规则绕过：
├─ "IEX(DownloadString)" 检测
│   绕过: 使用 .NET WebClient 直接调用，不走 PS
│   或: certutil / bitsadmin / curl 替代
│
├─ "cmd.exe spawned by outlook.exe" 检测
│   绕过: 使用 COM 对象执行，不创建子进程
│   或: 用 VBA 调用 WMI → wmiprvse.exe 作父进程
│
├─ "lsass.exe access" 检测
│   绕过: Handle duplicate 方式（不直接 OpenProcess）
│   或: 使用 NanoDump 的 MiniDumpWriteDump 替代方式
│
└─ "Reconnaissance command burst" 检测
    绕过: 分散执行（每个命令间隔 10+ 分钟）
    或: 通过 WMI/LDAP 查询代替命令行工具
```

### 策略 2: 行为模式正常化

```
原则：让你的操作看起来像正常业务行为

网络行为正常化：
├─ C2 通信在业务时间（9am-6pm）
├─ 心跳间隔匹配正常 HTTP 刷新（不要太规律）
├─ 流量大小匹配正常 API 调用
├─ 使用目标已有的 SaaS 域名（Slack/Teams API 模仿）
└─ 避免凌晨大量数据传输

主机行为正常化：
├─ 不要短时间内执行多个侦察命令
├─ 使用目标环境已有的工具（LOLBins）
├─ 进程名/路径匹配合法程序
├─ 不要创建明显异常的用户名（admin123/test）
└─ 操作间隔模仿人类行为节奏
```

### 策略 3: YARA 规则绕过

```
YARA 匹配原理：字节序列 + 条件逻辑

绕过方式：
├─ 字符串特征 → XOR/AES 加密关键字符串
├─ 字节序列 → 使用不同编译器/编译选项
├─ 文件结构 → 修改 PE header / Rich header
├─ 入口点模式 → 改变 stub / 使用合法 packer
└─ 行为签名 → 改变 API 调用顺序/方式

验证方式：
yara -r sigma_rules/ my_payload.exe  # 扫描前先自测
```

### 策略 4: EDR 行为检测规避

```
现代 EDR 不只看签名，看行为链：
├─ Process Chain: 邮件→CMD→PowerShell→网络连接 = 恶意
├─ Memory Pattern: RWX + PE header + 远程线程 = 注入
├─ File Pattern: 写入→执行→删除 = dropper
└─ Network Pattern: DNS over HTTPS + 固定间隔 = C2

红队对策：
├─ 断开行为链 → 不要在同一进程内完成所有操作
├─ 时间分散 → 每步操作之间 Sleep 较长时间
├─ 使用合法流程 → 通过 COM/WMI/计划任务执行
├─ 避免 known-bad 组合 → 研究目标 EDR 的检测逻辑
└─ 测试 → 在同类 EDR 环境中预演
```

### 策略 5: 猎杀者思维盲区利用

```
猎杀者常见盲区（可利用）：
├─ 周末/节假日 → 人员不足，响应慢
├─ 正常业务流量 → 混入合法 API 调用难以区分
├─ 非标准数据源 → 如果日志未采集就看不到
├─ 加密流量 → TLS 内容不可见（除非有 TLS 解密）
├─ Cloud 环境 → 日志碎片化，跨平台关联困难
├─ 合法工具 → LOLBins 产生的日志与正常管理操作相同
└─ 告警疲劳 → 大量低优先级告警中隐藏高风险操作
```

## 红队自检清单

```
操作前自检：
[ ] Sigma 公开规则是否命中我的 TTP？
[ ] 我的 C2 通信是否能被 JA3/JARM 识别？
[ ] 我的进程链是否有异常父子关系？
[ ] 我的网络模式是否有固定间隔/大小？
[ ] 我是否在短时间内执行了多个侦察命令？
[ ] 我的工具是否在 VirusTotal 上已有检出？
[ ] 目标是否部署了 Sysmon？配置了哪些规则？
[ ] 目标 EDR 是什么？我是否在同类环境测试过？
```

## 关联技能

- **IOC 分析与对抗** → `/skill:ioc-analysis`
- **APT 模拟** → `/skill:apt-emulation`
- **C2 免杀方法论** → `/skill:c2-evasion-methodology`
- **日志逃逸** → `/skill:log-evasion`
