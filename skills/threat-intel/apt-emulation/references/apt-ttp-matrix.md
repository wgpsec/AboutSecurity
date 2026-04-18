# 主流 APT 组织 TTP 速查表

> 本文档为红队模拟提供主流 APT 组织的 TTP 快速参考。目标不是完全复制 APT 的工具链，而是**复制其行为模式和攻击逻辑**，以测试目标组织对特定威胁的检测和响应能力。

---

## 1. APT 组织总览矩阵

| APT 组织 | 归属 | 主要目标行业 | 活跃时间 | 复杂度 | 典型攻击周期 |
|----------|------|-------------|---------|--------|-------------|
| APT28 (Fancy Bear) | 俄罗斯 GRU | 政府/军事/媒体 | 2004-至今 | 高 | 数周-数月 |
| APT29 (Cozy Bear) | 俄罗斯 SVR | 政府/外交/科研 | 2008-至今 | 极高 | 数月-数年 |
| APT41 (Double Dragon) | 中国 | 科技/通信/游戏/医疗 | 2012-至今 | 高 | 数周-数月 |
| Lazarus Group | 朝鲜 RGB | 金融/加密货币/国防 | 2009-至今 | 高 | 数周-数月 |
| FIN7 (Carbanak) | 犯罪组织 | 零售/餐饮/金融 | 2013-至今 | 中高 | 数天-数周 |
| Turla (Venomous Bear) | 俄罗斯 FSB | 政府/外交/军事 | 2004-至今 | 极高 | 数月-数年 |
| Sandworm (Voodoo Bear) | 俄罗斯 GRU | 能源/政府/选举 | 2009-至今 | 极高 | 数月（破坏性） |
| APT38 | 朝鲜 RGB | 银行/SWIFT/金融 | 2014-至今 | 高 | 数月（金融盗窃） |
| Salt Typhoon | 中国 | 电信/ISP/通信 | 2020-至今 | 高 | 数月-数年 |
| Volt Typhoon | 中国 | 关基/通信/能源 | 2021-至今 | 高 | 数月-数年 |

---

## 2. 各 APT 组织详细 TTP 分析

### 2.1 APT28 (Fancy Bear / Sofacy / Sednit)

**归属**: 俄罗斯军事情报总局 (GRU Unit 26165)
**主要目标**: 政府、军事、媒体、体育组织、选举基础设施
**动机**: 间谍活动、政治干预、信息战

#### 攻击链

```
APT28 典型攻击链:

Initial Access:
├─ T1566.001 - 鱼叉钓鱼附件（Office 文档 + VBA 宏）
├─ T1566.002 - 鱼叉钓鱼链接（凭据钓鱼页面）
├─ T1190 - 公开应用漏洞利用（Exchange, VPN）
└─ T1133 - 外部远程服务（被盗 VPN 凭据）

Execution:
├─ T1059.001 - PowerShell
├─ T1059.005 - Visual Basic (VBA 宏)
├─ T1204.001 - 用户打开恶意链接
└─ T1204.002 - 用户打开恶意文件

Persistence:
├─ T1547.001 - Registry Run Keys
├─ T1053.005 - Scheduled Task
└─ T1137.001 - Office Application Startup

Privilege Escalation:
├─ T1068 - 内核漏洞利用（CVE-2016-7255 等）
└─ T1548.002 - UAC Bypass

Defense Evasion:
├─ T1027 - 混淆编码
├─ T1036.005 - 合法进程名伪装
├─ T1070.004 - 文件删除
└─ T1055 - 进程注入

Credential Access:
├─ T1003.001 - LSASS 内存 dump
├─ T1003.003 - NTDS.dit
├─ T1110.003 - 密码喷洒
└─ T1556.001 - 凭据拦截

Lateral Movement:
├─ T1021.002 - SMB/Windows Admin Shares
├─ T1021.001 - RDP
└─ T1550.002 - Pass the Hash

C2:
├─ T1071.001 - HTTPS（自定义 HTTP header）
├─ T1071.004 - DNS
├─ T1090.002 - External Proxy
└─ T1573.002 - 非对称加密

Exfiltration:
├─ T1041 - Over C2 Channel
├─ T1567.002 - 到云存储
└─ T1048 - 替代协议（邮件外传）
```

#### 已知工具与模拟映射

| APT28 工具 | 功能 | 红队模拟替代 |
|------------|------|-------------|
| X-Agent / Sofacy | 全功能 RAT (Windows/Linux) | Cobalt Strike / Sliver |
| X-Tunnel | 网络隧道 | Chisel / Ligolo-ng |
| Zebrocy | 下载器/信息收集 | 自定义 Go Dropper |
| LoJax | UEFI 持久化 | 概念验证（不在红队行动中使用） |
| Responder (修改版) | 凭据中继 | Responder + ntlmrelayx |
| Mimikatz | 凭据 dump | Mimikatz / Rubeus / NanoDump |
| Koadic | C2 框架 | Koadic / Havoc |

#### 红队模拟要点

```
APT28 模拟核心行为:
├─ 大量使用凭据钓鱼（OAuth 钓鱼尤其常见）
├─ 快速凭据收集 → 横向移动
├─ 使用一次性基础设施（快速轮换）
├─ 多层代理链隐藏源 IP
├─ 积极利用 0day/Nday（Exchange, VPN, 浏览器）
└─ 数据压缩 + 加密后通过 C2 或云服务外传
```

