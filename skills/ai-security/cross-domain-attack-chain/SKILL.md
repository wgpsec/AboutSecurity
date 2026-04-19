---
name: cross-domain-attack-chain
description: |
  Web 与 AI 跨域攻击链方法论。当目标系统同时包含传统 Web 应用和 AI/LLM 组件、
  需要评估 Web 漏洞对 AI 系统的影响或 AI 漏洞对 Web 系统的影响时触发。
  覆盖双向攻击链: Web→AI(XSS 窃取对话/SSRF 调用模型 API/SQLi 污染 RAG/文件上传 RAG 投毒)
  和 AI→Web(注入生成存储型 XSS/Agent 执行 SQL 命令/工具读取敏感文件/沙箱逃逸 RCE)。
metadata:
  tags: cross domain, web to ai, ai to web, 跨域攻击, attack chain, rag poisoning, xss ai, ssrf model api, agent sql injection, sandbox escape, 攻击链
  difficulty: hard
  category: ai-security
---

# Web/AI 跨域攻击链方法论

> **相关 skill**：间接注入 → `prompt-injection`；Agent 工具链 → `agent-security`；MCP 协议 → `mcp-security`

## 概述

现代系统中 Web 服务与 AI/LLM 组件共享数据管道和基础设施。Web 层的低危漏洞（如受限 SSRF）接触到内部模型 API 时可升级为 Prompt 注入；反过来，Prompt 注入通过 Agent 工具链回写数据库可产生存储型 XSS。跨域攻击链的价值在于将两个领域的"中低危"串联为"高危/严重"。

## 跨域攻击路径总览

| 方向 | 编号 | 入口漏洞 | 跨域跳板 | 最终影响 |
|------|------|----------|----------|----------|
| Web→AI | W2A-1 | XSS | 劫持 AI 对话接口 | 窃取对话内容/注入恶意上下文 |
| Web→AI | W2A-2 | SSRF | 访问内部模型 API | 获取 embedding/直接执行 prompt |
| Web→AI | W2A-3 | SQLi | 修改向量库记录 | 污染 RAG 检索结果 |
| Web→AI | W2A-4 | 文件上传 | 上传含隐藏指令文档 | RAG 投毒/间接注入 |
| Web→AI | W2A-5 | API 越权 | 管理接口未鉴权 | 篡改 System Prompt/模型配置 |
| AI→Web | A2W-1 | Prompt 注入 | 模型输出未转义 | 生成存储型 XSS payload |
| AI→Web | A2W-2 | Agent 劫持 | SQL/命令工具 | 执行任意 SQL 查询或系统命令 |
| AI→Web | A2W-3 | 工具滥用 | 文件读取工具 | 读取服务器敏感文件 |
| AI→Web | A2W-4 | 代码执行 | 沙箱逃逸 | 反弹 shell/RCE |
| AI→Web | A2W-5 | MCP 投毒 | 外部回调工具 | 数据外泄到攻击者服务器 |

## Phase 0: 攻击面映射

- 识别系统中 Web 与 AI 组件的所有交互点：RAG 数据源（数据库、文件存储、CMS）、模型 API 端点、共享缓存/队列
- 绘制数据流图，标注哪些 Web 用户输入最终会进入 LLM 上下文（直接或经 RAG 检索）
- 确认 AI 输出回写到 Web 层的路径：是否直接渲染到页面、存入数据库、或触发后端操作

## Phase 1: Web→AI 攻击路径

**1.1 XSS → 窃取 AI 对话/注入上下文**
利用 XSS 劫持用户与 AI 的 WebSocket 或 API 会话，窃取对话历史或注入恶意上下文（GAARM.0040.001）。关键在于 AI 聊天界面是否将 Markdown/HTML img 标签渲染为实际请求，从而通过 `img src` 外泄会话内容。

**1.2 SSRF → 调用内部模型 API**
Web 层 SSRF 若能触达内网模型端点，可直接发送 prompt 请求、获取 embedding 或修改参数。Agent 自身的网络访问能力也可能成为 SSRF 跳板（GAARM.0041.001）。

**1.3 SQLi → 污染 RAG 向量库**
当 RAG 系统使用关系型数据库存储文档 chunk 或元数据时，SQL 注入可修改检索内容，间接将恶意指令注入 LLM 上下文，实现持久化的间接 Prompt 注入。

**1.4 文件上传 → RAG 投毒**
上传含隐藏指令的文档（PDF 中的白色文字、DOCX 中的隐藏段落、图片 EXIF 中的文本），文档被 RAG 管道索引后，隐藏指令在检索阶段被注入到模型上下文中。

**1.5 API 越权 → 修改 System Prompt/模型配置**
管理接口若缺乏鉴权或存在 IDOR，攻击者可直接修改 System Prompt、调整模型温度参数、切换底层模型版本，从根本上改变 AI 的行为边界。

## Phase 2: AI→Web 攻击路径

**2.1 Prompt 注入 → 生成存储型 XSS**
诱导模型生成包含 `<script>` 或事件处理器的 HTML 片段，若 Web 层对 AI 输出未做输出编码，payload 被存储并在其他用户浏览时执行。

**2.2 Agent 劫持 → 执行 SQL/系统命令**
通过间接注入劫持 Agent 目标，使其调用数据库查询工具执行 `DROP TABLE` 或调用 shell 工具执行系统命令（GAARM.0041.002），影响直接作用于 Web 后端基础设施。

**2.3 工具滥用 → 读取敏感文件**
劫持 Agent 的文件系统工具读取 `.env`、数据库凭据、TLS 私钥等服务器敏感文件，并通过对话输出或回调机制将内容传递给攻击者。

**2.4 沙箱逃逸 → 反弹 shell**
代码执行型 Agent 若沙箱隔离不足，Prompt 注入可诱导生成并执行逃逸 payload，获取宿主机 shell 权限，完成从 AI 层到基础设施层的穿透。

**2.5 MCP 投毒 → 数据外泄**
通过恶意 MCP Server 的工具描述投毒，劫持 Agent 在调用合法工具时附带数据外泄动作，将用户对话或内部数据通过 HTTP 回调发送到攻击者服务器。

## 攻击链组合决策

| 可用入口 | 推荐组合路径 | 预期严重度 |
|----------|-------------|-----------|
| XSS + AI 聊天界面 | W2A-1 → 窃取对话 → 提取内部信息 | High |
| SSRF + 内网模型端点 | W2A-2 → 直接 prompt → 信息泄露/后续注入 | Critical |
| 文件上传 + RAG 管道 | W2A-4 → RAG 投毒 → A2W-1 存储型 XSS | Critical |
| SQLi + 向量库 | W2A-3 → 持久化注入 → A2W-2 Agent 执行命令 | Critical |
| Prompt 注入 + Agent 工具 | A2W-2/A2W-3 → 读取凭据 → 横向移动 | Critical |
| MCP 第三方 Server | A2W-5 → 数据外泄 + A2W-2 命令执行 | High |

## 检测清单

```
1. [ ] Web 与 AI 组件的交互点已完整映射？数据流方向已标注？
2. [ ] Web 用户输入到 LLM 上下文的路径是否存在注入点？
3. [ ] AI 输出回写到 Web 层时是否做了输出编码和消毒？
4. [ ] RAG 数据源（数据库/文件存储）是否对写入做了权限控制？
5. [ ] 内部模型 API 是否限制了网络访问来源？
6. [ ] Agent 工具调用是否有参数校验和权限隔离？
7. [ ] 文件上传到 RAG 索引的管道是否检测隐藏指令？
8. [ ] 跨域攻击链的组合路径是否纳入威胁建模？
```
