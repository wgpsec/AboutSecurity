---
id: JAVA-RMI-CODEBASE
title: Java RMI Codebase 远程代码执行漏洞
product: java
vendor: Oracle
version_affected: "<=JDK 7u21, <=JDK 8u121"
severity: CRITICAL
tags: [rce, rmi, 无需认证]
fingerprint: ["Java RMI"]
---

## 漏洞描述

Java RMI 客户端可以通过指定 `java.rmi.server.codebase` 参数使服务端加载远程对象。当 RMI 服务配置不当时，攻击者可以操控 codebase 指向恶意服务器，执行任意 Java 字节码。

## 影响版本

- JDK <= 7u21
- JDK <= 8u121

## 前置条件

- 目标 RMI 服务允许远程 codebase
- 攻击者能访问 RMI Registry 端口（默认 1099）

## 利用步骤

1. 启动恶意 RMI 服务器
2. 让目标连接并加载攻击者的远程对象
3. 执行任意代码

## Payload

```bash
# 启动恶意 RMI 服务器
# 需要编写并编译恶意 Java 类
# 启动 JRMPListener
java -cp ysoserial.jar ysoserial.exploit.JRMPListener <port> <gadget> <command>
```

## 验证方法

```bash
# 检查是否能连接到目标 RMI 服务
nc -zv target 1099
```

## 修复建议

1. 升级 JDK 至最新版本
2. 设置 `java.rmi.server.useCodebaseOnly=true`
3. 禁用 RMI 远程 codebase 加载
