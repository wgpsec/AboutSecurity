---
name: ctf-web-recon
description: "CTF Web 挑战专用侦察方法。当面对 CTF 靶场目标需要快速发现攻击入口时使用。与真实渗透的 recon 不同——CTF 是单个应用、有意留线索、侦察应在 2-3 轮内完成。覆盖源码泄露、备份文件、隐藏路径、页面线索提取"
metadata:
  tags: "ctf,recon,侦察,源码泄露,备份文件,robots,git,信息收集,web"
  difficulty: "easy"
  icon: "🔦"
  category: "CTF"
---

# CTF Web 侦察方法论

CTF 侦察和真实渗透的侦察本质不同：
- 真实渗透：大量资产，需要枚举子域名、扫端口、做指纹
- CTF：**单个 Web 应用，出题者故意留了线索**，侦察的目标是找到这些线索

核心原则：**2-3 轮内完成侦察**，不要在侦察上花太多 rounds。

## Step 1: 首页分析

用 `http_request` GET 首页，仔细检查响应：

### HTTP 响应头
- `Server` — 服务器类型和版本（Apache/Nginx/Express）
- `X-Powered-By` — 后端语言（PHP/Express/ASP.NET）
- `Set-Cookie` — Cookie 格式（PHPSESSID=PHP, connect.sid=Node, JSESSIONID=Java）
- 非标准 Header — 出题者可能通过自定义 Header 给提示

### HTML 内容
- `<!-- 注释 -->` — CTF 出题者常在注释里留提示（密码、路径、漏洞类型）
- `<input type="hidden">` — 隐藏字段可能可以篡改
- `<form action="...">` — 表单提交地址暴露后端接口
- `<script src="...">` — JS 文件路径暴露项目结构
- 页面文字 — 有时提示就在页面内容里（"Try harder", "Look deeper"）

## Step 2: 关键路径检查

按优先级依次检查（有发现就分析，不要机械地全部检查）：

### 信息泄露路径
```
/robots.txt          — 最常见的提示位置，Disallow 的路径往往是关键
/.git/HEAD           — Git 源码泄露（存在则用 git-dumper 下载整个仓库）
/.svn/entries        — SVN 泄露
/.DS_Store           — macOS 目录文件泄露
/crossdomain.xml     — Flash 跨域策略（可能暴露内部域名）
/.env                — 环境变量文件（数据库密码、API 密钥）
/composer.json       — PHP 依赖（暴露框架版本）
/package.json        — Node.js 依赖
```

### 备份文件
```
/www.zip, /www.tar.gz, /backup.zip     — 整站打包
/index.php.bak, /index.php~, /index.php.swp  — 编辑器备份
/flag.txt, /flag, /flag.php             — 直接读 flag（有时就这么简单）
/.index.php.swp                         — Vim swap 文件
```

### 管理入口
```
/admin, /admin.php, /login, /login.php
/console, /dashboard, /phpmyadmin
/api, /api/v1, /graphql
```

## Step 3: JavaScript 分析

如果首页引用了 JS 文件，用 `http_request` 获取它们，搜索：

- API 端点路径（`/api/`, `fetch(`, `axios.`）
- 硬编码凭据（`password`, `token`, `secret`, `key`）
- 隐藏功能（`admin`, `debug`, `test`）
- 注释中的提示

**技巧**：压缩/混淆的 JS 不需要完全理解，搜索关键字符串即可。

## Step 4: 技术栈确认

通过前面的信息确认技术栈，这决定了后续的漏洞利用方向：

| 线索 | 技术栈 | 常见漏洞 |
|------|--------|----------|
| `.php` 后缀, PHPSESSID | PHP | LFI, 反序列化, 文件上传 |
| `express`, connect.sid | Node.js | 原型链污染, SSTI(EJS) |
| JSESSIONID, `.jsp` | Java | 反序列化, JNDI, SpEL |
| `_csrf_token`, `csrfmiddlewaretoken` | Python Django | SSTI(Jinja2) |
| `session=eyJ` | Python Flask | Flask session 伪造 |

## 不要做的事
- ❌ 不要对 CTF 目标做子域名枚举（只有一个应用）
- ❌ 不要做大规模端口扫描（通常只有一个端口）
- ❌ 不要花超过 3 轮在侦察上（线索不在侦察里就在功能点里）
