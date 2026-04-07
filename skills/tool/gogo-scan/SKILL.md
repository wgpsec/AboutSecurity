---
name: gogo-scan
description: "使用 gogo 进行端口扫描和指纹识别。gogo 是 chainreactors 出品的高速端口扫描器，支持主动/被动指纹识别、智能分组输出、自动 TLS 握手提取证书信息。和 fscan 的区别：gogo 专注于扫描精度和指纹覆盖（2000+ 指纹规则），而 fscan 兼顾弱口令和 POC。当需要精确识别目标服务和中间件版本（而不只是端口开放）时优先使用 gogo。涉及端口扫描、服务识别、指纹识别、资产发现的场景都应考虑此技能"
metadata:
  tags: "gogo,port,scan,fingerprint,指纹,端口,扫描,资产发现,chainreactors"
  category: "tool"
---

# gogo 高速端口扫描与指纹识别

gogo 的核心优势是**指纹精度**——内置 2000+ 指纹规则，能精确识别 Web 框架、中间件版本、CMS 类型，输出结构化 JSON 便于后续处理。

项目地址：https://github.com/chainreactors/gogo

## 基本用法

```bash
# 扫描单个目标
gogo -i 10.0.0.1

# 扫描网段
gogo -i 10.0.0.0/24

# 扫描指定端口
gogo -i 10.0.0.0/24 -p 80,443,8080,8443

# 扫描 Top1000 端口
gogo -i 10.0.0.0/24 -p top1000

# 从文件读取目标
gogo -l targets.txt
```

## 输出控制

```bash
# JSON 输出（便于后续处理）
gogo -i 10.0.0.0/24 -o result.json -f json

# 只输出存活 + 有指纹的
gogo -i 10.0.0.0/24 --filter

# CSV 输出
gogo -i 10.0.0.0/24 -o result.csv -f csv
```

## 高级扫描

```bash
# 调整并发（默认 500，内网可加大）
gogo -i 10.0.0.0/16 -t 2000

# 启用版本探测（更精确但更慢）
gogo -i 10.0.0.1 -p top1000 -v

# 指定超时（毫秒）
gogo -i 10.0.0.0/24 --timeout 3000

# 排除端口
gogo -i 10.0.0.0/24 --exclude-port 22,80
```

## 与其他工具联动

```bash
# gogo 发现服务 → nuclei 扫描漏洞
gogo -i 10.0.0.0/24 -p top1000 -o result.json -f json
cat result.json | jq -r '.[] | select(.port==80 or .port==443 or .port==8080) | .uri' | nuclei -t ~/nuclei-templates/

# gogo 发现服务 → httpx 探测
gogo -i 10.0.0.0/24 -o result.json -f json
cat result.json | jq -r '.uri' | httpx -silent
```

## 决策树

```
需要扫描什么？
├─ 快速看网段存活 + 弱口令 + POC → fscan
├─ 精确指纹识别（Web 框架/CMS/中间件版本）→ gogo
├─ 大规模端口扫描（SYN/全端口）→ naabu 或 nmap
└─ 子域名资产 → subfinder + httpx
```
