---
name: ctf-flag-hunting
description: "CTF 挑战中的 Flag 搜索策略。当已获取命令执行/文件读取/数据库访问权限但不知道 flag 在哪里时使用。覆盖文件系统、数据库、环境变量、源码、内存等所有 flag 可能的存储位置。按成功率排序的搜索优先级"
metadata:
  tags: "ctf,flag,搜索,hunting,文件系统,数据库,环境变量,rce,getflag"
  difficulty: "easy"
  icon: "🎯"
  category: "CTF"
---

# CTF Flag 搜索策略

你已经拿到了某种程度的权限（RCE/文件读取/数据库访问/管理后台），但不知道 flag 在哪里。本方法论按成功率排序搜索路径。

## 按权限类型选择搜索策略

### 情况 A: 有命令执行（RCE）

这是最理想的情况，按以下顺序搜索：

**1. 常见 flag 文件路径（先试这些，通常 1-2 个命中）**
```bash
cat /flag
cat /flag.txt
cat /flag.php
cat /root/flag.txt
cat /home/*/flag.txt
cat /var/www/html/flag.php
cat /var/www/flag.txt
cat /tmp/flag
cat /opt/flag.txt
```

**2. 文件系统搜索**
```bash
find / -name "flag*" 2>/dev/null
find / -name "*.flag" 2>/dev/null
grep -r "FLAG{" / --include="*.txt" --include="*.php" 2>/dev/null
grep -r "flag" /var/www/ 2>/dev/null
```

**3. 环境变量**
```bash
env | grep -i flag
printenv FLAG
cat /proc/1/environ | tr '\0' '\n' | grep FLAG
```

**4. 数据库配置文件 → 连接数据库找 flag**
```bash
cat /var/www/html/config.php       # PHP
cat /var/www/html/.env             # Laravel/通用
cat /var/www/html/application.yml  # Java
cat /app/config.py                 # Python
```
找到数据库凭据后连接查询（见下方「情况 C」）

**5. 进程和网络**
```bash
ps aux                    # flag 可能在其他进程的命令行参数里
cat /proc/*/cmdline       # 同上
netstat -tlnp             # 可能有内网服务藏着 flag
```

### 情况 B: 有文件读取（LFI/任意文件读取）

**按优先级读取：**
1. `/flag.txt`, `/flag`, `/flag.php`
2. `/etc/passwd` — 确认可读性，看有哪些用户
3. `/var/www/html/config.php` — 数据库凭据
4. `/proc/self/environ` — 环境变量中的 flag
5. `/proc/self/cmdline` — 启动命令中的 flag
6. 源码文件 — 从中发现更多漏洞

**LFI 转 RCE 的方法**（如果直接读不到 flag）：
- PHP session 文件写入：`/tmp/sess_[PHPSESSID]`
- 日志文件注入：`/var/log/apache2/access.log`
- `/proc/self/fd/[N]` — 文件描述符
- php://filter + php://input

### 情况 C: 有数据库访问（SQLi/数据库凭据）

**SQL 注入搜索**：
```sql
-- 1. 找所有数据库
SHOW DATABASES;
-- 2. 每个库里找表
SHOW TABLES;
-- 3. 找可疑表名
SELECT * FROM flag;
SELECT * FROM flags;
SELECT * FROM secret;
SELECT * FROM ctf;
SELECT * FROM admin;
-- 4. 全表搜索 FLAG 关键字（MySQL）
SELECT table_name, column_name FROM information_schema.columns
WHERE column_name LIKE '%flag%';
```

**MySQL 文件读取**（如果有 FILE 权限）：
```sql
SELECT LOAD_FILE('/flag.txt');
SELECT LOAD_FILE('/etc/passwd');
```

### 情况 D: 只有 Web 管理后台权限

1. 翻遍所有页面和菜单 — flag 可能在某个配置页/用户信息中
2. 检查「系统信息」「关于」「调试」页面
3. 查看用户列表 — flag 可能在某个用户的 notes/bio/email 字段
4. 检查文件管理功能 — 读取服务器文件
5. 检查模板编辑功能 — 可能注入代码（SSTI/代码执行）

## Flag 格式识别

常见 flag 格式：
- `FLAG{hex_string}` — 最常见（xbow benchmark 默认格式）
- `flag{string}` — 小写变体
- `CTF{string}`, `ctf{string}`
- 纯字符串（无包裹格式）— 题目会说明

用 Python 正则搜索：
```python
import re
# 匹配所有常见 flag 格式
patterns = [
    r'FLAG\{[a-fA-F0-9_-]+\}',
    r'flag\{[^\}]+\}',
    r'CTF\{[^\}]+\}',
]
```

## 注意事项
- **假 flag 陷阱**：`FLAG{test}`, `FLAG{this_is_not_the_flag}` 是常见的迷惑项
- **Flag 位置暗示**：题目描述有时会暗示 flag 在哪（"数据库里有秘密"→SQL注入）
- **拿到 flag 后立即验证**：参考 `ctf-flag-verification` 技能
