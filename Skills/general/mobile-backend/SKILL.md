---
name: mobile-backend
description: "移动 App 后端 API 安全测试。当目标是移动应用的后端接口、发现 /api/v1/ 等移动端 API 路径、或需要测试 App 与服务器之间的通信安全时使用。覆盖 API 端点发现、认证机制测试、业务逻辑漏洞、移动端特有的安全问题"
metadata:
  tags: "mobile,api,backend,auth,app,ios,android,移动安全,业务逻辑,支付"
  difficulty: "medium"
  icon: "📱"
  category: "综合"
---

# 移动 App 后端 API 安全测试方法论

移动后端 API 和传统 Web 的区别：移动端通常直接调用 REST API（不经过浏览器），认证机制、参数格式、业务逻辑都有移动端特色。

## Phase 1: API 端点发现

### 1.1 路径发现
```bash
# 常见移动 API 路径
brute_dir target="http://target" wordlist="api_paths"
# 重点检查：
# /api/v1/, /api/v2/, /api/v3/
# /mobile/api/, /app/api/
# /graphql, /gateway/
```

### 1.2 文档搜索
检查是否暴露了 API 文档：
- `/docs`, `/swagger`, `/swagger-ui`, `/api-docs`
- `/openapi.json`, `/openapi.yaml`
- `/redoc`

Swagger/OpenAPI 文档暴露所有接口和参数——是最大的信息泄露。

### 1.3 App 逆向获取 API
如果无法通过 Web 发现 API（需要 App 才能访问）：
- 抓包：用代理拦截 App 流量（Burp/Charles/mitmproxy）
- APK 反编译：搜索 URL 字符串
- 搜索 `api.target.com`, `https://`, `endpoint` 等关键字

## Phase 2: 认证机制测试

### 2.1 认证类型识别
| 认证方式 | 特征 | 攻击方向 |
|----------|------|----------|
| JWT Token | `Authorization: Bearer eyJ...` | 参考 `jwt-attack-methodology` |
| API Key | `X-API-Key: xxx` 或 URL 参数 | 泄露检测、权限测试 |
| OAuth 2.0 | 有 `/oauth/token` 端点 | 参考 `oauth-sso-attack` |
| Session Cookie | `Set-Cookie: session=xxx` | Session 固定/劫持 |
| 自定义签名 | `sign=md5(...)`, `timestamp=...` | 签名算法逆向 |

### 2.2 认证绕过测试
- 不带 Token 直接访问 API（某些端点可能忘记加认证）
- 过期 Token 是否仍有效
- 修改 Token 中的 user_id/role
- 用低权限 Token 访问高权限 API

## Phase 3: 业务逻辑漏洞

移动端最常见的漏洞不是技术漏洞，而是**业务逻辑漏洞**：

### 3.1 越权访问（IDOR）
```
GET /api/v1/users/1001/profile    → 200（自己的数据）
GET /api/v1/users/1002/profile    → 200？（别人的数据！）
GET /api/v1/users/1/profile       → 200？（管理员的数据！）
```
参考 `idor-methodology` 技能。

### 3.2 支付/金额篡改
```json
// 原始请求
{"product_id": 1, "quantity": 1, "price": 99.00}
// 篡改
{"product_id": 1, "quantity": 1, "price": 0.01}
{"product_id": 1, "quantity": -1, "price": 99.00}
```
检查：价格是否由前端传入、数量能否为负数、优惠券能否叠加使用。

### 3.3 验证码绕过
- 短信验证码：暴力枚举 4-6 位数字（有无限速？）
- 图形验证码：是否每次请求都刷新、是否可以复用
- 验证码绕过：删除验证码参数、置空、固定值

### 3.4 条件竞争
移动端常见场景：
- 优惠券/红包同时使用（参考 `race-condition-methodology`）
- 积分兑换重复提交
- 限购商品超额下单

## Phase 4: 数据安全

### 4.1 敏感数据泄露
- API 响应中是否包含不必要的字段（密码哈希、内部 ID、手机号完整显示）
- 错误信息是否泄露内部实现（堆栈信息、SQL 语句、文件路径）
- 调试端点是否暴露（`/debug`, `/actuator`, `/metrics`）

### 4.2 接口限速
- 登录接口：无限速 → 暴力破解
- 短信发送：无限速 → 短信轰炸
- 数据查询：无限速 → 数据爬取

### 4.3 传输安全
- 是否使用 HTTPS（某些内部 API 可能用 HTTP）
- 证书校验是否可绕过（App 端 SSL Pinning 是否有效）

## Phase 5: 移动端特有问题

- **设备绑定绕过**：修改 `Device-ID` / `IMEI` Header
- **版本降级**：旧版 API（v1）可能有已修复但未下线的漏洞
- **推送通知泄露**：推送内容是否含敏感信息
- **深度链接劫持**：自定义 URL Scheme 可能被恶意 App 拦截

## 注意事项
- 移动 API 通常比 Web 更信任客户端——前端校验更多、后端校验更少
- 注意 API 版本差异（v1 可能有漏洞，v2 修复了，但 v1 未下线）
- 业务逻辑漏洞比技术漏洞更常见，需要理解业务流程