---

### 2.2 APT29 (Cozy Bear / The Dukes / Nobelium)

**归属**: 俄罗斯对外情报局 (SVR)
**主要目标**: 政府、外交机构、科研机构、IT 供应链
**动机**: 长期战略间谍活动

#### 攻击链

```
APT29 典型攻击链:

Initial Access:
├─ T1195.002 - 供应链攻击（SolarWinds SUNBURST）
├─ T1566.001 - 鱼叉钓鱼（ISO/LNK/HTML Smuggling）
├─ T1078.004 - 云服务合法账户
└─ T1199 - 受信任关系（MSP/IT服务商）

Execution:
├─ T1059.001 - PowerShell
├─ T1059.003 - Windows Command Shell
├─ T1106 - Native API
└─ T1047 - WMI

Persistence:
├─ T1098.001 - 云账户权限修改
├─ T1098.002 - Exchange 邮箱权限添加
├─ T1136 - 创建账户（Azure AD 应用注册）
├─ T1078 - 合法账户（OAuth Token 持久）
└─ T1505.003 - Web Shell (Exchange)

Defense Evasion:
├─ T1027.005 - 工具特征消除
├─ T1055.012 - Process Hollowing
├─ T1497.001 - 沙箱检测
├─ T1480.001 - Environment Keying（只在目标环境运行）
├─ T1218.011 - Rundll32 执行
└─ T1036 - 进程伪装

Credential Access:
├─ T1003.001 - LSASS
├─ T1003.006 - DCSync
├─ T1558.003 - Kerberoasting
├─ T1528 - 窃取 OAuth Token
└─ T1552.004 - 私钥窃取

Lateral Movement:
├─ T1021.006 - WinRM
├─ T1021.002 - SMB Admin Shares
├─ T1550.001 - Application Access Token（云环境）
└─ T1072 - 软件分发工具（利用 SCCM 等）

C2:
├─ T1071.001 - HTTPS（伪装合法 SaaS API）
├─ T1071.003 - Mail Protocol（Exchange Web Services）
├─ T1102.002 - Bidirectional Web Service（合法云服务做 C2）
└─ T1568.002 - Domain Generation Algorithm

Exfiltration:
├─ T1567.002 - 到云存储（OneDrive/Google Drive）
├─ T1048.002 - 非对称加密外传
└─ T1041 - Over C2 Channel（低速长期）
```

#### 已知工具与模拟映射

| APT29 工具 | 功能 | 红队模拟替代 |
|------------|------|-------------|
| SUNBURST | 供应链后门 | 自定义 DLL 注入 |
| EnvyScout | HTML Smuggling 投递 | 自定义 HTML Smuggling 模板 |
| BoomBox | 下载器（Dropbox C2） | 自定义 Go 下载器 + 云 C2 |
| NativeZone / VaporRage | 加载器 | 自定义 Shellcode Loader |
| WELLMESS / WELLMAIL | 跨平台后门 | Sliver (Go 跨平台) |
| FoggyWeb | AD FS 后门 | 概念验证测试 |
| MagicWeb | Azure AD 后门 | AADInternals |
| Brute Ratel C4 | 商业 C2 | Brute Ratel C4 |

#### 红队模拟要点

```
APT29 模拟核心行为:
├─ 极高的 OPSEC（几乎不被检测）
├─ 大量使用合法云服务作为 C2（Dropbox/Teams/OneDrive）
├─ HTML Smuggling 投递（ISO → LNK → DLL sideload）
├─ 供应链入侵作为初始访问
├─ 环境感知: payload 仅在目标环境解密执行
├─ 对 Azure AD / M365 环境的深度利用
├─ 超长驻留时间（SolarWinds 事件中驻留 14 个月）
└─ C2 通信伪装成正常 API 调用
```

---

### 2.3 APT41 (Double Dragon / Winnti / Barium)

**归属**: 中国（同时执行国家任务和网络犯罪）
**主要目标**: 科技、游戏、通信、医疗、教育
**动机**: 间谍活动 + 经济利益（双重动机）

#### 攻击链

```
APT41 典型攻击链:

Initial Access:
├─ T1190 - 公开应用漏洞利用（Citrix, Cisco, Zoho, Exchange）
├─ T1195.002 - 供应链攻击（CCleaner, ASUS Live Update）
├─ T1566.001 - 鱼叉钓鱼附件
└─ T1078 - 合法账户（被盗凭据）

Execution:
├─ T1059.001 - PowerShell
├─ T1059.003 - cmd.exe
├─ T1047 - WMI
└─ T1569.002 - 服务执行

Persistence:
├─ T1543.003 - Windows Service
├─ T1547.001 - Registry Run Keys
├─ T1053.005 - Scheduled Task
├─ T1505.003 - Web Shell
└─ T1554 - 二进制植入（合法软件 Trojanize）

Defense Evasion:
├─ T1055 - 进程注入
├─ T1027 - 混淆
├─ T1036 - 伪装
├─ T1070 - 痕迹清除
├─ T1140 - 去混淆/解码
└─ T1553.002 - 代码签名（使用被盗证书）

Credential Access:
├─ T1003 - 凭据 Dump
├─ T1110 - 暴力破解
└─ T1552 - 不安全凭据存储

Discovery:
├─ T1082 - 系统信息
├─ T1083 - 文件目录发现
├─ T1135 - 网络共享发现
└─ T1046 - 网络服务扫描

Lateral Movement:
├─ T1021.001 - RDP
├─ T1021.002 - SMB
├─ T1021.004 - SSH
└─ T1570 - 内网工具传输

C2:
├─ T1071.001 - HTTPS
├─ T1071.004 - DNS
├─ T1090.001 - Internal Proxy
├─ T1095 - 非应用层协议（TCP/UDP 自定义）
└─ T1572 - 协议隧道

Exfiltration:
├─ T1041 - Over C2 Channel
├─ T1560.001 - 压缩归档
└─ T1048 - 替代协议
```

