---
name: database-tactics
description: "数据库服务攻击方法论。当发现 Redis(6379)、MSSQL(1433)、PostgreSQL(5432)、MySQL(3306)、MongoDB(27017) 等数据库端口时使用。覆盖未授权访问、弱口令爆破、命令执行、文件读写、提权。任何涉及数据库攻击、数据库提权、数据库利用的场景都应使用此技能"
metadata:
  tags: "database,redis,mssql,postgresql,mysql,mongodb,数据库,未授权,命令执行,提权,6379,1433,5432,3306"
  category: "postexploit"
---

# 数据库服务攻击方法论

数据库是内网渗透的核心跳板——几乎每个应用都有数据库后端，而数据库通常有操作系统级的能力。

## ⛔ 深入参考（必读）

- Redis 攻击（未授权/写文件/主从复制RCE）→ [references/redis-attack.md](references/redis-attack.md)
- MSSQL 攻击（xp_cmdshell/CLR/提权）→ [references/mssql-attack.md](references/mssql-attack.md)
- PostgreSQL 攻击（命令执行/文件读写/提权）→ [references/postgresql-attack.md](references/postgresql-attack.md)

---

## Phase 1: 数据库识别

| 端口 | 服务 | 攻击优先级 |
|------|------|-----------|
| 6379 | Redis | ⭐⭐⭐ 未授权概率高 |
| 1433 | MSSQL | ⭐⭐⭐ xp_cmdshell 直接 RCE |
| 5432 | PostgreSQL | ⭐⭐ 命令执行能力强 |
| 3306 | MySQL | ⭐⭐ UDF 提权 |
| 27017 | MongoDB | ⭐⭐ 未授权概率高 |
| 1521 | Oracle | ⭐ 利用复杂 |

## Phase 2: 通用攻击流程

```
发现数据库端口？
├─ 1. 尝试未授权访问（空密码/匿名）
├─ 2. 弱口令爆破（默认账号 + top100）
├─ 3. 已知漏洞利用
├─ 4. 进入数据库后：
│   ├─ 搜索敏感数据（用户表/配置表/flag）
│   ├─ 尝试命令执行
│   └─ 尝试文件读写
└─ 5. 操作系统提权
```

## Phase 3: 快速未授权检测

```bash
# Redis
redis-cli -h TARGET ping
# 返回 PONG → 未授权

# MSSQL（默认 sa 账号）
netexec mssql TARGET -u sa -p '' --local-auth
netexec mssql TARGET -u sa -p 'sa' --local-auth

# PostgreSQL
psql -h TARGET -U postgres -w
# 空密码测试

# MySQL
mysql -h TARGET -u root --skip-password

# MongoDB
mongosh --host TARGET --eval "db.adminCommand('listDatabases')"
```

## Phase 4: 弱口令爆破

```bash
# 通用爆破（netexec 支持多种协议）
netexec mssql TARGET -u userlist.txt -p passlist.txt --local-auth
netexec ssh TARGET -u userlist.txt -p passlist.txt

# 常见默认账号
# Redis: 无认证 / requirepass 常为弱密码
# MSSQL: sa / sa, sa / 空, sa / 123456
# PostgreSQL: postgres / postgres, postgres / 空
# MySQL: root / root, root / 空, root / 123456
# MongoDB: admin / admin, 无认证
```

## Redis 速查（最常见）

```bash
# 未授权连接
redis-cli -h TARGET

# 信息收集
INFO server
CONFIG GET dir
CONFIG GET dbfilename
```

**Redis 关键利用路径：**
- 写 Webshell / SSH 密钥 / Crontab
- 主从复制 RCE
- Lua 沙箱逃逸

→ 密码爆破 / Cluster / Sentinel 详情 → [references/redis-attack.md](references/redis-attack.md)

## MSSQL 速查

```bash
# 连接
impacket-mssqlclient DOMAIN/sa:PASSWORD@TARGET -windows-auth
```

**MSSQL 关键利用路径：**
- xp_cmdshell / OLE / Agent Job RCE
- CLR Assembly 攻击
- 文件读写
- NTLM Hash 窃取

→ 信息收集 / 提权方法论 → [references/mssql-attack.md](references/mssql-attack.md)

## MySQL 速查

**MySQL 关键利用路径：**
- UDF 提权 / 文件读写
