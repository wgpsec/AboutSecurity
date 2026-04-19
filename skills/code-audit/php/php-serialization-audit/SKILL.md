---
name: php-serialization-audit
description: |
  PHP 源码序列化与模板类漏洞审计。当在 PHP 白盒审计中需要检测反序列化、XML 解析或模板注入漏洞时触发。
  覆盖 3 类风险: PHP 反序列化(unserialize/phar 反序列化/POP 链构造)、
  XXE(XML 外部实体注入/libxml 配置)、SSTI(模板注入/Twig/Blade/Smarty 引擎)。
  需要 php-audit-pipeline 提供的数据流证据。
metadata:
  tags: deserialization, unserialize, phar, pop chain, xxe, xml, libxml, ssti, template injection, twig, smarty, blade, 反序列化, 模板注入, xml外部实体
  difficulty: hard
  category: code-audit
---

# PHP 序列化与模板类漏洞源码审计

> **相关 skill**: 审计总流程 → `php-audit-pipeline` | 反序列化黑盒利用 → `deserialization-methodology` | XXE 黑盒利用 → `xxe-injection-methodology`

本 skill 聚焦源码层面判断"反序列化/XXE/SSTI 是否成立"，核心是验证 Source→Sink 路径上的数据可控性和安全配置。构造 payload、链条利用等运行时技术属于对应黑盒 exploit skill 范畴。

## 深入参考

- 3 类漏洞的危险模式 / 安全模式代码对比 / EVID 证据示例 → [references/deser-patterns.md](references/deser-patterns.md)

---

## 3 类漏洞速查表

| 类型 | 典型 Sink | 利用条件 | 严重度 |
|------|-----------|----------|--------|
| 反序列化 | `unserialize`, `phar://` 触发函数 | 用户可控序列化数据 + 可用 Gadget 类 | Critical |
| XXE | `DOMDocument::loadXML`, `simplexml_load_string`, `XMLReader::xml` | 外部实体未禁用 + 用户可控 XML 输入 | High-Critical |
| SSTI | `Twig::render`, `Smarty::display`, `Blade {!! !!}`, `eval` | 用户输入直接进入模板渲染上下文 | Critical |

## 反序列化审计要点

- **unserialize() 入口**: 搜索所有 `unserialize` 调用，追踪参数来源（Cookie、Session、缓存、数据库、HTTP 请求体），判断用户是否可控
- **Phar 反序列化**: `file_exists`/`is_dir`/`fopen`/`filesize`/`copy` 等 40+ 文件系统函数在处理 `phar://` 协议时自动触发反序列化，检查路径参数是否用户可控
- **POP 链搜索**: 从 `__destruct`/`__wakeup`/`__toString` 入口出发，沿链式方法调用追踪到危险 Sink（文件写入/命令执行/SQL 操作）。重点关注 Composer 依赖中的 Gadget 类
- **allowed_classes 限制**: `unserialize($data, ['allowed_classes' => [...]])` 是否生效？空数组 `[]` 或 `false` 才完全安全，`true`（默认）不做任何限制

## XXE 审计要点

- **libxml_disable_entity_loader**: 在 PHP < 8.0 中需显式调用 `libxml_disable_entity_loader(true)` 禁用外部实体。PHP 8.0+ 该函数已废弃且默认禁用，但 `LIBXML_NOENT` 标志仍可重新启用
- **DOMDocument 风险**: `loadXML($input, LIBXML_NOENT)` 是最大风险点，该标志会展开外部实体。即使不传 `LIBXML_NOENT`，PHP < 8.0 默认仍可能加载实体
- **SimpleXML/XMLReader**: `simplexml_load_string` 默认安全（PHP 8.0+），但 `LIBXML_NOENT` 标志使其危险；`XMLReader::xml` 同理
- **盲 XXE vs 带外**: 解析结果是否回显到页面？无回显时检查是否可利用带外通道（HTTP/FTP/DNS）

## SSTI 审计要点

- **Twig**: `{{ user_input }}` 直接渲染用户输入时可注入。检查是否启用沙箱模式 `sandbox`，沙箱策略是否过于宽松（允许危险 filter/function）
- **Smarty**: `{php}` 标签（Smarty 3.1+ 已废弃但可能未禁用）、`{if}` 表达式中注入 PHP 函数调用（`{if system('id')}{/if}`）
- **Blade**: `{!! $var !!}` 输出未转义内容，若 `$var` 用户可控则存在 XSS 或更严重风险；`@php` 指令如果可注入则直接 RCE
- **自定义模板引擎**: 搜索 `eval`/`preg_replace(/e)` + 字符串替换模式，自研模板引擎常见的致命组合

## 检测清单

- [ ] 所有 `unserialize` 调用点已逐一审查参数来源
- [ ] Phar 协议触发函数的路径参数可控性已检查
- [ ] POP 链入口魔术方法已列举，链路可达性已追踪
- [ ] `allowed_classes` 配置已验证，默认值 `true` 已标记
- [ ] XML 解析器的 `LIBXML_NOENT` 标志使用情况已确认
- [ ] `libxml_disable_entity_loader` 调用状态已检查（PHP < 8.0）
- [ ] Twig/Smarty/Blade 模板中用户输入的渲染方式已审查
- [ ] 自定义模板引擎的 eval 调用已排查
- [ ] 严重度评分使用了统一公式，与 pipeline 一致
