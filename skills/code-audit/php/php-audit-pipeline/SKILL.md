---
name: php-audit-pipeline
description: |
  PHP 白盒源码安全审计总方法论。当需要对 PHP 项目进行完整的源码安全审计、
  或需要系统化的白盒漏洞挖掘流程时触发。
  覆盖 5 阶段审计流水线: 路由映射→权限建模→数据流追踪→分类漏洞审计→利用链组装。
  核心机制: 证据合约系统(EVID_*)防止 AI 幻觉误报，所有漏洞结论必须有数据流证据支撑。
metadata:
  tags: php audit, code audit, 代码审计, white box, 白盒, source code, 源码审计, pipeline, evidence contract, 证据合约, route mapping, data flow, sink, source, php security
  difficulty: hard
  category: code-audit
---

# PHP 白盒审计总方法论

> **相关 skill**: 注入类 → `php-injection-audit` | 文件类 → `php-file-audit` | 前端类 → `php-frontend-audit` | 序列化类 → `php-serialization-audit` | 认证配置 → `php-auth-config-audit` | 框架特定 → `php-framework-audit` | 利用链 → `php-exploit-chain`

白盒审计在源码层面发现漏洞，关注"代码为什么不安全"。发现漏洞后的实际利用技术（构造 payload、绕过 WAF）属于黑盒 exploit skill 范畴。

## 深入参考

- 证据合约系统与评分公式 → [references/evidence-contract.md](references/evidence-contract.md)
- PHP 危险函数分类速查 → [references/sink-reference.md](references/sink-reference.md)

---

## 审计 5 阶段概览

| 阶段 | 名称 | 核心任务 | 产出物 |
|------|------|----------|--------|
| P1 | 路由映射 | 解析所有入口点及其参数 | 路由清单 |
| P2 | 权限建模 | 分析认证/授权，标记裸露路由 | 权限矩阵 |
| P3 | 数据流追踪 | Source→Sink 完整路径追踪 | EVID_* 证据集 |
| P4 | 分类审计 | 按 Sink 类型深入检查 | 漏洞清单 |
| P5 | 报告组装 | 评分 + 利用链编排 | 审计报告 |

## Phase 1: 路由映射与入口点识别

解析框架路由配置，建立完整的攻击面清单:
- **Laravel**: `routes/web.php` + `routes/api.php`，关注 `Route::any` 和资源路由
- **ThinkPHP**: `config/route.php` + 控制器自动路由（注意版本差异，TP5 默认开启自动路由）
- **原生 PHP**: 扫描所有可直接访问的 `.php` 文件，识别 `$_GET/$_POST/$_REQUEST` 入口

产出: 路由清单，每条记录包含路径、Handler 方法、接受参数、是否需认证。

## Phase 2: 权限建模与认证审查

分析中间件/拦截器的挂载范围，找出哪些路由缺少认证保护:
- 未认证即可访问的路由标记为高优先级审计目标
- 审查全局过滤器（如 `addslashes`、自定义 WAF 类）的实际覆盖范围和绕过可能
- 检查 Session 配置、CSRF token 机制、密码存储方式

## Phase 3: 数据流追踪（Source → Sink）

这是白盒审计的核心阶段。每条潜在漏洞路径都要产出 EVID_* 证据点（详见 evidence-contract.md）。

**三层分析法**:
1. **面** — 全局关键字扫描: 搜索 Sink 函数（参考 sink-reference.md），快速定位危险代码区域
2. **线** — 逐行追踪变量流: 从 Sink 反向追溯到 Source，记录每一步的变量传递和过滤操作
3. **点** — 验证利用条件: 确认过滤是否可绕过、参数是否可控、执行路径是否可达

当无法追踪到完整的 Source→Sink 路径时，只能标注为"待验证"。缺少任何一个环节的证据都不能标"已确认"。

## Phase 4: 分类漏洞审计

按 Sink 类型分派到对应子 skill 进行深入审计:
- 注入类（SQL/CMD/LDAP/表达式）→ `php-injection-audit`
- 文件类（读取/包含/上传/写入/归档）→ `php-file-audit`
- 前端类（XSS/CSRF/重定向/CRLF）→ `php-frontend-audit`
- 序列化类（反序列化/XXE）→ `php-serialization-audit`
- 认证配置类（越权/弱加密/信息泄露）→ `php-auth-config-audit`
- 框架特定漏洞（已知 CVE、框架配置缺陷）→ `php-framework-audit`

## Phase 5: 报告与利用链组装

**严重度评分**: `Score = R * 0.40 + I * 0.35 + C * 0.25`（R=可达性, I=影响范围, C=利用复杂度，各 0-3 分）

将同一目标上的多个漏洞组合为利用链（如: 信息泄露→认证绕过→文件写入→RCE），详见 `php-exploit-chain`。

## 审计质量检查清单

- [ ] 所有公开路由均已纳入路由清单
- [ ] 未认证路由已全部标记并优先审计
- [ ] 每个"已确认"漏洞都有完整的 EVID_* 证据链
- [ ] 全局过滤器的绕过可能性已评估
- [ ] 框架版本已确认，已知 CVE 已交叉比对
- [ ] 漏洞评分使用了统一公式，等级划分一致
- [ ] 利用链可行性已在源码层面验证
