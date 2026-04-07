---
name: hashcat-crack
description: "使用 hashcat 进行密码哈希离线破解。当获取到密码哈希（NTLM/NTLMv2/Kerberos TGS/AS-REP/SHA/MD5/bcrypt/NetNTLMv2）需要还原明文密码时使用。hashcat 是 GPU 加速的密码破解工具，比 john 快几十倍。覆盖哈希类型识别、字典攻击、规则攻击、掩码攻击、组合攻击。拿到 hashdump/secretsdump/Kerberoast/AS-REP 输出后必用此技能"
metadata:
  tags: "hashcat,crack,hash,password,ntlm,kerberos,tgs,md5,sha,密码,破解,GPU,john,哈希"
  category: "tool"
---

# hashcat 密码哈希离线破解

hashcat 利用 GPU 加速哈希破解，速度远超 CPU。核心工作流：**识别哈希类型 → 选择攻击模式 → 喂字典/规则/掩码**。

## 哈希类型识别（-m 参数）

| 哈希类型 | -m 值 | 来源 |
|----------|-------|------|
| NTLM | 1000 | hashdump / secretsdump |
| NetNTLMv2 | 5600 | Responder / ntlmrelayx 抓包 |
| Kerberos TGS (Kerberoast) | 13100 | GetUserSPNs.py |
| Kerberos AS-REP | 18200 | GetNPUsers.py |
| MD5 | 0 | Web 数据库泄露 |
| SHA-256 | 1400 | — |
| SHA-512 | 1800 | Linux /etc/shadow ($6$) |
| bcrypt | 3200 | Web 应用 |
| DCC2 (Domain Cached Credentials 2) | 2100 | secretsdump 域缓存凭据 |
| WPA-PBKDF2 | 22000 | WiFi 握手包 |

## 攻击模式

### 字典攻击（最常用）

```bash
# 基本字典攻击
hashcat -m 1000 hashes.txt /usr/share/wordlists/rockyou.txt

# 加规则（变形字典，如 password → Password1!）
hashcat -m 1000 hashes.txt /usr/share/wordlists/rockyou.txt -r /usr/share/hashcat/rules/best64.rule

# 常用规则文件
# best64.rule — 64 条高效规则，速度和效果平衡
# rockyou-30000.rule — 大规则集，覆盖更多变形
# OneRuleToRuleThemAll.rule — 社区最强规则集
```

### 掩码攻击（已知密码模式）

```bash
# 8 位纯数字
hashcat -m 1000 hashes.txt -a 3 ?d?d?d?d?d?d?d?d

# 首字母大写 + 6 位小写 + 1 位数字（如 Password1）
hashcat -m 1000 hashes.txt -a 3 ?u?l?l?l?l?l?l?d

# 掩码字符集：?l=小写 ?u=大写 ?d=数字 ?s=特殊 ?a=全部
```

### 组合攻击

```bash
# 两个字典组合（word1+word2）
hashcat -m 1000 hashes.txt -a 1 dict1.txt dict2.txt
```

## 实战场景

### Kerberoast 破解

```bash
# GetUserSPNs.py 输出 → hashcat
GetUserSPNs.py domain/user:pass -dc-ip DC_IP -request -outputfile tgs.txt
hashcat -m 13100 tgs.txt /usr/share/wordlists/rockyou.txt -r /usr/share/hashcat/rules/best64.rule
```

### AS-REP Roasting 破解

```bash
GetNPUsers.py domain/ -usersfile users.txt -no-pass -dc-ip DC_IP -outputfile asrep.txt
hashcat -m 18200 asrep.txt /usr/share/wordlists/rockyou.txt
```

### NTLM 哈希破解（hashdump/secretsdump）

```bash
# secretsdump 输出格式：user:RID:LM:NTLM:::
# 提取 NTLM 部分
cat secretsdump.txt | awk -F: '{print $4}' | sort -u > ntlm.txt
hashcat -m 1000 ntlm.txt /usr/share/wordlists/rockyou.txt -r /usr/share/hashcat/rules/best64.rule
```

### NetNTLMv2 破解（Responder 抓取）

```bash
hashcat -m 5600 responder_hashes.txt /usr/share/wordlists/rockyou.txt
```

## 实用参数

```bash
# 查看已破解结果
hashcat -m 1000 hashes.txt --show

# 继续中断的任务
hashcat -m 1000 hashes.txt --restore

# 只跑 GPU（不用 CPU）
hashcat -m 1000 hashes.txt -D 2

# 设置工作负载（1=低 2=默认 3=高 4=极限）
hashcat -m 1000 hashes.txt -w 3

# 输出到文件
hashcat -m 1000 hashes.txt wordlist.txt -o cracked.txt
```

## 决策树

```
拿到哈希后：
├─ 知道哈希类型 → 直接 hashcat -m 值
├─ 不确定类型 → hashcat --identify hashes.txt 或 hashid
├─ 有 GPU → hashcat（首选）
├─ 无 GPU / CPU 环境 → john the ripper
└─ 在线查询 → hashes.org / crackstation.net（先试再跑）
```
