---
name: ctf-web-methodology
description: "CTF Web 挑战的总体方法论。当面对 CTF 靶场、xbow benchmark、Web 安全挑战赛时使用。包含挑战类型快速识别、攻击策略选择决策树、常见出题模式、何时切换方向的判断标准。与 exploit/ 下的具体漏洞技能配合使用"
metadata:
  tags: "ctf,web,methodology,challenge,benchmark,靶场,比赛,策略,capture the flag"
  difficulty: "medium"
  icon: "🏆"
  category: "CTF"
---

# CTF Web 挑战方法论

CTF Web 挑战和真实渗透测试有本质区别：目标明确（拿 flag）、漏洞是故意设置的、通常只有一个入口点。本方法论帮助你快速识别挑战类型并选择最短路径。

## 核心思维模型

**CTF 的本质是解谜**。出题者故意留了一条攻击路径，你的任务是找到它。

关键原则：
1. **先广后深** — 花 2-3 轮快速侦察全貌，再深入具体漏洞
2. **线索驱动** — 每一步的结果告诉你下一步该做什么
3. **3 轮法则** — 一种方法尝试 3 轮无实质进展就切换方向
4. **不要硬猜** — 如果需要暴力破解，说明你可能走错了方向（CTF 通常有巧妙的解法）

## Phase 1: 快速侦察（1-3 轮）

按优先级执行（不是全部都做，有发现就停下来分析）：

1. **访问首页** — `http_request` GET 首页，观察：
   - 是什么应用？（登录页/博客/商城/API）
   - 有什么功能？（搜索/上传/注册/评论）
   - 页面底部/注释有没有提示？

2. **查看源码** — 检查 HTML 源码（不是渲染后的页面）：
   - HTML 注释 `<!-- hint: ... -->`
   - 隐藏表单字段 `<input type="hidden">`
   - JavaScript 中的 API 路径和变量
   - 引用的 JS/CSS 文件路径

3. **路径探测** — 检查常见路径：
   - `/robots.txt` — 经常藏着禁止访问的敏感路径
   - `/flag`, `/flag.txt`, `/flag.php`
   - `/.git/`, `/.svn/` — 源码泄露
   - `/backup.sql`, `/www.zip`, `/源码.tar.gz`
   - `/admin`, `/login`, `/api`

4. **指纹识别** — `smart_discover` 或 `scan_finger` 识别技术栈

## Phase 2: 挑战类型识别与策略选择

根据侦察结果，快速归类：

| 看到什么 | 可能是什么 | 下一步 |
|----------|------------|--------|
| 搜索框/查询参数 | SQL 注入 | 读 `sql-injection-methodology` |
| 登录页面 | 弱密码/SQL注入/JWT | 先试 `admin:admin`，再试 SQLi |
| 文件上传功能 | 文件上传漏洞 | 读 `file-upload-methodology` |
| 模板渲染/用户输入回显 | SSTI/XSS | 试 `{{7*7}}` 和 `${7*7}` |
| URL 中有文件路径参数 | LFI/目录穿越 | 试 `../../etc/passwd` |
| 反序列化数据（base64 cookie） | 反序列化 RCE | 读 `deserialization-methodology` |
| API 端点 + JSON | IDOR/权限绕过 | 读 `idor-methodology` |
| JWT token（eyJ...） | JWT 攻击 | 读 `jwt-attack-methodology` |
| 源码可见（.git 泄露等） | 源码审计 | 读 `ctf-source-audit` |
| ping/curl 功能 | 命令注入 | 读 `command-injection-methodology` |
| XML 输入/SOAP | XXE | 读 `ssrf-xxe-methodology` |

## Phase 3: 漏洞利用

利用过程中的 CTF 特有注意事项：

### 效率优先
- SQL 注入：**UNION SELECT 优先**（一次拿完整数据），EXTRACTVALUE 是备选
- 命令注入：**直接 cat /flag.txt**，别折腾反弹 shell
- LFI：**直接读 /flag.txt**，别先读 /etc/passwd

### 常见出题陷阱
- **假 flag** — `FLAG{this_is_a_fake_flag}` 或 `FLAG{test}` 不是真 flag
- **多层漏洞** — 有些挑战需要先拿到源码（通过 LFI），再从源码中发现另一个漏洞
- **WAF 绕过** — 过滤了 `select`？试 `SeLeCt` / `sElEcT` / `/*!select*/` / 双写 `selselectect`
- **编码** — 输入可能需要 URL 编码、双重编码、Unicode 编码

## Phase 4: 策略切换判断

**何时该换方向**：
- 同一种注入 payload 试了 5 种变体都没成功 → 可能不是这类漏洞
- 目录爆破没发现有价值的路径 → 回去看页面功能点
- SQL 注入确认但无法读文件 → flag 可能在数据库里，用 `--dump`
- 文件上传总是被拒绝 → 检查是否有其他攻击面
- 感觉「差一点就行了」但就是不行 → 最危险的信号，强制自己退后一步重新审视

**切换方向不是失败**，是排除法的正常部分。每次切换都缩小了搜索空间。