#### 已知工具与模拟映射

| APT41 工具 | 功能 | 红队模拟替代 |
|------------|------|-------------|
| ShadowPad | 模块化后门 | Cobalt Strike + 自定义 BOF |
| Winnti | 内核 Rootkit | 概念验证（不在常规红队中使用） |
| POISONPLUG | 模块化 RAT | Sliver + 自定义 C2 |
| Cobalt Strike | C2 框架 | Cobalt Strike（APT41 直接使用商业工具） |
| China Chopper | Web Shell | 自定义内存 WebShell |
| DeadEye / LowKey | 加载器/后门 | 自定义 Loader |
| KEYPLUG | 跨平台后门 (Linux/Win) | Sliver / Mythic (跨平台 agent) |

#### 红队模拟要点

```
APT41 模拟核心行为:
├─ 大规模漏洞利用扫描 + 快速武器化
├─ 供应链攻击（比 APT29 更频繁）
├─ 同时攻击 Windows 和 Linux
├─ 使用被盗代码签名证书签署恶意软件
├─ 在被入侵网络中部署加密挖矿（犯罪活动）
├─ 广泛使用 Cobalt Strike（直接使用破解版）
├─ 针对游戏行业的虚拟货币/道具盗窃
└─ 白天执行国家任务，晚上搞犯罪（双重行为）
```

---

### 2.4 Lazarus Group (HIDDEN COBRA / Zinc)

**归属**: 朝鲜侦察总局 (RGB)
**主要目标**: 金融机构、加密货币交易所、国防/航空、媒体
**动机**: 经济利益（外汇获取）+ 间谍活动

#### 攻击链

```
Lazarus 典型攻击链:

Initial Access:
├─ T1566.001 - 鱼叉钓鱼（定制化招聘/工作机会主题）
├─ T1566.002 - 鱼叉钓鱼链接
├─ T1189 - 水坑攻击
├─ T1195.002 - 供应链攻击（3CX 事件）
└─ T1195.001 - 开发工具供应链（npm 恶意包）

Execution:
├─ T1059.001 - PowerShell
├─ T1059.005 - Visual Basic
├─ T1059.007 - JavaScript
├─ T1204.002 - 用户执行恶意文件
└─ T1106 - Native API

Persistence:
├─ T1547.001 - Registry Run Keys
├─ T1543.003 - Windows Service
├─ T1053.005 - Scheduled Task
└─ T1547.009 - Shortcut Modification

Defense Evasion:
├─ T1027 - 混淆文件
├─ T1036 - 伪装
├─ T1055 - 进程注入
├─ T1140 - 去混淆解码
├─ T1070.004 - 文件删除
└─ T1553.002 - 代码签名

Credential Access:
├─ T1003 - LSASS Dump
├─ T1056.001 - 键盘记录
└─ T1555 - 密码存储

Lateral Movement:
├─ T1021.002 - SMB Admin Shares
├─ T1021.001 - RDP
└─ T1570 - 内网工具传输

C2:
├─ T1071.001 - HTTPS
├─ T1071.004 - DNS
├─ T1090.003 - Multi-hop Proxy
├─ T1102 - Web Service（被入侵的合法网站做 C2）
└─ T1573 - 加密通道（AES/RSA 自定义协议）

Impact（金融攻击特有）:
├─ T1531 - 帐户访问删除
├─ T1485 - 数据销毁（攻击后擦除痕迹）
└─ T1565.001 - SWIFT 交易篡改
```

#### 已知工具与模拟映射

| Lazarus 工具 | 功能 | 红队模拟替代 |
|-------------|------|-------------|
| BLINDINGCAN | RAT | Havoc / Mythic |
| DRATzarus | 后门 | 自定义 C/C++ Implant |
| HOPLIGHT | 代理/隧道 | Chisel + Ligolo-ng |
| AppleJeus | 假加密货币交易软件 | 自定义 Electron 应用 |
| FALLCHILL | RAT + 擦除器 | 自定义 Implant |
| TraderTraitor | 加密货币攻击链 | 社会工程 + Payload |
| Manuscrypt | 多平台后门 | Sliver (跨平台) |
| 破坏模块 | KillDisk / 磁盘擦除 | 概念验证（禁止实际使用） |

#### 红队模拟要点

