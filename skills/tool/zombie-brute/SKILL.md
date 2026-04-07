---
name: zombie-brute
description: "使用 zombie 进行多协议暴力破解。zombie 是 chainreactors 出品的高性能暴力破解工具，支持 SSH/FTP/MySQL/MSSQL/PostgreSQL/Redis/SMB/RDP/SNMP/LDAP/VNC 等 20+ 协议，内置智能字典生成和分布式模式。与 hydra 的区别：zombie 支持更多协议、更快的并发、以及基于规则的字典生成。当需要批量弱口令检测、凭据喷洒时使用此技能"
metadata:
  tags: "zombie,brute,bruteforce,暴力破解,弱口令,密码,ssh,rdp,mysql,redis,smb,chainreactors,hydra"
  category: "tool"
---

# zombie 多协议暴力破解

zombie 专注于**暴力破解的效率和覆盖面**——支持 20+ 协议、内置智能字典生成、支持凭据喷洒模式（一个密码试所有用户，避免锁定）。

项目地址：https://github.com/chainreactors/zombie

## 基本用法

```bash
# SSH 暴力破解
zombie -i 10.0.0.1 -s ssh -u root -P passwords.txt

# 指定用户名和密码文件
zombie -i 10.0.0.1 -s ssh -U users.txt -P passwords.txt

# MySQL 暴力破解
zombie -i 10.0.0.1 -s mysql -u root -P passwords.txt

# Redis 未授权 + 密码检测
zombie -i 10.0.0.1 -s redis -P passwords.txt

# RDP 暴力破解
zombie -i 10.0.0.1 -s rdp -u administrator -P passwords.txt
```

## 批量目标

```bash
# 从文件读取目标（每行 ip:port）
zombie -l targets.txt -s ssh -U users.txt -P passwords.txt

# 网段扫描 + 爆破
zombie -i 10.0.0.0/24 -s ssh -u root -p admin123

# 多协议同时爆破
zombie -i 10.0.0.1 -s ssh,mysql,redis,ftp -U users.txt -P passwords.txt
```

## 凭据喷洒模式

凭据喷洒（一个密码试所有用户）比传统爆破（一个用户试所有密码）更安全——不容易触发账户锁定：

```bash
# 喷洒模式
zombie -i 10.0.0.0/24 -s smb -U domain_users.txt -p 'P@ssw0rd' --spray

# 多密码喷洒（每轮一个密码）
zombie -i 10.0.0.0/24 -s smb -U domain_users.txt -P top10.txt --spray
```

## 并发与超时

```bash
# 调整并发线程（默认 10）
zombie -i 10.0.0.0/24 -s ssh -u root -P passwords.txt -t 50

# 超时设置（秒）
zombie -i 10.0.0.1 -s rdp -u admin -P passwords.txt --timeout 10

# 成功后停止
zombie -i 10.0.0.1 -s ssh -u root -P passwords.txt --stop-on-success
```

## 支持的协议

SSH, FTP, MySQL, MSSQL, PostgreSQL, Redis, MongoDB, Memcached, SMB, RDP, VNC, SNMP, LDAP, SMTP, POP3, IMAP, HTTP-Basic, HTTP-Form, Telnet, Oracle

## 决策树

```
需要爆破什么？
├─ 单协议爆破 + 简单场景 → zombie / hydra 都行
├─ 多协议批量 + 大规模 → zombie（更快、协议更全）
├─ 域环境凭据喷洒 → zombie --spray 或 nxc
├─ 需要内网综合扫描+弱口令 → fscan（集成扫描+爆破）
└─ Web 表单爆破 → zombie / hydra / ffuf
```
