---
name: passive-recon
description: "纯被动 OSINT 情报收集，不触碰目标。当需要在不被目标察觉的情况下收集资产情报、在正式渗透前做预研、或通过 FOFA/Quake/Hunter 等搜索引擎发现暴露资产时使用。同时适用于需要从多引擎交叉比对获取完整资产视图的场景"
metadata:
  tags: "osint,passive,fofa,quake,hunter,被动侦察,情报收集,资产发现,搜索引擎,whois,dns"
  difficulty: "easy"
  icon: "🕵️"
  category: "侦察"
---

# 被动 OSINT 情报收集方法论

被动侦察的核心优势是**零接触**——不会在目标日志中留下痕迹。适合渗透前期预研、红队侦察、或在授权范围外只能做被动收集的场景。

## Phase 1: 多引擎资产搜索

### FOFA
`osint_fofa` — 国内最大的网络空间测绘引擎，适合发现国内资产。

常用查询模式：
- 域名资产：`domain="example.com"`
- IP 段：`ip="192.168.1.0/24"`
- 特定服务：`domain="example.com" && port="8080"`
- 特定组件：`domain="example.com" && app="WordPress"`

### Quake
`osint_quake` — 360 网络空间测绘，擅长深度指纹识别。

常用查询模式：
- 域名：`domain:"example.com"`
- 服务：`domain:"example.com" AND port:8443`
- 组件：`domain:"example.com" AND app:"Apache Tomcat"`

### Hunter
`osint_hunter` — 鹰图平台，擅长 IP 关联分析和资产聚合。

## Phase 2: 结果交叉比对

三个引擎各有侧重，交叉比对才能获取完整视图：

| 维度 | 分析方法 |
|------|----------|
| IP/域名清单 | 三引擎去重合并，标注仅单一引擎发现的（可能是新上线/已下线） |
| 端口分布 | 统计高危端口（22/3306/6379/9200），标注非标准端口 |
| 技术栈 | 汇总 Web 框架、中间件、CMS 版本 |
| 管理后台 | 搜索 title 含 "login"/"admin"/"dashboard" 的资产 |
| 证书信息 | SSL 证书中的 CN/SAN 可能泄露内部域名 |
| 历史数据 | 对比不同时间点数据，发现新增/下线资产 |

## Phase 3: 高价值目标识别

从被动收集结果中优先标注：
1. **暴露的管理后台** — 通常是最短攻击路径
2. **过期/未维护的服务** — 旧版本组件更可能有已知漏洞
3. **内部系统误暴露** — OA/VPN/GitLab/Jenkins 等不应公网可达的服务
4. **数据库端口暴露** — Redis/MongoDB/Elasticsearch 无认证是常见问题
5. **开发/测试环境** — dev/test/staging 子域通常安全措施较弱

## 注意事项
- 纯被动收集，**不要**直接访问或扫描目标
- 搜索引擎数据有时效性，最新资产可能未收录
- 不同引擎查询语法不同，注意区分

## 多引擎交叉验证
- 单引擎独有的结果可能新上线或已下线
- 数据时效性：各引擎收录时间不同、更新频率不同
- 标注来源：标记仅单一引擎发现的资产，需进一步验证
- 注意：不能扫描、不能直接访问目标、不能端口扫描

## 其他被动信息源
- WHOIS 查询域名注册信息
- DNS 历史记录
- GitHub 搜索泄露代码/凭据
- 其他公开来源（社交媒体、论坛等）