```
Lazarus 模拟核心行为:
├─ 高度定制化的社会工程（假招聘、假加密货币工具）
├─ 使用被入侵的合法网站作为 C2 跳板
├─ 自定义加密协议（非标准 C2 通信）
├─ 多阶段感染链（Dropper → Loader → RAT）
├─ 攻击后擦除痕迹（磁盘擦除/日志清除）
├─ 跨平台攻击（Windows/macOS/Linux）
├─ 针对加密货币行业的定向攻击
└─ 极长的社会工程准备周期（数月培养信任）
```

---

### 2.5 FIN7 (Carbanak / Navigator Group)

**归属**: 犯罪组织（起源东欧，全球运营）
**主要目标**: 零售（POS系统）、餐饮、酒店、金融
**动机**: 经济利益（信用卡数据、ATM 盗窃）

#### 攻击链

```
FIN7 典型攻击链:

Initial Access:
├─ T1566.001 - 鱼叉钓鱼附件（精心制作的 Office 文档）
├─ T1566.002 - 钓鱼链接
└─ T1199 - 通过第三方供应商（POS 管理软件）

Execution:
├─ T1059.001 - PowerShell（混淆）
├─ T1059.005 - VBA 宏
├─ T1059.007 - JavaScript/JScript
├─ T1047 - WMI
└─ T1218.005 - Mshta

Persistence:
├─ T1547.001 - Registry Run Keys
├─ T1053.005 - Scheduled Task
└─ T1137.001 - Office Add-in

Defense Evasion:
├─ T1027.001 - 二进制填充
├─ T1027.010 - Command Obfuscation
├─ T1036 - 伪装
├─ T1055 - 进程注入
├─ T1218.005 - Mshta 执行
└─ T1218.010 - Regsvr32 执行

Credential Access:
├─ T1003 - LSASS
├─ T1056.001 - 键盘记录
└─ T1552 - 不安全凭据

Discovery:
├─ T1018 - 远程系统发现
├─ T1057 - 进程发现
├─ T1082 - 系统信息发现
└─ T1016 - 网络配置发现

Lateral Movement:
├─ T1021.001 - RDP
├─ T1021.002 - SMB
└─ T1021.004 - SSH

Collection (POS 相关):
├─ T1005 - 本地数据收集
├─ T1113 - 屏幕截图
├─ T1125 - 视频捕获
└─ T1056 - 输入捕获（POS RAM scraping）

C2:
├─ T1071.001 - HTTPS
├─ T1071.004 - DNS（DNSCAT 变体）
└─ T1102 - Web Service（合法服务做 C2）
```

#### 已知工具与模拟映射

| FIN7 工具 | 功能 | 红队模拟替代 |
|-----------|------|-------------|
| GRIFFON | JavaScript 后门 | 自定义 JS/VBS 后门 |
| BIRDDOG | 后门/下载器 | 自定义 C# Implant |
| Carbanak | 银行木马 | Cobalt Strike + 自定义模块 |
| PILLOWMINT | POS RAM Scraper | 概念验证 |
| POWERPLANT | PowerShell 框架 | PowerShell Empire / 自定义 |
| BOOSTWRITE | Loader（DLL 劫持） | 自定义 DLL Sideloader |
| Cobalt Strike | C2 框架 | Cobalt Strike |
| DICELOADER | 轻量下载器 | 自定义 Shellcode Loader |

#### 红队模拟要点

```
FIN7 模拟核心行为:
├─ 精心制作的钓鱼文档（像真实业务文件）
├─ 重度依赖 PowerShell + VBA 宏
├─ 通过 COM 对象绕过进程链检测
├─ 大量使用 WMI 做横向移动
├─ 目标明确: POS 系统 / 财务系统
├─ 使用合法 IT 管理工具伪装（RMM 工具）
├─ 创建假安全公司（Combi Security/Bastion Secure）招募人才
└─ 使用 Cobalt Strike 作为主要 C2
```

---

### 2.6 Turla (Venomous Bear / Snake / Uroburos)

**归属**: 俄罗斯联邦安全局 (FSB Center 16)
**主要目标**: 政府、外交、军事、科研（全球范围）
**动机**: 长期战略间谍

#### 攻击链

```
Turla 典型攻击链:

Initial Access:
├─ T1566.001 - 鱼叉钓鱼
├─ T1189 - 水坑攻击（Strategic Web Compromise）
├─ T1199 - 劫持其他 APT 的基础设施（劫持 APT34 C2）
└─ T1078 - 被盗凭据

Execution:
├─ T1059.001 - PowerShell
├─ T1059.003 - cmd.exe
├─ T1106 - Native API
└─ T1129 - 共享模块

Persistence:
├─ T1547.001 - Registry Run Keys
├─ T1543.003 - Windows Service
├─ T1547.012 - Print Processor
├─ T1546.003 - WMI Event Subscription
└─ T1505.003 - Web Shell

Defense Evasion:
├─ T1027 - 多层混淆
├─ T1036 - 伪装
├─ T1055 - 进程注入
├─ T1014 - Rootkit（Snake rootkit）
├─ T1480 - 执行环境门槛
└─ T1564.001 - 隐藏文件

C2（最独特的部分）:
├─ T1071.001 - HTTPS
├─ T1071.004 - DNS（精细的 DNS 隧道）
├─ T1102 - Web Service（Google/Pastebin 做 C2）
├─ T1090.003 - Multi-hop Proxy（被入侵的卫星链路）
├─ T1205 - Traffic Signaling（CD00R 端口敲门）
└─ 使用被入侵的其他组织作为代理节点

Exfiltration:
├─ T1041 - Over C2 Channel
├─ T1048 - 替代协议
└─ T1567 - 到 Web 服务
```

