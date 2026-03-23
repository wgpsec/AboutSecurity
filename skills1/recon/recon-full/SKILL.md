---
name: recon-full
description: "主动式全流程资产侦察。当需要对目标进行从零到漏洞发现的完整侦察、渗透测试的第一阶段、或需要全面了解目标攻击面时使用。覆盖子域名枚举→端口扫描→存活检测→指纹识别→POC 扫描的完整链条"
metadata:
  tags: "recon,subdomain,port,fingerprint,poc,扫描,侦察,资产发现,攻击面,渗透测试"
  difficulty: "medium"
  icon: "🔍"
  category: "侦察"
---

# 主动式全流程侦察方法论

本技能是渗透测试的标准第一步，目标是从域名/IP 出发，尽可能多地发现资产和漏洞。

## Phase 1: 子域名枚举
用 `scan_dns` 枚举子域名。这步很关键——子域名往往是被遗忘的攻击面（测试环境、旧版本、内部系统）。

**分析要点**：
- 子域名命名模式：`dev.`, `test.`, `staging.`, `api.`, `admin.` 通常是高价值目标
- CDN 分布：被 CDN 保护的域名可能需要找源站 IP
- 通配符记录：`*.example.com` 存在时，需要用字典枚举而非纯 DNS 解析

## Phase 2: 端口扫描
对发现的 IP/域名用 `scan_port` 扫描端口。

**高价值端口**：
- Web：80, 443, 8080, 8443, 8888
- 数据库：3306(MySQL), 5432(PostgreSQL), 6379(Redis), 27017(MongoDB)
- 远程管理：22(SSH), 3389(RDP), 5900(VNC)
- 中间件：8009(AJP/Tomcat), 9200(Elasticsearch), 2375(Docker API)

非标准端口（30000+）值得特别关注——常用于隐藏管理服务。

## Phase 3: 存活检测
用 `scan_urlive` 检测 HTTP/HTTPS 服务存活状态。

**分析要点**：
- HTTP 到 HTTPS 的重定向链
- 不同端口返回不同应用（同 IP 多站点）
- 状态码 403/401 的端点 → 可能是需要认证的管理后台
- 302 跳转到登录页 → 说明有受保护的内容

## Phase 4: 指纹识别
用 `scan_finger` 识别技术栈，这直接决定后续的漏洞利用方向。

**技术栈 → 攻击策略映射**：
| 技术栈 | 优先检查 |
|--------|----------|
| PHP | LFI/文件上传/反序列化 |
| Java/Spring | 反序列化/JNDI/Actuator |
| Python/Django/Flask | SSTI/Pickle |
| Node.js/Express | 原型链污染/SSRF |
| WordPress/Joomla | CMS 专用 POC |
| Nginx/Apache | 解析漏洞/配置错误 |

## Phase 5: POC 扫描
用 `poc_web` 进行已知漏洞扫描。根据指纹结果关注特定类别：
- 框架漏洞（Spring4Shell, Struts2, Log4j）
- CMS 漏洞（WordPress plugin, Joomla, Drupal）
- 中间件漏洞（Tomcat Manager, WebLogic, JBoss）

## 输出要求
每个阶段结束后简要总结发现，最终按攻击优先级排序：
1. 可直接利用的高危漏洞
2. 暴露的管理后台和敏感接口
3. 可进一步探测的攻击面
