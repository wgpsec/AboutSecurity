# 供应链深度审计技术

## 子域名接管（Subdomain Takeover）

### 原理
```
blog.target.com  CNAME → target.ghost.io
如果 target.ghost.io 已被注销 → 攻击者可注册该 Ghost 账号 → 控制 blog.target.com
```

### 检测
对每个子域名的 CNAME 记录检查：
- DNS 解析返回 `NXDOMAIN` 但 CNAME 仍存在
- 访问返回 "There isn't a GitHub Pages site here"、"No such app"、"Domain not configured"
- 常见可接管服务：GitHub Pages、Heroku、AWS S3、Shopify、Tumblr、Fastly

## CDN 和外部资源安全

### CDN 配置
- 有 SRI 则安全：`<script src="..." integrity="sha384-...">`
- 无 SRI，CDN 被入侵即中招：`<script src="...">`
- 公共 CDN（cdnjs, jsdelivr）被投毒影响所有用户

### 第三方脚本风险
嵌入的第三方 JS 拥有和自有脚本相同的权限：
- Google Analytics / Tag Manager
- 在线客服（Intercom, Zendesk）
- A/B 测试脚本、支付 SDK

任何一个被入侵都等于目标被入侵（Magecart 类攻击）。

## 退役/停止维护的组件
比有 CVE 更危险的是完全停止维护的组件：
- AngularJS 1.x（2021年末停止支持）
- Python 2.x
- jQuery UI（安全更新很少）
- Moment.js（已停止开发）

## 风险评估矩阵

| 风险等级 | 发现 |
|----------|------|
| 严重 | 已知 RCE CVE 的组件版本（Log4Shell, Spring4Shell） |
| 高危 | 可接管的子域名、无 SRI 的 CDN 引用 |
| 中危 | 已知 XSS/信息泄露 CVE 的组件 |
| 低危 | 退役组件、过时版本但无已知 CVE |
| 信息 | 第三方脚本清单、技术栈概览 |
