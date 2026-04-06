# CTF Flag 搜索完整路径

## 情况 A: 有命令执行（RCE）

**1. 常见 flag 文件路径（先试这些）**
```bash
cat /flag
cat /flag.txt
cat /flag.php
cat /root/flag.txt
cat /home/*/flag.txt
cat /var/www/html/flag.php
cat /tmp/flag
cat /opt/flag.txt
```

**2. 文件系统搜索**
```bash
find / -name "flag*" 2>/dev/null
grep -r "flag{" / --include="*.txt" --include="*.php" 2>/dev/null
```

**3. 环境变量**
```bash
env | grep -i flag
cat /proc/1/environ | tr '\0' '\n' | grep FLAG
```

**4. 数据库配置 → 连接数据库**
```bash
cat /var/www/html/config.php
cat /var/www/html/.env
cat /app/config.py
```

**5. 进程和网络**
```bash
ps aux                    # flag 可能在进程命令行参数里
netstat -tlnp             # 内网服务可能藏着 flag
```

## 情况 B: 有文件读取（LFI）

按优先级：
1. `/flag.txt`, `/flag`, `/flag.php`, `/.flag`, `/flag.md`
2. 路径遍历：对 `../`、`../../`、`../../../` 每个深度都同时尝试 `flag`、`flag.txt`、`.flag`
3. `/etc/passwd` — 确认可读性
4. `/var/www/html/config.php` — 数据库凭据
5. `/proc/self/environ` — 环境变量中的 flag
6. 源码文件 — 发现更多漏洞

> ⚠️ 路径遍历时必须同时发送带后缀和不带后缀的变体，不要只试 `../flag` 不试 `../flag.txt`

LFI 转 RCE：PHP session 文件写入、日志投毒、php://filter

## 情况 C: 有数据库访问（SQLi）

```sql
SHOW DATABASES;
SHOW TABLES;
SELECT * FROM flag;
SELECT * FROM flags;
SELECT * FROM secret;
SELECT table_name, column_name FROM information_schema.columns WHERE column_name LIKE '%flag%';
SELECT LOAD_FILE('/flag.txt');  -- 需要 FILE 权限
```

## 情况 D: 只有 Web 管理后台

1. 翻遍所有页面 — flag 可能在配置页/用户信息中
2. 检查「系统信息」「关于」「调试」页面
3. 查看用户列表 — flag 可能在 notes/bio/email 字段
4. 检查文件管理/模板编辑功能
