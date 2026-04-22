---
id: PHP-FPM-FASTCGI-UNAUTHORIZED
title: PHP-FPM FastCGI 未授权访问漏洞
product: php
vendor: PHP
version_affected: "任意版本（配置相关）"
severity: CRITICAL
tags: [rce, 无需认证]
fingerprint: ["PHP-FPM"]
---

## 漏洞描述

PHP-FPM（FastCGI 进程管理器）是一个替代性的 PHP FastCGI 实现。当 PHP-FPM 在没有适当访问控制的情况下暴露在网络中时，FastCGI 接口可被未经授权访问，攻击者可以执行任意 PHP 代码。

## 影响版本

- 任意版本（取决于配置）

## 前置条件

- 无需认证
- PHP-FPM 端口（默认9000）暴露在网络中
- 没有配置防火墙限制访问

## 利用步骤

1. 使用 FastCGI 协议客户端连接目标 PHP-FPM 端口
2. 发送精心构造的请求执行任意 PHP 代码

## Payload

```bash
# 使用 FastCGI 客户端工具
# 参考: https://gist.github.com/phith0n/9615e2420f31048f7e30f3937356cf75
```

## 验证方法

```bash
# 工具执行后会返回 PHP 代码执行结果
```

## 修复建议

1. 配置防火墙限制访问 PHP-FPM 端口
2. 使用 UNIX socket 代替 TCP 端口
3. 配置 php-fpm.conf 中的 security.limit_extensions
