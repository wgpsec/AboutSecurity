---
name: supply-chain-audit
description: "供应链安全审计。当需要检查目标使用的第三方组件、JS 库、CDN 资源、SaaS 服务的安全风险时使用。覆盖组件版本发现、CVE 关联、子域名接管、JS 库投毒检测、CDN 安全配置评估"
metadata:
  tags: "supply-chain,component,cdn,third-party,js,npm,subdomain-takeover,供应链,组件安全"
  difficulty: "medium"
  icon: "🔗"
  category: "综合"
---

# 供应链安全审计方法论

供应链攻击不需要突破目标的代码——只需要目标依赖的某个组件有漏洞或被投毒。

## Phase 1: 组件发现

### 1.1 前端 JS 库识别
```bash
# 爬取页面获取所有 JS 引用
scan_crawl target="http://target"
# 或直接 HTTP 请求分析页面
http_request url="http://target" method="GET"
```

从 HTML/JS 中提取：
- `<script src="https://cdn.xxx.com/jquery-3.6.0.min.js">` → jQuery 3.6.0
- `<script src="/static/js/vendor.chunk.js">` → 内部打包，需分析内容
- `/__webpack_manifest__`, `/static/js/main.*.js` → Webpack 构建

### 1.2 后端技术栈
```bash
scan_finger target="http://target"
```
从响应头识别：
- `X-Powered-By: Express` → Node.js
- `Server: Apache/2.4.41` → Apache（CVE-rich）
- `X-AspNet-Version` → .NET 版本

### 1.3 子域名 → 第三方服务映射
```bash
scan_dns target="target.com"
```
检查 CNAME 指向的第三方服务：
- `status.target.com → statuspage.io` — 状态页托管
- `docs.target.com → gitbook.io` — 文档托管
- `mail.target.com → mailgun.org` — 邮件服务
- `cdn.target.com → cloudfront.net` — CDN 服务

## Phase 2: 已知漏洞关联

### 2.1 组件版本 → CVE 匹配
对发现的每个组件+版本，检查已知漏洞：
- jQuery < 3.5.0 → CVE-2020-11022/11023（XSS）
- lodash < 4.17.21 → CVE-2021-23337（命令注入）
- log4j 2.0-2.14.1 → CVE-2021-44228（RCE，Log4Shell）
- Apache 2.4.49-2.4.50 → CVE-2021-41773（路径穿越 RCE）
- Spring Framework < 5.3.18 → CVE-2022-22965（Spring4Shell）

```bash
poc_web target="http://target"
```

### 2.2 退役/停止维护的组件
比有 CVE 更危险的是完全停止维护的组件：
- AngularJS 1.x（2021年末停止支持）
- Python 2.x
- jQuery UI（安全更新很少）
- Moment.js（已停止开发）

## Phase 3: 子域名接管

子域名接管（Subdomain Takeover）是供应链审计的高价值发现：

### 3.1 原理
```
blog.target.com  CNAME → target.ghost.io
如果 target.ghost.io 已被注销 → 攻击者可注册该 Ghost 账号 → 控制 blog.target.com 的内容
```

### 3.2 检测
对每个子域名的 CNAME 记录，检查第三方服务是否仍然绑定：
- DNS 解析返回 `NXDOMAIN` 但 CNAME 仍存在
- 访问返回 "There isn't a GitHub Pages site here"、"No such app"、"Domain not configured"
- 常见可接管服务：GitHub Pages、Heroku、AWS S3、Shopify、Tumblr、Fastly

## Phase 4: CDN 和外部资源安全

### 4.1 CDN 配置
- 是否使用了 SRI（Subresource Integrity）？
  `<script src="https://cdn.example.com/lib.js" integrity="sha384-...">` — 有 SRI 则安全
  `<script src="https://cdn.example.com/lib.js">` — 无 SRI，CDN 被入侵即中招
- CDN 域名是否专属？公共 CDN（cdnjs, jsdelivr）被投毒影响所有用户

### 4.2 第三方脚本风险
嵌入的第三方 JS 脚本（分析/广告/聊天）拥有和自有脚本相同的权限：
- Google Analytics / Tag Manager
- 在线客服（Intercom, Zendesk）
- A/B 测试脚本
- 支付 SDK

任何一个被入侵都等于目标被入侵（Magecart 类攻击）。

## Phase 5: 风险评估

| 风险等级 | 发现 |
|----------|------|
| 严重 | 已知 RCE CVE 的组件版本（Log4Shell, Spring4Shell） |
| 高危 | 可接管的子域名、无 SRI 的 CDN 引用 |
| 中危 | 已知 XSS/信息泄露 CVE 的组件 |
| 低危 | 退役组件、过时版本但无已知 CVE |
| 信息 | 第三方脚本清单、技术栈概览 |

## 注意事项
- 供应链审计的核心是**完整性**——漏掉一个组件就可能漏掉关键风险
- 前端组件版本通常在 JS 文件注释或变量中能找到
- 子域名接管是供应链审计中最容易出成果的方向