#### 已知工具与模拟映射

| Turla 工具 | 功能 | 红队模拟替代 |
|------------|------|-------------|
| Snake / Uroburos | 内核 Rootkit + P2P C2 | 概念验证 |
| Carbon / Cobra | 模块化后门 | Cobalt Strike + Sliver |
| Kazuar | .NET 后门 | Covenant / Mythic |
| LightNeuron | Exchange 邮件后门 | 自定义 Transport Agent |
| Crutch | Dropbox C2 后门 | 自定义云 C2 |
| TinyTurla | 轻量后门 | 自定义极简 Implant |
| Gazer | 模块化后门 | 自定义 C/C++ |
| Penquin | Linux 后门 | 自定义 Linux Implant |

#### 红队模拟要点

```
Turla 模拟核心行为:
├─ 极高的 OPSEC（最难检测的 APT 之一）
├─ 劫持其他 APT 的基础设施作为自己的跳板
├─ 使用被入侵的卫星链路作为 C2（极难追踪）
├─ 多层 C2 架构（P2P mesh + 集中式混合）
├─ 使用合法 Web 服务（Google/Dropbox/Pastebin）做 C2
├─ 内核级 Rootkit 隐藏
├─ 超长驻留（数年级别）
└─ 使用 WMI Event Subscription 做高级持久化
```

---

### 2.7 Sandworm (Voodoo Bear / BlackEnergy Group)

**归属**: 俄罗斯军事情报总局 (GRU Unit 74455)
**主要目标**: 能源/电力、政府、选举基础设施
**动机**: 破坏性攻击 + 信息战

#### 攻击链

```
Sandworm 典型攻击链:

Initial Access:
├─ T1566.001 - 鱼叉钓鱼（BlackEnergy 宏文档）
├─ T1190 - 公开应用漏洞利用
├─ T1133 - 外部远程服务（VPN）
└─ T1195.002 - 供应链攻击（M.E.Doc → NotPetya）

Execution:
├─ T1059.001 - PowerShell
├─ T1059.005 - VBA
├─ T1047 - WMI
└─ T1106 - Native API

Persistence:
├─ T1053.005 - Scheduled Task
├─ T1543.003 - Windows Service
├─ T1547.001 - Registry Run Keys
└─ T1505.003 - Web Shell

Impact（Sandworm 的标志性阶段）:
├─ T1485 - 数据销毁（NotPetya, KillDisk）
├─ T1486 - 数据加密影响（伪勒索软件）
├─ T1491 - Defacement
├─ T1495 - 固件破坏
├─ T1529 - 系统关机/重启
└─ T1562 - 安全工具禁用

ICS/OT 相关:
├─ Industroyer/CrashOverride → 电力系统攻击
├─ Industroyer2 → 2022 乌克兰电网攻击
└─ BlackEnergy → SCADA HMI 攻击
```

#### 已知工具与模拟映射

| Sandworm 工具 | 功能 | 红队模拟替代 |
|--------------|------|-------------|
| BlackEnergy | 模块化后门 | Cobalt Strike |
| Industroyer / CrashOverride | ICS 攻击 | 概念验证（仅在授权 ICS 环境） |
| NotPetya | 伪勒索/擦除器 | 概念验证（禁止实际使用） |
| Olympic Destroyer | 擦除器 | 概念验证 |
| VPNFilter | IoT 攻击 | 概念验证 |
| Cyclops Blink | 网络设备后门 | 概念验证 |
| CaddyWiper | 擦除器（2022乌克兰） | 概念验证 |

#### 红队模拟要点

```
Sandworm 模拟核心行为:
├─ 重点模拟: 供应链攻击路径（不执行实际破坏）
├─ 模拟 ICS/OT 环境渗透路径（需专门授权）
├─ 测试破坏性攻击的检测和响应能力
├─ 供应链软件更新劫持场景
├─ ⛔ 禁止: 实际部署擦除器/勒索软件
└─ ⛔ 禁止: 未授权的 ICS/OT 系统测试
```

---

### 2.8 APT38 (Stardust Chollima)

**归属**: 朝鲜侦察总局 (RGB) — Lazarus 子集，专注金融盗窃
**主要目标**: 银行（SWIFT系统）、金融机构
**动机**: 为朝鲜政权获取外汇

#### 攻击链

