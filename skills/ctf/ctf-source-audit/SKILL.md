---
name: ctf-source-audit
description: "CTF 挑战中的源码审计方法。当通过 .git 泄露、备份文件下载、LFI 读取等方式获取到目标源码时使用。与真实代码审计不同——CTF 源码中的漏洞是故意设置的，通常只有 1-2 个关键点。覆盖 PHP/Python/Node.js/Java 的常见 CTF 漏洞模式"
metadata:
  tags: "ctf,source,audit,code review,源码审计,php,python,node,java,代码审计,SAST"
  difficulty: "medium"
  icon: "📝"
  category: "CTF"
---

# CTF 源码审计方法论

CTF 源码审计 ≠ 真实代码审计。区别：
- 真实审计：几万行代码，漏洞可能在任何地方
- CTF 审计：**几十到几百行代码，漏洞是故意设置的，通常很明显**

核心策略：**找危险函数**（sink），然后追溯输入（source）到危险函数的路径。

## ⛔ 深入参考（必读）

- ⛔**必读** PHP/Python/Node.js 完整危险函数清单、漏洞模式（弱比较/变量覆盖/条件竞争） → `read_skill(id="ctf-source-audit", path="references/dangerous-functions.md")`

## Step 1: 快速定位危险函数

| 语言 | 命令执行 | 反序列化 | 模板注入 |
|------|----------|----------|----------|
| PHP | `system()` `eval()` `exec()` | `unserialize()` | N/A |
| Python | `os.system()` `eval()` `exec()` | `pickle.loads()` `yaml.load()` | `render_template_string()` |
| Node.js | `child_process.exec()` `eval()` | N/A | `__proto__` 原型链污染 |

→ 完整危险函数清单 → `read_skill(id="ctf-source-audit", path="references/dangerous-functions.md")`

## Step 2: 追踪数据流（sink → source）

1. **参数从哪来？** — `$_GET`, `request.args`, `req.body`
2. **有没有过滤？** — 搜 `filter`, `sanitize`, `escape`
3. **过滤能绕过吗？** — CTF 中通常有绕过（黑名单遗漏、双重编码、大小写）

## Step 3: 常见 CTF 漏洞模式速查

- **PHP 弱比较**：`== '0e...'` → true | `md5([])===md5([])`
- **变量覆盖**：`extract($_GET)` / `parse_str()`
- **逻辑漏洞**：`admin ` (trailing space) | 金额负数

→ 完整模式和代码示例 → `read_skill(id="ctf-source-audit", path="references/dangerous-functions.md")`

## Step 4: 审计产出
1. 漏洞类型和位置（文件名+行号）
2. 利用方法（构造什么请求触发）
3. Flag 获取路径

## PHP 数组绕过
- md5(array) 返回 NULL，可绕过比较
- GET 参数数组语法：`a[]=1&b[]=2`

## 变量覆盖
- register_globals 历史漏洞及类似原理（extract/parse_str）
