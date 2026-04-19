---
name: php-auth-config-audit
description: |
  PHP 源码认证、配置与逻辑类漏洞审计。当在 PHP 白盒审计中需要检测认证绕过、
  权限控制、安全配置、密码学误用或业务逻辑漏洞时触发。
  覆盖 5 类风险: 认证绕过(硬编码凭据/弱比较/JWT 缺陷)、授权失控(IDOR/水平越权)、
  安全配置(CORS/错误暴露/调试模式)、密码学误用(弱哈希/ECB/硬编码密钥)、业务逻辑(竞争条件/支付篡改)。
metadata:
  tags: authentication, authorization, idor, config, cors, debug mode, cryptography, weak hash, business logic, 认证绕过, 授权, 越权, 配置审计, 密码学, 业务逻辑
  difficulty: medium
  category: code-audit
---

# PHP 认证配置与逻辑类漏洞源码审计

> **相关 skill**: 审计总流程 → `php-audit-pipeline` | 注入类 → `php-injection-audit` | 文件类 → `php-file-audit`

本 skill 聚焦源码层面的认证、授权、配置、密码学和业务逻辑缺陷。运行时利用（如 JWT 伪造、条件竞争脚本）属于对应黑盒 exploit skill 范畴。

## 深入参考

- 5 类风险的危险模式 / 安全模式代码对比 / 检测方法 → [references/auth-config-patterns.md](references/auth-config-patterns.md)

---

## 5 类风险速查表

| 类型 | 典型模式 | 危险信号 | 严重度 |
|------|----------|----------|--------|
| 认证绕过 | 硬编码凭据、`==` 弱比较、JWT algorithm none | 登录/令牌验证逻辑 | Critical-High |
| 授权失控 | IDOR 直接引用、缺少 ownership 检查、中间件跳过 | 资源访问无权限校验 | High-Critical |
| 安全配置 | `display_errors=On`、CORS `*`、调试模式残留 | 信息泄露/跨域滥用 | Medium-High |
| 密码学误用 | `md5($pass)`、ECB 模式、硬编码密钥 | 密码存储/加解密逻辑 | High-Critical |
| 业务逻辑 | 竞争条件、支付金额可控、状态机跳步 | 交易/库存/状态流转 | High-Critical |

## 认证审计要点

- **硬编码密码/API Key**: 搜索 `password`/`secret`/`api_key`/`token` 赋值为字面量字符串的位置
- **弱比较**: `==` 对比密码/token 导致类型混淆（`"0e123" == "0e456"` 为 true），必须使用 `===` 或 `hash_equals`
- **JWT 缺陷**: algorithm confusion（RS256→HS256）、签名未验证、`alg:none` 接受、密钥泄露、`kid` 参数注入
- **Remember Me**: token 是否可预测（`md5(username.time())`）、是否绑定用户/设备
- **密码重置**: token 可预测性、token 是否绑定目标用户、是否有过期机制

## 授权审计要点

- **IDOR**: `$_GET['id']` 直接查询无 `WHERE user_id=` 归属检查，对象引用可水平篡改
- **路由级 vs 函数级权限**: 中间件挂载范围是否完整覆盖、是否存在未保护的路由
- **中间件跳过**: 路由分组遗漏、`withoutMiddleware` 滥用、OPTIONS 预检绕过
- **水平越权 vs 垂直越权**: 水平 — 同角色访问他人资源；垂直 — 低权限访问高权限功能

## 配置审计要点

- **错误暴露**: `display_errors=On` + `error_reporting=E_ALL` 泄露路径/SQL/栈信息
- **CORS**: `Access-Control-Allow-Origin: *` 配合 `Allow-Credentials: true` 允许任意源携带凭据
- **调试模式**: Laravel `APP_DEBUG=true`、ThinkPHP `app_debug`、自定义 `DEBUG` 常量残留
- **安全头缺失**: `X-Frame-Options`、`Content-Security-Policy`、`X-Content-Type-Options` 未设置

## 密码学审计要点

- **弱哈希**: `md5($pass)` / `sha1($pass)` 用于密码存储，应使用 `password_hash(PASSWORD_BCRYPT)`
- **ECB 模式**: 确定性加密，相同明文产生相同密文，可分析推断内容
- **硬编码密钥**: `KEY`/`IV`/`SECRET` 写死在源码中，搜索 `openssl_encrypt`/`mcrypt_*` 调用的密钥来源
- **弱随机数**: `mt_rand`/`rand`/`uniqid` 用于生成安全令牌，应使用 `random_bytes`/`random_int`

## 逻辑审计要点

- **竞争条件**: 余额/库存先查后减无事务/无锁（SELECT→UPDATE 无 `FOR UPDATE`）
- **支付金额篡改**: 金额从客户端传入而非服务端计算、缺少签名验证
- **状态机跳步**: 订单状态从"待支付"直接跳到"已发货"，缺少状态转换合法性校验
- **批量操作无限制**: 无频率限制/无数量上限，可被滥用进行批量操作

## 检测清单

- [ ] 硬编码凭据搜索已完成（password/secret/key/token/api_key）
- [ ] 所有 `==` 比较密码/token 的位置已标记
- [ ] JWT 签名验证逻辑已审查（algorithm、密钥来源、kid）
- [ ] IDOR 风险点已检查 ownership 校验
- [ ] 路由权限覆盖完整性已验证
- [ ] php.ini / 框架配置安全基线已对照
- [ ] 密码存储方式已确认（password_hash vs md5/sha1）
- [ ] 加密密钥管理方式已审查（硬编码 vs 环境变量/密钥管理）
- [ ] 竞争条件敏感操作已检查事务/锁机制
- [ ] 支付/交易流程的金额来源和签名验证已确认
