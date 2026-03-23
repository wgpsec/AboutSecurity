---
name: ctf-osint
description: "CTF 开源情报(OSINT)技术。用于社交媒体调查、地理定位、DNS侦察、Google Dorking、反向图片搜索、用户名枚举、Wayback Machine、Tor中继查询等 CTF OSINT 类挑战"
metadata:
  tags: "ctf,osint,开源情报,geolocation,社交媒体,dns,dorking,图片搜索"
  difficulty: "medium"
  icon: "🌐"
  category: "CTF"
---

# CTF 开源情报 (OSINT)

## 深入参考

- 社交媒体调查（Twitter/Tumblr/BlueSky/Discord/用户名枚举） → 读 [references/social-media.md](references/social-media.md)
- 地理定位与媒体分析（反向图搜/街景匹配/MGRS/EXIF） → 读 [references/geolocation-and-media.md](references/geolocation-and-media.md)
- Web 与 DNS 侦察（Dorking/Wayback/Zone Transfer/WHOIS） → 读 [references/web-and-dns.md](references/web-and-dns.md)

---

## 分类决策树

```
OSINT 题目？
├─ 找人/找账号
│  ├─ 用户名 → whatsmyname.app / namechk.com (741+ 站点)
│  ├─ Twitter/X → 数字 User ID 持久追踪 / Snowflake 时间戳
│  ├─ Tumblr → curl -sI 检查 x-tumblr-user / avatar/512
│  └─ BlueSky → public.api.bsky.app (无需认证)
├─ 找位置（地理定位）
│  ├─ 图片 → Google Lens 裁剪搜索 / Yandex(人脸) / TinEye
│  ├─ 路标/铁路 → OpenRailwayMap / OpenInfraMap
│  ├─ MGRS 坐标 → 在线转换器 → Google Maps
│  ├─ Plus Codes → `XXXX+XXX` 格式 → Google Maps
│  └─ 街景匹配 → 特征提取 + 多指标相似度排序
├─ 找信息
│  ├─ DNS → dig TXT/CNAME/MX / zone transfer
│  ├─ Google Dorking → site: filetype: intitle:
│  ├─ Wayback Machine → 历史快照
│  ├─ WHOIS → 反向WHOIS / 历史WHOIS / IP/ASN
│  └─ GitHub → issue/PR/commit/wiki 分析
└─ 特殊场景
   ├─ Tor 中继 → metrics.torproject.org 指纹查询
   ├─ FEC 政治捐款 → FEC.gov
   └─ Unicode 同形字隐写 → ASCII=0, 同形字=1
```

## 快速命令

```bash
# 元数据提取
exiftool image.jpg
pdfinfo document.pdf

# DNS 侦察
dig -t txt domain.com
dig axfr @ns.domain.com domain.com

# IP 地理定位
curl "http://ip-api.com/json/IP_ADDR"

# Google Dorking
# site:example.com filetype:pdf
# intitle:"index of" password

# Flag 搜索
grep -rniE '(flag|ctf)\{' .
```

## 字符串识别

| 格式 | 类型 |
|------|------|
| 40 hex chars | SHA-1（Tor 指纹） |
| 64 hex chars | SHA-256 |
| 32 hex chars | MD5 |

## 常用工具

| 工具 | 用途 |
|------|------|
| Shodan | 联网设备搜索 |
| Censys | 证书和主机搜索 |
| VirusTotal | 文件/URL 信誉 |
| Wayback Machine | 历史网页快照 |
| whatsmyname.app | 用户名跨平台枚举 |
| Google Lens | 裁剪区域反向图搜 |