```
APT38 典型攻击链（银行攻击专用）:

Phase 1: 初始入侵（数周-数月）
├─ T1566.001 - 鱼叉钓鱼（银行员工）
├─ T1189 - 水坑攻击（金融行业网站）
└─ T1190 - 漏洞利用

Phase 2: 内部侦察（数月）
├─ T1087 - 账户发现
├─ T1083 - 文件浏览（寻找 SWIFT 相关文件）
├─ T1057 - 进程发现
├─ T1049 - 网络连接发现
└─ 深入了解银行内部流程和 SWIFT 操作

Phase 3: 横向到 SWIFT（数周）
├─ T1021 - 横向移动到 SWIFT 终端
├─ T1003 - 凭据获取（SWIFT 操作员凭据）
└─ T1078 - 获取合法 SWIFT 操作权限

Phase 4: 执行盗窃
├─ T1565.001 - 修改 SWIFT 交易
├─ 在银行结算窗口期发起转账
└─ 转账到预先设置的收款账户

Phase 5: 销毁证据
├─ T1485 - 数据销毁（擦除日志）
├─ T1070 - 痕迹清除
├─ T1489 - 服务停止（禁用安全监控）
└─ 部署擦除器覆盖攻击痕迹
```

#### 红队模拟要点

```
APT38 模拟核心行为:
├─ 超长侦察期（深入了解目标业务流程）
├─ 精确定位关键系统（SWIFT 终端/财务系统）
├─ 在特定时间窗口执行（银行休息日/假期）
├─ 攻击后主动销毁证据
├─ 模拟要点: 测试金融系统隔离有效性
├─ 模拟要点: 测试 SWIFT 操作异常检测能力
└─ ⛔ 禁止: 实际修改金融交易数据
```

---

### 2.9 Salt Typhoon (GhostEmperor / FamousSparrow)

**归属**: 中国
**主要目标**: 电信运营商、ISP、通信基础设施
**动机**: 通信监控/情报收集

#### 攻击链

```
Salt Typhoon 典型攻击链:

Initial Access:
├─ T1190 - 边界设备漏洞利用（路由器/交换机/防火墙）
├─ T1133 - VPN/远程管理接口
└─ T1078 - 被盗凭据（电信运营商管理账户）

Persistence:
├─ 固件级后门（路由器/交换机 implant）
├─ T1542 - Pre-OS Boot（网络设备固件修改）
└─ T1505.003 - Web Shell

Collection:
├─ T1040 - 网络嗅探（核心路由器上的流量镜像）
├─ T1557 - 中间人（BGP 劫持/流量重定向）
├─ 合法通信数据拦截（通话记录/短信/邮件元数据）
└─ T1114 - 邮件收集

C2:
├─ T1071 - 通过合法网络管理协议（SNMP/SSH）
├─ 嵌入网络设备固件中的后门
└─ 利用电信骨干网自身作为 C2 通道
```

#### 红队模拟要点

```
Salt Typhoon 模拟核心行为:
├─ 针对网络基础设施（路由器/交换机/防火墙）
├─ 利用网络设备管理接口漏洞
├─ 测试网络设备固件完整性验证
├─ 测试 BGP 安全配置
├─ 测试核心路由器访问控制
├─ 评估网络流量监控的检测能力
└─ 模拟合法网络数据拦截场景
```

---

### 2.10 Volt Typhoon (Bronze Silhouette)

**归属**: 中国
**主要目标**: 关键基础设施（通信、能源、水利、交通）
**动机**: 预置访问（战时可启用的破坏能力）

#### 攻击链

```
Volt Typhoon 典型攻击链:

Initial Access:
├─ T1190 - 边界设备漏洞（Fortinet FortiGuard, Zoho, Citrix）
├─ T1133 - 外部远程服务
└─ T1078 - 合法凭据

Execution:
├─ T1059.003 - cmd.exe（纯命令行操作）
├─ T1047 - WMI
├─ T1106 - Native API
└─ ⛔ 不使用 PowerShell（避免 ScriptBlock Logging）

Persistence:
├─ T1078 - 合法账户（创建/修改本地账户）
├─ T1505.003 - Web Shell（SOHO 路由器）
└─ 几乎不使用传统持久化机制（依赖合法凭据）

Defense Evasion（Volt Typhoon 最大特色: Living-off-the-Land）:
├─ T1218 - LOLBins 执行
│   ├─ ntdsutil.exe → DC 密码管理
│   ├─ netsh.exe → 网络配置/端口转发
│   ├─ ldifde.exe → LDAP 数据导出
│   └─ 其他系统自带工具
├─ T1036 - 二进制伪装
├─ T1070 - 痕迹清除
├─ ⛔ 不使用自定义恶意软件
├─ ⛔ 不使用 Cobalt Strike / Sliver 等 C2 框架
└─ ⛔ 不使用 PowerShell Empire 等后渗透框架

Credential Access:
├─ T1003 - LSASS + SAM + NTDS.dit
├─ T1003.003 - ntdsutil (AD 备份获取凭据)
└─ T1552 - 配置文件中的凭据

Discovery:
├─ T1082 - systeminfo
├─ T1016 - ipconfig / netstat
├─ T1049 - net session / net use
├─ T1033 - whoami
└─ T1018 - ping / net view

Lateral Movement:
├─ T1021.001 - RDP（合法凭据）
├─ T1021.002 - SMB（合法凭据）
├─ T1021.004 - SSH
└─ 通过 SOHO 路由器作为跳板

C2:
├─ 通过 SOHO 路由器构建代理网络
├─ T1090 - 多层代理（被入侵的路由器链）
├─ 使用合法协议（SSH/RDP）→ 不需要自定义 C2
└─ 极低频率通信
```

#### 红队模拟要点

