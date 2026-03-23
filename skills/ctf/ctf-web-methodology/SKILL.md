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

## 深入参考（来自 ctf-skills 技术库）

- 服务端注入（SQLi/SSTI/LFI/XXE/SSRF） → 读 [references/server-side.md](references/server-side.md)
- 服务端执行（命令注入/RCE/文件上传/CRLF） → 读 [references/server-side-exec.md](references/server-side-exec.md)
- 服务端高级（Race Condition/HTTP走私/缓存投毒） → 读 [references/server-side-advanced.md](references/server-side-advanced.md)
- 反序列化（PHP/Java/Python/Node/.NET） → 读 [references/server-side-deser.md](references/server-side-deser.md)
- 认证与访问（密码/MFA/OAuth/IDOR/逻辑漏洞） → 读 [references/auth-and-access.md](references/auth-and-access.md)
- JWT 攻击（none/弱密钥/JWK注入/算法混淆） → 读 [references/auth-jwt.md](references/auth-jwt.md)
- 认证基础设施（LDAP/Kerberos/SAML/证书） → 读 [references/auth-infra.md](references/auth-infra.md)
- 客户端（XSS/CSP绕过/DOM/CSS注入） → 读 [references/client-side.md](references/client-side.md)
- Node.js 与原型链污染 → 读 [references/node-and-prototype.md](references/node-and-prototype.md)
- CVE 利用集（Log4Shell/Gitea/Grafana等） → 读 [references/cves.md](references/cves.md)
- Web3/区块链（Solidity/重入/闪电贷） → 读 [references/web3.md](references/web3.md)

---

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

- SQL 注入：**UNION SELECT 优先**，EXTRACTVALUE 备选
- 命令注入：**直接 cat /flag.txt**，别折腾反弹 shell
- LFI：**直接读 /flag.txt**，别先读 /etc/passwd
- **假 flag** — `FLAG{test}` 不是真 flag；**多层漏洞** — LFI 拿源码再挖第二个洞
- **WAF 绕过** — 大小写/双写/注释 `/*!select*/`；**编码** — URL/双重/Unicode

## Phase 4: 策略切换

- 同一 payload 试 5 种变体没成功 → 换方向
- SQL 注入确认但无法读文件 → flag 在数据库里
- 感觉「差一点」但不行 → 最危险信号，退后重新审视
