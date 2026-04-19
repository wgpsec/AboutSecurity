---
name: php-frontend-audit
description: |
  PHP 源码前端交互类漏洞审计。当在 PHP 白盒审计中需要检测前端安全相关漏洞时触发。
  覆盖 5 类前端风险: XSS(反射/存储/DOM)、CSRF(Token 验证缺失)、
  开放重定向(header Location 可控)、CRLF 注入(HTTP 响应拆分)、会话与 Cookie 安全(固定/劫持/属性)。
  需要 php-audit-pipeline 提供的数据流证据。
metadata:
  tags: xss, csrf, open redirect, crlf injection, session, cookie, 跨站脚本, 跨站请求伪造, 会话安全, http response splitting, 前端安全审计
  difficulty: medium
  category: code-audit
---

# PHP 前端交互类漏洞源码审计

> **相关 skill**: 审计总流程 → `php-audit-pipeline` | XSS 黑盒利用 → `xss-methodology` | CSRF 黑盒利用 → `csrf-methodology`

本 skill 聚焦源码层面判断"前端安全漏洞是否成立"，核心是验证用户可控数据在 HTTP 响应中的输出是否安全。构造 payload、绕 WAF 等运行时利用技术属于对应黑盒 exploit skill 范畴。

## 深入参考

- 5 类前端漏洞的危险模式 / 安全模式代码对比 / EVID 证据示例 → [references/frontend-patterns.md](references/frontend-patterns.md)

---

## 5 类前端漏洞速查表

| 类型 | 典型 Sink | 触发条件 | 严重度 |
|------|-----------|----------|--------|
| XSS (反射/存储/DOM) | `echo`, `print`, 模板输出 `{!! !!}` | 用户输入未转义输出到 HTML 上下文 | High-Critical |
| CSRF | 状态变更表单/API | 缺少 Token 校验且无 SameSite 保护 | Medium-High |
| 开放重定向 | `header("Location:")`, 框架 `redirect()` | 重定向目标 URL 用户完全可控 | Medium |
| CRLF 注入 | `header()`, `setcookie()` | 用户输入含 `\r\n` 进入 HTTP 响应头 | Medium-High |
| 会话安全 | `session_start()`, `setcookie()` | session 固定/Cookie 属性缺失 | Medium-High |

## XSS 审计要点

- **输出上下文决定转义需求**: HTML body、属性、JavaScript 字符串、URL 各需要不同的转义策略，单一 `htmlspecialchars` 不能覆盖所有场景
- **htmlspecialchars 检查**: 确认使用了 `ENT_QUOTES` flag（默认 `ENT_COMPAT` 不转义单引号）和正确的编码参数（`'UTF-8'`）
- **模板引擎自动转义**: Blade `{{ }}` 自动转义但 `{!! !!}` 不转义；Twig `{{ }}` 自动转义但 `|raw` 过滤器跳过；Smarty 取决于 `$escape_html` 配置
- **存储型 vs 反射型**: 存储型需跨越存储边界追踪——数据入库时是否过滤不重要，关键看输出时是否转义
- **DOM XSS**: PHP 后端输出 JSON 到 `<script>` 标签或 HTML data 属性，前端 JS 取出后写入 DOM（`innerHTML`/`document.write`）

## CSRF 审计要点

- **状态变更操作识别**: 所有 POST/PUT/DELETE 请求中修改数据的操作都应有 Token 验证
- **框架中间件例外**: Laravel `VerifyCsrfToken` 的 `$except` 数组、ThinkPHP 的 `token_on` 配置——被排除的路由是高风险目标
- **SameSite 属性**: `SameSite=Lax` 可防御大多数 CSRF（但不防 GET 型），`None` 无保护，缺省值因浏览器而异
- **自定义 Token 实现**: 检查 Token 是否绑定 Session、是否一次性消费、是否有时效限制

## 开放重定向审计要点

- **header Location 可控**: `header("Location: " . $_GET['url'])` 是经典模式，也包括框架的 `redirect($url)`
- **parse_url 绕过**: `//evil.com`（协议相对 URL）、`///evil.com`、`\evil.com`（IE 兼容）、`javascript:` 伪协议都能绕过简单校验
- **安全白名单**: 正确实现是解析 host 后对比允许域名列表，而非正则匹配或前缀检查（`example.com.evil.com` 绕过前缀）

## CRLF 审计要点

- **header() + 用户输入**: `header("X-Custom: " . $input)` 中 `$input` 含 `\r\n` 可注入额外响应头
- **PHP 版本差异**: PHP 7.0+ 的 `header()` 已检测 `\r\n` 并抛 warning（但 `setcookie()` 到 PHP 8.x 才完善防护）
- **利用方式**: 注入 `Set-Cookie` 头实现 Session 固定、注入空行后写 Body 实现 XSS

## 会话安全审计要点

- **session_regenerate_id 时机**: 登录成功后应调用此函数防止会话固定。参数 `true` 删除旧 Session 文件
- **Cookie 属性**: `session.cookie_httponly=1`（防 JS 读取）、`session.cookie_secure=1`（仅 HTTPS）、`session.cookie_samesite=Lax`
- **自定义 Session Handler**: 实现 `SessionHandlerInterface` 时，`read()`/`write()` 是否有注入风险（如存储在 DB 时的 SQL 拼接）

## 检测清单

- [ ] 所有前端类 EVID_* 证据点已逐一审查
- [ ] echo/print 输出点的上下文类型已标注，转义方式与上下文匹配
- [ ] 模板引擎的自动转义是否被关闭已检查
- [ ] 状态变更路由的 CSRF Token 验证已确认，例外路由已标记
- [ ] header() 和 redirect() 的目标参数来源已追踪
- [ ] CRLF 注入对 PHP 版本与受影响函数已交叉确认
- [ ] Session 配置（php.ini / 代码 ini_set）已审计
- [ ] Cookie 四属性（httponly/secure/samesite/path）已逐项检查
- [ ] 严重度评分使用了统一公式，与 pipeline 一致
