---
name: subdomain-deep
description: "深度子域名挖掘，多源联合枚举。当需要最大化子域名发现覆盖率、常规 DNS 枚举结果不足、或目标使用了 CDN/通配符 DNS 时使用。联合 DNS 爆破、OSINT 引擎、爬虫三种方式交叉发现"
metadata:
  tags: "recon,subdomain,dns,osint,crawl,子域名,枚举,爆破,DNS,资产发现"
  difficulty: "medium"
  icon: "🔎"
  category: "侦察"
---

# 深度子域名挖掘方法论

单一来源的子域名枚举通常只能覆盖 30-50% 的实际资产。本方法论联合三种独立来源交叉验证，最大化覆盖率。

## Phase 1: DNS 枚举
用 `scan_dns` 进行 DNS 子域名枚举（字典爆破 + 递归发现）。

**结果分析**：
- 统计解析到不同 IP 段的子域（识别多机房/多云部署）
- 识别 CNAME 记录 → CDN/云服务（CloudFront, Cloudflare, Fastly）
- 识别通配符：如果 `random12345.example.com` 也解析，说明有通配符记录
  - 通配符存在时，需要过滤掉通配符 IP 对应的结果

## Phase 2: OSINT 引擎搜索
用 `osint_fofa` 查询域名关联资产。OSINT 引擎能发现 DNS 枚举遗漏的资产（因为它基于实际网络扫描数据，而非 DNS 记录）。

**OSINT 能补充的发现**：
- 使用非标准端口的 Web 服务（如 `dev.example.com:8443`）
- DNS 记录已删除但服务仍在线的"幽灵"子域
- IP 反查发现的同一服务器上的其他域名

## Phase 3: 爬虫发现
用 `scan_crawl` 爬取主站和已知子域，从页面内容中提取更多子域引用。

**爬虫能发现的来源**：
- HTML 中的链接（href/src/action）
- JavaScript 中硬编码的 API 地址
- CSS 中引用的资源域名
- 跨域请求头（CORS: Access-Control-Allow-Origin）

## Phase 4: 结果合并与分类

将三个来源的子域名去重合并后，按用途分类：

| 类型 | 特征 | 攻击价值 |
|------|------|----------|
| Web 应用 | 80/443, HTTP 响应 | 高 — 主要攻击面 |
| API 服务 | api.*/gateway.* | 高 — 常有认证缺陷 |
| 管理后台 | admin.*/manage.*/cms.* | 极高 — 直接管理权限 |
| 邮件系统 | mail.*/smtp.*/mx.* | 中 — 钓鱼和信息收集 |
| 开发/测试 | dev.*/test.*/staging.* | 极高 — 安全措施最弱 |
| 内部系统 | vpn.*/oa.*/git.*/jenkins.* | 极高 — 不应公网可达 |
| CDN/静态 | cdn.*/static.*/img.* | 低 — 通常无动态内容 |

**优先深入探测**：管理后台 > 开发测试 > 内部系统 > API > Web 应用
