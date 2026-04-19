# PHP 认证配置与逻辑类漏洞审计模式参考

5 类风险的危险代码 / 安全代码对比 + 检测方法。

---

## 1. 认证绕过

### 1.1 硬编码凭据检测

```bash
grep -rn "password\s*=\s*['\"]" --include="*.php"
grep -rn "secret\s*=\s*['\"]" --include="*.php"
grep -rn "api_key\s*=\s*['\"]" --include="*.php"
grep -rn "MYSQL_PASSWORD\|DB_PASS\|DB_PASSWORD" --include="*.php" --include="*.env"
```

```php
// 危险                                    // 安全
if ($password === 'admin@2024') {}         $api_secret = getenv('API_SECRET');
define('API_SECRET', 'hardcoded-key');     $db_pass = $_ENV['DB_PASSWORD'];
```

### 1.2 PHP 弱比较表

| 表达式 | 结果 | 原因 |
|--------|------|------|
| `"0e123" == "0e456"` | true | 科学计数法均为 0 |
| `"0e123" == 0` | true | 字符串转数字 |
| `"" == 0` | true | 空串转 0 |
| `"1abc" == 1` | true | 前缀数字 |
| `"php" == 0` | true (PHP<8) | 非数字串转 0 |

```php
// 危险: == 比较 token — 攻击者提交 0 或 "0e..." 可绕过
if ($_GET['token'] == $stored_token) { grant_access(); }
if (md5($input) == $hash) { authenticate(); }  // 0e 开头哈希碰撞

// 安全: hash_equals 防时序攻击 + 严格比较
if (hash_equals($stored_token, $_GET['token'])) { grant_access(); }
```

### 1.3 JWT 审计

**Algorithm Confusion**: 服务端 RS256，攻击者改 header 为 HS256，用公钥作 HMAC 密钥签名。

```php
// 危险: 从 token header 读取算法 / 接受 alg:none
$algo = $header->alg;  // 攻击者可控
// 安全: 服务端强制指定算法
$decoded = JWT::decode($jwt, new Key($secret, 'RS256'));
```

**kid 注入**: `file_get_contents('/keys/' . $header->kid)` 路径遍历；`WHERE id='{$header->kid}'` SQL 注入。

**密钥泄露**: 搜索 `.env`、`config/`、`storage/` 中 JWT 密钥，确认 `.gitignore` 排除。

### 1.4 密码重置漏洞

```php
// 危险模式
$token = md5($user->email . time());          // time() 可爆破
$token = substr(md5(rand()), 0, 16);          // rand() 种子可预测
$token = base64_encode($user->email);          // 无随机性
$user = User::where('reset_token', $token)->first(); // 未绑定用户
// 缺少过期: WHERE created_at > NOW() - INTERVAL 30 MINUTE

// 安全: 不可预测 + 绑定用户 + 过期
$token = bin2hex(random_bytes(32));
DB::insert('reset_tokens', ['user_id'=>$user->id, 'token'=>hash('sha256',$token),
    'expires_at'=>date('Y-m-d H:i:s', strtotime('+30 minutes'))]);
```

### 1.5 OAuth 缺陷

三个检查点: (1) `state` 参数未校验 → CSRF; (2) `redirect_uri` 未白名单限制; (3) 仅用 OAuth 返回 email 登录，未检查 `email_verified`。

---

## 2. 授权失控

### 2.1 IDOR 代码模式

```php
// 危险: 直接引用无归属检查
$order = Order::find($_GET['order_id']);
$invoice = file_get_contents("/invoices/" . $_GET['file_id'] . ".pdf");

// 安全: ownership 检查
$order = Order::where('id', $_GET['order_id'])->where('user_id', auth()->id())->firstOrFail();
```

搜索策略: `$_GET`/`$request->input` 直接进入 `find()`/`where('id',...)` 且缺少当前用户过滤。

### 2.2 中间件覆盖缺陷

```php
// 路由分组遗漏
Route::middleware(['auth','admin'])->group(function () {
    Route::get('/admin/dashboard', [AdminController::class, 'index']);
});
Route::get('/admin/export', [AdminController::class, 'export']); // 遗漏!

// withoutMiddleware 滥用
Route::get('/api/data', [DataController::class, 'index'])->withoutMiddleware('auth');
```

发现方法: `php artisan route:list` 导出，对比中间件列找漏洞。

### 2.3 水平越权 vs 垂直越权

**水平**: `Order::find($id)` 无 `user_id` 过滤，同角色跨用户访问。

**垂直**: 仅前端隐藏按钮，后端 `deleteUser($id)` 缺少 `role !== 'admin'` 检查。

---

## 3. 安全配置

### 3.1 php.ini 安全基线

| 配置项 | 安全值 | 风险 |
|--------|--------|------|
| `display_errors` | `Off` | 泄露路径/SQL/栈 |
| `log_errors` | `On` | 错误写日志不输出 |
| `expose_php` | `Off` | 隐藏 X-Powered-By |
| `allow_url_include` | `Off` | 阻止远程包含 |
| `allow_url_fopen` | `Off` | 减少 SSRF 面 |
| `open_basedir` | 项目目录 | 限制文件范围 |
| `disable_functions` | `exec,system,...` | 禁危险函数 |
| `session.cookie_httponly` | `1` | 阻止 JS 读 cookie |
| `session.cookie_secure` | `1` | 仅 HTTPS |
| `session.cookie_samesite` | `Strict`/`Lax` | 防 CSRF |
| `session.use_strict_mode` | `1` | 拒绝未初始化 SID |
| `session.sid_length` | `>=48` | 增加 SID 熵 |
| `upload_max_filesize` | 合理值 | 防资源耗尽 |
| `max_input_vars` | `1000` | 防 HashDoS |
| `memory_limit` | 合理值 | 防 OOM |

