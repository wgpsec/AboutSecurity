---
name: ctf-source-audit
description: "CTF 挑战中的源码审计方法。当通过 .git 泄露、备份文件下载、LFI 读取等方式获取到目标源码时使用。与真实代码审计不同——CTF 源码中的漏洞是故意设置的，通常只有 1-2 个关键点。覆盖 PHP/Python/Node.js/Java 的常见 CTF 漏洞模式"
metadata:
  tags: "ctf,source,audit,code review,源码审计,php,python,node,java,代码审计"
  difficulty: "medium"
  icon: "📝"
  category: "CTF"
---

# CTF 源码审计方法论

CTF 源码审计 ≠ 真实代码审计。区别：
- 真实审计：几万行代码，漏洞可能在任何地方
- CTF 审计：**几十到几百行代码，漏洞是故意设置的，通常很明显**

核心策略：**找危险函数**（sink），然后追溯输入（source）到危险函数的路径。

## Step 1: 快速定位危险函数

### PHP 危险函数（最常见的 CTF 语言）

**命令执行**：
- `system()`, `exec()`, `passthru()`, `shell_exec()`, `popen()`
- 反引号 `` `$cmd` ``
- `preg_replace('/e', ...)` — PHP < 7.0 的 /e 修饰符可执行代码

**代码执行**：
- `eval()`, `assert()` — 直接执行 PHP 代码
- `create_function()` — 等价于 eval
- `call_user_func()`, `call_user_func_array()` — 动态函数调用

**文件操作**：
- `include()`, `require()`, `include_once()`, `require_once()` — LFI
- `file_get_contents()`, `readfile()`, `fopen()` — 任意文件读取
- `file_put_contents()`, `fwrite()` — 任意文件写入 → webshell
- `unlink()` — 任意文件删除
- `move_uploaded_file()` — 文件上传

**反序列化**：
- `unserialize()` — 搜索 `__wakeup`, `__destruct`, `__toString` 魔术方法构造 POP 链

**SQL 相关**：
- 字符串拼接 SQL：`"SELECT * FROM users WHERE id=".$_GET['id']` — SQL 注入
- `mysql_query()`, `mysqli_query()`, `PDO::query()` — 看参数是否来自用户输入

### Python 危险函数

**命令执行**：
- `os.system()`, `os.popen()`, `subprocess.*`
- `eval()`, `exec()` — 代码执行

**反序列化**：
- `pickle.loads()`, `yaml.load()` (无 Loader 参数) — RCE
- `marshal.loads()`

**模板注入**：
- `render_template_string(user_input)` — Jinja2 SSTI
- `Template(user_input).render()` — SSTI

**Flask 特有**：
- `app.secret_key` — 如果泄露，可以伪造 session
- `@app.route` 中缺少认证装饰器 — 未授权访问

### Node.js 危险函数

**命令执行**：
- `child_process.exec()`, `child_process.spawn()`
- `eval()`, `new Function()`

**原型链污染**：
- `Object.assign()`, `_.merge()`, `_.set()` — 当 source 来自用户输入时
- 递归合并函数 — `__proto__` 或 `constructor.prototype` 注入

**模板注入**：
- EJS: `<%= user_input %>` 有时可注入
- Pug/Jade: 模板编译时注入

## Step 2: 追踪数据流

找到危险函数后，从 sink 反向追踪到 source：

1. **参数从哪来？** — `$_GET`, `$_POST`, `$_COOKIE`, `$_FILES`, `request.args`, `req.body`
2. **中间有没有过滤？** — 搜索 `filter`, `sanitize`, `escape`, `htmlspecialchars`, `strip`
3. **过滤能绕过吗？** — CTF 中的过滤通常有绕过方式（黑名单遗漏、双重编码、大小写）

## Step 3: 常见 CTF 源码漏洞模式

### 弱比较（PHP 最常见）
```php
if ($_GET['password'] == '0e123456') { ... }  // "0e..." == 0 → true
if (md5($a) == md5($b)) { ... }  // 0e 开头的 MD5 碰撞
if ($a != $b && md5($a) === md5($b)) { ... }  // 需要数组绕过 md5([])===md5([])
```

### 变量覆盖
```php
extract($_GET);  // GET 参数覆盖任意变量
parse_str($str); // 解析字符串为变量
$$key = $value;  // 可变变量
```

### 条件竞争
```php
move_uploaded_file($tmp, $target);  // 上传
// 检查并删除恶意文件（有时间窗口）
if (is_malicious($target)) unlink($target);
```
→ 在检查前访问上传的文件

### 逻辑漏洞
- 注册时 username 为 `admin` 被禁止 → 试 `admin ` (trailing space) 或 `Admin`
- 金额/积分为负数 → 购买时扣负数 = 加钱
- 密码重置 token 可预测 → 基于时间戳或弱随机数

## Step 4: 审计产出

审计完成后应输出：
1. **漏洞类型和位置** — 具体文件名和行号
2. **利用方法** — 构造什么样的请求可以触发
3. **Flag 获取路径** — 漏洞利用后如何读取 flag
