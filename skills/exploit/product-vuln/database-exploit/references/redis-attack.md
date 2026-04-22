# Redis 攻击详解

## 1. 未授权访问利用

写 Webshell / SSH 公钥 / Crontab 是 Redis 未授权的核心利用手法。

## 2. 主从复制 RCE

通过伪造 Redis Master 节点，利用主从复制功能向目标加载恶意 .so 模块实现 RCE。

## 3. Lua 沙箱逃逸

特定版本中 Lua 沙箱存在逃逸漏洞，可通过 EVAL 命令执行系统命令。

## 4. Redis 有密码时

```bash
# 爆破
hydra -P /usr/share/wordlists/rockyou.txt redis://TARGET

# 使用 netexec
netexec redis TARGET -p /usr/share/wordlists/redis_passwords.txt

# 连接时带密码
redis-cli -h TARGET -a PASSWORD
```

## 5. Redis Cluster / Sentinel

```bash
# Redis Sentinel 信息泄露
redis-cli -h TARGET -p 26379
SENTINEL masters
SENTINEL get-master-addr-by-name mymaster
# 获取真正的 Redis master 地址

# Cluster 信息
redis-cli -h TARGET
CLUSTER INFO
CLUSTER NODES
```

## 6. 信息收集

```bash
redis-cli -h TARGET
INFO                   # 全量信息
INFO server            # Redis 版本、OS
INFO keyspace          # 数据库和 key 数量
DBSIZE                 # 当前 db 的 key 数
KEYS *                 # 列出所有 key（慎用，key 多会卡死）
SCAN 0 COUNT 100       # 安全遍历
CONFIG GET *           # 所有配置

# 搜索 flag
KEYS *flag*
GET flag
```
