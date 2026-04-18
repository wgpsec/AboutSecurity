---
name: ioc-analysis
description: "IOC（失陷指标）分析与对抗方法论。蓝队视角：如何收集、富化、关联 IOC 进行威胁猎杀。红队视角：如何避免自身基础设施和工具产生可识别的 IOC，以及如何使 IOC 快速失效。当红队需要评估自身暴露面或规划 C2 基础设施时使用"
metadata:
  tags: "ioc,indicator,threat-intel,c2-infrastructure,opsec,威胁情报,失陷指标,基础设施,归因"
  category: "threat-intel"
  mitre_attack: "T1583,T1584,T1588,T1608,T1071"
---

# IOC 分析与对抗

> **红队定位**：理解蓝队如何追踪你 → 设计短生命周期、不可关联的基础设施

## ⛔ 深入参考

- C2 基础设施 OPSEC 清单 → [references/c2-infra-opsec.md](references/c2-infra-opsec.md)
- IOC 类型与生命周期管理 → [references/ioc-lifecycle.md](references/ioc-lifecycle.md)

---

## IOC 金字塔（Pyramid of Pain）

```
难以更换                     防御者价值高
   ▲
   │  TTPs（战术/技术/过程）      ← 最难改变
   │  工具特征（Imphash/YARA）    ← 需重新编译
   │  网络/主机 Artifact          ← 需改行为模式
   │  域名                        ← 需新注册
   │  IP 地址                     ← 最容易换
   │  哈希值                      ← 改一字节即变
   ▼
容易更换                     防御者价值低
```

**红队策略：确保自己的 IOC 处于金字塔底部（容易更换），避免暴露顶部（TTP 不可变）**

## Part A: 蓝队视角 — IOC 收集与分析

### IOC 类型

| 类型 | 示例 | 采集来源 |
|------|------|---------|
| 文件哈希 | MD5/SHA256 | 终端/沙箱/VirusTotal |
| IP 地址 | C2 服务器 IP | 网络日志/PCAP |
| 域名 | C2/钓鱼域名 | DNS 日志/证书透明度 |
| URL/URI | C2 路径 | 代理日志/HTTP 日志 |
| Email | 发件人/附件名 | 邮件网关 |
| 注册表 | 持久化键值 | 终端检测 |
| 进程 | 进程名/命令行 | EDR/Sysmon |
| 文件路径 | 恶意文件位置 | 终端检测 |
| 证书 | SSL 证书哈希 | JA3/JARM |
| 网络签名 | JA3/JA3S/JARM | 流量分析 |

### IOC 富化流程

```
原始 IOC → 富化 → 关联
├─ 文件哈希 → VirusTotal/MalwareBazaar → 家族/来源/关联样本
├─ IP → Shodan/Censys/GreyNoise → 服务/端口/历史
├─ 域名 → PassiveDNS/Whois/CT Logs → 注册信息/关联域
├─ 证书 → crt.sh/Censys → 关联域名/IP
└─ JA3 → JA3er → 客户端指纹识别
```

---

## Part B: 红队视角 — IOC 对抗

### 策略 1: 基础设施分离与轮换

```
C2 基础设施设计原则：
├─ 分层架构:
│   攻击者 → Redirector(多个/轮换) → TeamServer(隐藏)
│   被发现的只是 Redirector → 换一个 IP 即可
│
├─ 域名策略:
│   ├─ 注册 30 天以上的域名（新域名有风险评分）
│   ├─ 使用合法分类的域名（非新注册/非恶意分类）
│   ├─ 域前置（Domain Fronting）→ CDN 背后真正的 C2
│   └─ 使用被接管的合法子域名（更可信）
│
├─ IP 策略:
│   ├─ 使用云服务商 IP（AWS/Azure/GCP）→ 难以封锁
│   ├─ 每次行动新建 VPS → 不复用 IP
│   └─ 使用 CDN/反代 → 隐藏真实 IP
│
└─ 证书策略:
    ├─ 使用 Let's Encrypt 证书（最常见，不突出）
    ├─ 或购买与目标同类的商业证书
    └─ ⛔ NEVER 使用自签名证书 → JA3S/JARM 特征明显
```

### 策略 2: 工具特征消除

```
文件级 IOC 对抗：
├─ 每次行动重新编译 → SHA256 变化
├─ 使用 Garble/Shikata 多态编码 → YARA 规则失效
├─ 修改 Rich Header / 编译时间 → Imphash 变化
├─ 资源签名替换 → 看起来像合法软件
└─ 代码混淆/虚拟化 → 静态分析失效

网络级 IOC 对抗：
├─ JA3 指纹 → 使用合法浏览器 TLS 库/配置
├─ User-Agent → 匹配目标环境真实浏览器
├─ URI 模式 → 模仿合法 SaaS API（/api/v1/events）
├─ 心跳间隔 → 加大 Jitter（30-50%），不要固定间隔
└─ 数据大小 → 添加 padding 避免固定包大小
```

### 策略 3: 归因对抗

```
防止被关联到同一组织/行动：
├─ 不同行动使用完全独立的基础设施
├─ 工具重新编译（不同编译器/选项/时间）
├─ 不复用 C2 Profile / Malleable 模板
├─ 注册信息使用一次性邮箱 + 不同注册商
├─ 支付使用加密货币 → Monero 优于 Bitcoin
└─ 时区/语言特征随机化
```

### 策略 4: IOC 生命周期缩短

```
让蓝队收集到的 IOC 快速过时：
├─ 短期 C2 域名 → 48h 后切换
├─ 一次性 Payload → 每个目标唯一编译
├─ 短期 VPS → 行动结束即销毁
├─ 快速阶段切换 → 初始访问 ≠ 驻留 ≠ 数据外传
└─ Payload 自毁 → 执行后删除自身
```

## 红队 C2 基础设施检查清单

```
部署前检查：
[ ] 域名注册 > 30 天 + 已分类
[ ] SSL 证书为 LE 或商业证书（非自签名）
[ ] Redirector 已配置（Apache/Nginx/Cloudflare）
[ ] TeamServer 无直接公网暴露
[ ] JA3 指纹匹配合法客户端
[ ] JARM 指纹不匹配已知 C2 框架
[ ] User-Agent 匹配目标环境
[ ] 域名 Whois 隐私保护已启用
[ ] IP 不在已知恶意 IP 列表中（VirusTotal/AbuseIPDB 检查）
[ ] DNS 记录无异常（无 TXT payload / 多 A 记录）

行动中检查：
[ ] 监控 C2 域名/IP 的 VT 检出率
[ ] Redirector 日志无异常扫描
[ ] 备用 C2 channel 已测试
[ ] 轮换计划已确认

行动后：
[ ] 销毁所有 VPS 实例
[ ] 销毁所有 Redirector
[ ] 确认无 DNS 残留指向已销毁 IP
```

## 关联技能

- **C2 免杀方法论** → `/skill:c2-evasion-methodology`
- **免杀研究** → `/skill:evasion-research`
- **社会工程** → `/skill:social-engineering`
- **红队评估** → `/skill:red-team-assessment`