```
Volt Typhoon 模拟核心行为（最具挑战性的模拟）:
├─ 纯 LOLBins 操作（不使用任何自定义工具/框架）
├─ 所有操作通过系统自带工具完成
├─ 不落地文件（Living off the Land to the extreme）
├─ 命令行不使用 PowerShell
├─ 使用 SOHO 路由器/IoT 设备作为代理
├─ 依赖合法凭据而非恶意软件持久化
├─ 极低速度操作（模拟长期预置）
├─ 重点测试: EDR 能否检测纯 LOLBin 攻击链
└─ 重点测试: 网络监控能否识别合法协议中的横向移动
```

---

## 3. MITRE ATT&CK 阶段 TTP 对照矩阵

### 各 APT 各阶段使用的技术 ID

| 阶段 | APT28 | APT29 | APT41 | Lazarus | FIN7 | Turla | Sandworm | Volt Typhoon |
|------|-------|-------|-------|---------|------|-------|----------|-------------|
| Initial Access | T1566 | T1195 | T1190 | T1566 | T1566 | T1189 | T1195 | T1190 |
| Execution | T1059.001 | T1059.001 | T1059.001 | T1059.007 | T1059.001 | T1059.001 | T1059.001 | T1059.003 |
| Persistence | T1053 | T1098 | T1543 | T1547 | T1547 | T1546 | T1543 | T1078 |
| Priv Esc | T1068 | T1548 | T1068 | T1055 | T1055 | T1055 | T1068 | T1078 |
| Defense Evasion | T1027 | T1480 | T1553 | T1027 | T1218 | T1014 | T1070 | T1218 |
| Credential | T1003 | T1528 | T1003 | T1003 | T1003 | T1003 | T1003 | T1003 |
| Discovery | T1087 | T1087 | T1046 | T1083 | T1018 | T1082 | T1082 | T1082 |
| Lateral | T1021.002 | T1021.006 | T1021.001 | T1021.002 | T1021.001 | T1021 | T1021 | T1021.001 |
| C2 | T1071.001 | T1102 | T1071 | T1090.003 | T1071.001 | T1205 | T1071 | T1090 |
| Exfil | T1041 | T1567 | T1041 | T1041 | T1041 | T1048 | N/A | N/A |
| Impact | N/A | N/A | N/A | T1485 | N/A | N/A | T1485 | N/A |

---

## 4. 开源工具模拟映射

### 4.1 按 APT 行为选择工具

```
如果模拟 APT29（高 OPSEC + 云环境攻击）:
├─ C2: Sliver / Brute Ratel
├─ 云攻击: ROADtools / AADInternals / GraphRunner
├─ 投递: 自定义 HTML Smuggling + ISO
├─ 凭据: Rubeus + NanoDump
├─ 横向: Evil-WinRM
└─ 持久化: 自定义 Azure AD App

如果模拟 APT28（快速激进 + 漏洞利用）:
├─ C2: Cobalt Strike / Havoc
├─ 投递: Office 宏 + 钓鱼页面
├─ 凭据: Mimikatz + Responder
├─ 横向: PsExec / SMBExec / RDP
├─ 提权: 内核漏洞利用
└─ 外传: 自定义 Exfil 脚本

如果模拟 Volt Typhoon（纯 LOLBins）:
├─ C2: 无（使用 SSH/RDP 合法协议）
├─ 投递: 漏洞利用 + 合法凭据
├─ 凭据: ntdsutil / reg save / comsvcs.dll MiniDump
├─ 横向: 原生 RDP/SMB/SSH
├─ 侦察: 全部使用系统命令
└─ 持久化: 合法账户 + 路由器后门

如果模拟 Lazarus（社会工程 + 金融目标）:
├─ C2: Mythic / Havoc
├─ 投递: 定制化社会工程（招聘/加密货币主题）
├─ 凭据: Mimikatz
├─ 横向: SMB + RDP
├─ 特殊: 加密货币相关应用模拟
└─ 外传: 加密 + 多层代理
```

### 4.2 通用模拟工具栈

| 功能 | 工具 | 适用 APT 模拟 |
|------|------|--------------|
| C2 框架 | Cobalt Strike | APT28, APT41, FIN7 |
| C2 框架 | Sliver | APT29, Turla |
| C2 框架 | Havoc | Lazarus, APT38 |
| C2 框架 | Mythic | 通用 |
| C2 框架 | Brute Ratel | APT29 |
| 自动化模拟 | MITRE CALDERA | 多 APT 自动化 |
| 原子测试 | Atomic Red Team | 单 TTP 验证 |
| AD 攻击 | Impacket | 所有 |
| AD 攻击 | Rubeus | APT29, APT28 |
| AD 攻击 | Certify / Certipy | ADCS 场景 |
| 凭据 | Mimikatz | 所有 |
| 凭据 | NanoDump | APT29 (高 OPSEC) |
| 凭据 | SharpDPAPI | APT29, Turla |
| 隧道 | Chisel | Lazarus |
| 隧道 | Ligolo-ng | 所有 |
| 云攻击 | ROADtools | APT29 |
| 云攻击 | AADInternals | APT29 |
| 社工 | GoPhish | APT28, FIN7, Lazarus |
| 社工 | Evilginx2 | APT28 (MFA 绕过) |

---

## 5. 时间模式分析