### 3.2 框架调试模式

```bash
grep -rn "APP_DEBUG\s*=\s*true" .env .env.production          # Laravel
grep -rn "app_debug\s*=>\s*true" config/                       # ThinkPHP
grep -rn "define.*DEBUG.*true" --include="*.php"                # 自定义
```

泄露内容: 栈跟踪、环境变量(数据库密码)、SQL 日志、已加载文件列表。

### 3.3 CORS 策略审计

```php
// 危险: 任意源 + 凭据 / 反射 Origin 无校验
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Origin: ' . $_SERVER['HTTP_ORIGIN']);

// 安全: 白名单
$allowed = ['https://app.example.com'];
if (in_array($_SERVER['HTTP_ORIGIN'], $allowed)) {
    header('Access-Control-Allow-Origin: ' . $_SERVER['HTTP_ORIGIN']);
}
```

### 3.4 安全 HTTP 头

必须设置: `X-Frame-Options: DENY`、`Content-Security-Policy: default-src 'self'`、`X-Content-Type-Options: nosniff`、`Strict-Transport-Security: max-age=31536000`、`Referrer-Policy: strict-origin-when-cross-origin`。搜索 `header(` 调用或中间件配置确认。

---

## 4. 密码学误用

### 4.1 密码哈希

```php
// 危险: 弱哈希
$hash = md5($password);                    // 彩虹表/GPU 秒破
$hash = md5($password . $salt);            // 自定义盐迭代不足

// 安全
$hash = password_hash($password, PASSWORD_BCRYPT, ['cost' => 12]);
if (password_verify($input, $stored_hash)) { /* ok */ }
```

审计: 搜索 `md5(`/`sha1(`，排除非密码用途，聚焦密码存储和认证比较。

### 4.2 对称加密

```php
// 危险: ECB 确定性加密 — 相同明文=相同密文
$cipher = openssl_encrypt($data, 'AES-128-ECB', $key);

// 安全: GCM 认证加密
$iv = random_bytes(16);
$cipher = openssl_encrypt($data, 'AES-256-GCM', $key, 0, $iv, $tag);
```

**CBC Padding Oracle**: 解密失败返回不同错误时可逐字节还原明文。检查错误处理是否统一。

**密钥管理**: 搜索 `openssl_encrypt`/`mcrypt_encrypt` 的 `$key`/`$iv` 来源，硬编码 `$key='MySecret'` 为 Critical。安全做法: `getenv('ENCRYPT_KEY')` 或密钥管理服务。

### 4.3 随机数

```php
// 危险: 可预测                             // 安全: 密码学安全
$token = md5(mt_rand());                    $token = bin2hex(random_bytes(32));
$code = rand(100000, 999999);               $code = random_int(100000, 999999);
$id = uniqid('', true);                     // uniqid 基于时间，不可用于安全场景
```

搜索 `mt_rand`/`rand(`/`uniqid(`/`srand(`，判断是否用于令牌、验证码、密钥生成。

---

## 5. 业务逻辑

### 5.1 竞争条件

```php
// 危险: 先查后减无锁 — 并发可双花
$balance = DB::table('wallets')->where('user_id', $uid)->value('balance');
if ($balance >= $amount) {
    DB::table('wallets')->where('user_id', $uid)->update(['balance' => $balance - $amount]);
}

// 安全 1: 悲观锁
DB::transaction(function () use ($uid, $amount) {
    $w = DB::table('wallets')->where('user_id', $uid)->lockForUpdate()->first();
    if ($w->balance >= $amount) {
        DB::table('wallets')->where('user_id', $uid)->update(['balance' => $w->balance - $amount]);
    }
});

// 安全 2: 原子 UPDATE
DB::table('wallets')->where('user_id', $uid)->where('balance', '>=', $amount)->decrement('balance', $amount);
```

搜索策略: SELECT + UPDATE 同表无事务，关注余额/库存/积分/优惠券。

### 5.2 支付流程审计

三检查点: (1) **金额来源** — `$_POST['amount']` 客户端可控为 Critical，必须服务端从订单计算; (2) **签名验证** — 支付回调需 `verifySignature` 防篡改; (3) **幂等性** — 回调重放防重复发货，需检查订单状态。

### 5.3 状态机跳步

```php
// 危险: 直接设置任意状态
Order::where('id', $id)->update(['status' => $request->status]);

// 安全: 合法转换矩阵
$transitions = ['pending'=>['paid','cancelled'], 'paid'=>['shipped','refunding']];
if (!in_array($next, $transitions[$current] ?? [])) { abort(422); }
```

### 5.4 批量操作频率限制

审计关注: 短信发送、优惠券发放、积分赠送、邀请注册等高价值操作。检查是否有单次数量上限 (`array_slice`) 和时间窗口频率限制 (`Cache`/`Redis` 计数器)。无限制的批量接口可被滥用造成资金损失。
