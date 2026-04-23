---
name: waf-bypass-methodology
description: "WAF 绕过统一方法论。当漏洞利用 payload 被 WAF 拦截返回 403/406 时使用。覆盖编码绕过、分块传输、HTTP 方法切换、参数污染、Payload 变形等通用绕过技术"
metadata:
  tags: "waf,bypass,绕过,firewall,cloudflare,modsecurity,安全狗,宝塔,WAF绕过,编码,分块传输,参数污染,403,forbidden,blocked,rejected,406,拦截,intercepted,请求被拒绝,payload被拦截"
  category: "exploit"
---

# WAF 绕过统一方法论

WAF 绕过的核心原则：WAF 和后端应用对同一 HTTP 请求的解析存在差异，利用这个差异让 WAF "看到"合法请求而后端"看到"恶意 payload。

## 深入参考

- 编码绕过 Payload（双重 URL/Unicode/HTML/混合编码） → [references/encoding-bypass-payloads.md](references/encoding-bypass-payloads.md)
- HTTP 协议层绕过（分块传输/Content-Type/方法切换/HTTP2/走私） → [references/http-protocol-bypass.md](references/http-protocol-bypass.md)
- 参数层绕过（HPP/数组语法/Multipart） → [references/parameter-bypass.md](references/parameter-bypass.md)
- Payload 变形（通用编码/拆分/格式切换） → [references/payload-mutation.md](references/payload-mutation.md)

---

## Phase 0: WAF 识别

### 0.1 检测是否有 WAF

```bash
# 发送明显恶意请求，观察响应
curl -s "http://TARGET/?id=1' OR '1'='1" -D-
curl -s "http://TARGET/?id=<script>alert(1)</script>" -D-
curl -s "http://TARGET/?cmd=;id" -D-

# 对比正常请求和恶意请求的响应差异
# WAF 拦截特征：403/406 状态码、特定拦截页面、不同的 Server 头
```

### 0.2 WAF 指纹识别

| 特征 | WAF 产品 |
|------|----------|
| `Server: cloudflare` / `cf-ray` 头 | Cloudflare |
| `X-Sucuri-ID` 头 | Sucuri |
| 响应含 `ModSecurity` | ModSecurity |
| 响应含 `安全狗` / `safedog` | 安全狗 |
| 响应含 `宝塔` / `bt.cn` | 宝塔 WAF |
| `X-Powered-By-Anquanbao` | 安百 WAF |
| 响应含 `yunsuo` | 云锁 |
| 阿里云 403 页面 | 阿里云盾 |
| 腾讯云特定 403 | 腾讯云 WAF |

---

## 通用绕过检查流程

```
Payload 被拦截 → 403/拦截页
├── 1. 编码绕过
│   ├── 双重 URL 编码
│   ├── Unicode 编码
│   └── 混合大小写 + NULL 字节
├── 2. HTTP 层
│   ├── 分块传输
│   ├── Content-Type 切换
│   ├── HTTP 方法切换
│   └── HTTP/2
├── 3. 参数层
│   ├── 参数污染 (HPP)
│   ├── 数组/JSON 嵌套
│   └── Multipart 包裹
├── 4. Payload 变形
│   ├── 空格替代（注释/Tab/换行）
│   ├── 函数名替代
│   ├── 拼接/编码函数
│   └── 通配符/变量
└── 5. 逻辑层
    ├── 分多次请求发送（先探测再利用）
    └── 利用白名单路径（/api/health + 路径穿越）
```

> 每个分支的详细 payload 见对应 references 文件