### 5.1 工作时间分析

```
APT 组织工作时间（UTC，根据公开研究）:

俄罗斯 APT（APT28/29/Turla/Sandworm）:
├─ 主要活动: UTC 05:00 - 15:00（莫斯科时间 08:00-18:00）
├─ 工作日: 周一至周五
├─ 假期: 俄罗斯国家假日（1月1-8日新年、5月1-3日劳动节等）
├─ 特征: Turla/APT29 会有少量周末活动
└─ 例外: Sandworm 的破坏性攻击选择目标时区的非工作时间

中国 APT（APT41/Salt Typhoon/Volt Typhoon）:
├─ 主要活动: UTC 00:00 - 10:00（北京时间 08:00-18:00）
├─ 工作日: 周一至周五
├─ 假期: 中国国家假日（春节、国庆等）
├─ 特征: APT41 的犯罪活动在非工作时间（晚上和周末）
└─ 特征: Volt Typhoon 活动频率极低，难以判断时间模式

朝鲜 APT（Lazarus/APT38）:
├─ 主要活动: UTC 00:00 - 09:00（平壤时间 09:00-18:00）
├─ 工作日: 周一至周六（朝鲜六天工作制）
├─ 假期: 朝鲜国家假日较少
├─ 特征: 金融攻击选择目标银行的结算窗口期
└─ 特征: 加密货币攻击选择亚洲交易所营业时间

犯罪组织（FIN7）:
├─ 活动时间: 不固定，但偏向东欧时间
├─ 工作日: 周一至周五（像正规公司运营）
└─ 特征: 钓鱼邮件在目标地区的工作时间发送
```

### 5.2 红队模拟时如何匹配时间模式

```
时间模拟策略:
├─ 如果模拟 APT29 → 在 UTC 05:00-15:00 活动
│   Beacon sleep 在非工作时间设为长间隔
│   周末减少操作
│
├─ 如果模拟 APT41 → 在 UTC 00:00-10:00 活动
│   犯罪活动放在 UTC 10:00-16:00（北京时间晚上）
│
├─ 如果模拟 Lazarus → 在 UTC 00:00-09:00 活动
│   金融攻击在目标银行非工作时间执行
│
└─ Beacon Sleep 配置:
    工作时间: sleep 60s, jitter 30%
    非工作时间: sleep 3600s-86400s, jitter 50%
    匹配 APT 的真实通信节奏
```

### 5.3 攻击活动持续时间参考

| APT 组织 | 初始侦察 | 初始入侵 | 驻留建立 | 目标达成 | 总周期 |
|----------|---------|---------|---------|---------|--------|
| APT28 | 1-2 周 | 1-3 天 | 1-2 周 | 2-4 周 | 1-2 月 |
| APT29 | 2-4 周 | 1-7 天 | 2-4 周 | 数月 | 6-18 月 |
| APT41 | 1-2 周 | 1-3 天 | 1-2 周 | 2-4 周 | 1-3 月 |
| Lazarus | 2-4 周 | 1-7 天 | 2-4 周 | 4-12 周 | 3-12 月 |
| FIN7 | 1 周 | 1-3 天 | 3-7 天 | 1-2 周 | 2-6 周 |
| Turla | 2-4 周 | 1-7 天 | 4-8 周 | 数月 | 12-36 月 |
| Sandworm | 2-4 周 | 1-7 天 | 4-12 周 | 选定时机 | 3-12 月 |
| Volt Typhoon | 未知 | 1-7 天 | 数周 | 预置（不执行） | 年级别 |

---

## 6. 红队模拟执行模板

### 6.1 模拟规划清单

```
模拟准备阶段:
[ ] 选定模拟的 APT 组织（根据目标行业）
[ ] 收集该 APT 最新的 TTP 报告（不少于 3 份来源）
[ ] 映射 MITRE ATT&CK 技术到具体操作
[ ] 确认 Rules of Engagement（授权范围）
[ ] 选择工具栈（匹配 APT 行为，非简单替代）
[ ] 搭建匹配 APT 风格的 C2 基础设施
[ ] 制定时间线（匹配 APT 的活动节奏）
[ ] 准备检测差距记录模板
[ ] 确认紧急联系人和停止条件

模拟执行阶段:
[ ] 按 APT 时区/工作时间操作
[ ] 每步操作记录: 时间/TTP ID/检测状态
[ ] 按 APT 的行为模式间隔操作（不要一天做完）
[ ] 如被部分检测到 → 记录并评估是否继续
[ ] 保持备用 C2 通道可用

模拟结束阶段:
[ ] 生成 ATT&CK Navigator 热力图（检测覆盖率）
[ ] 记录每步操作的检测/遗漏状态
[ ] 根因分析: 为什么被检测到/为什么没被检测到
[ ] 修复建议按优先级排列
[ ] 销毁所有模拟基础设施
```

---

## 关联参考

- **APT 模拟方法论** → `../SKILL.md`
- **C2 基础设施 OPSEC** → `/skills/threat-intel/ioc-analysis/references/c2-infra-opsec.md`
- **检测规则绕过** → `/skills/threat-intel/threat-hunting-evasion/references/detection-rules-bypass.md`
- **红队评估** → `/skills/general/red-team-assessment/SKILL.md`
