# PHP 前端交互类漏洞审计模式参考

5 类前端漏洞的危险代码 / 安全代码对比 + EVID_* 证据格式示例。

---

## 1. XSS (跨站脚本)

### 1.1 输出上下文与转义要求

| 输出上下文 | 转义需求 | PHP 实现 | 注入示例 |
|-----------|----------|----------|---------|
| HTML Body | HTML 实体编码 | `htmlspecialchars($s, ENT_QUOTES, 'UTF-8')` | `<script>alert(1)</script>` |
| HTML 属性 | 实体编码 + 引号包裹 | 同上，属性值必须用引号 | `" onfocus=alert(1) autofocus="` |
| JS 字符串 | JS 转义 | `json_encode($s, JSON_HEX_TAG\|JSON_HEX_APOS\|JSON_HEX_AMP\|JSON_HEX_QUOT)` | `';alert(1)//` |
| URL 参数 | URL 编码 | `urlencode($s)` | `javascript:alert(1)` |
| CSS 值 | CSS 转义 | 白名单或 `ctype_alnum` | `expression(alert(1))` |

### 1.2 htmlspecialchars 正确 vs 错误用法

```php
// 错误: 缺少 ENT_QUOTES → 单引号属性可逃逸
echo "<input value='" . htmlspecialchars($input) . "'>";
// 错误: 缺少编码参数 → PHP < 5.4 默认 ISO-8859-1，多字节可绕过
echo htmlspecialchars($input, ENT_QUOTES);

// 正确
echo htmlspecialchars($input, ENT_QUOTES, 'UTF-8');
```

### 1.3 框架自动转义与关闭方式

```php
// Blade: {{ }} 自动转义 | {!! !!} 跳过 → 搜索 {!! 出现
// Twig:  {{ }} 自动转义 | |raw 跳过 | {% autoescape false %} 区块关闭
// Smarty: 取决于 $smarty->escape_html(默认 false)，{$var|escape} 显式转义
```

### 1.4 存储型 vs 反射型 vs DOM XSS

```php
// 反射型: 同一请求 Source→Sink
echo "搜索: " . $_GET['keyword'];

// 存储型: 跨存储边界，关键看输出时是否转义
$db->insert('comments', ['body' => $_POST['comment']]);  // 写入
echo "<p>" . $row['body'] . "</p>";                       // 读取未转义 → XSS

// DOM XSS: PHP 输出数据，前端 JS 写入 DOM
echo '<script>var cfg=' . json_encode(['name'=>$input]) . ';</script>';
// 前端: document.getElementById('x').innerHTML = cfg.name; → 触发
echo '<div data-content="' . htmlspecialchars($input, ENT_QUOTES, 'UTF-8') . '">';
// 前端: elem.innerHTML = elem.dataset.content; → 实体解码后执行
```

### 1.5 XSS EVID 证据示例

```
[EVID_XSS_OUTPUT_POINT]       resources/views/search.blade.php:42 | {!! $keyword !!}
[EVID_XSS_OUTPUT_CONTEXT]     HTML Body，Blade 非转义输出
[EVID_XSS_USER_INPUT_TO_OUTPUT]
  Source: SearchController.php:18 — $keyword=$request->input('q') | 无过滤 → 反射型 XSS
```

---

## 2. CSRF (跨站请求伪造)

### 2.1 Token 实现审计

```php
// 正确: Session 绑定 + 随机生成 + hash_equals 验证
$_SESSION['csrf_token'] = bin2hex(random_bytes(32));
if (!hash_equals($_SESSION['csrf_token'], $_POST['token'])) { die('CSRF'); }

// 缺陷 1: 全局固定值 → 可预测
define('CSRF_TOKEN', md5('secret_key'));
// 缺陷 2: == 比较 → 时序攻击
if ($_SESSION['csrf_token'] == $_POST['token']) { ... }
// 缺陷 3: 未在验证后销毁 → Token 可复用
```

### 2.2 框架 CSRF 中间件配置

```php
// Laravel: 审计 $except 数组，被排除路由不受保护
class VerifyCsrfToken extends Middleware {
    protected $except = ['api/webhook/*', 'user/update-profile']; // 用户操作排除 → 高风险
}
// Symfony: 需手动添加 _token 字段
// ThinkPHP: config/app.php 的 token_on 或控制器 $this->request->checkToken()
```

Double Submit Cookie 模式的限制: 攻击者通过子域 XSS 或 CRLF 注入设置 Cookie 可同时控制两个值，弱于 Session-bound Token。

### 2.3 CSRF EVID 证据要点

```
[EVID_CSRF_STATE_CHANGE]      UserController.php:95 | updateProfile() 修改邮箱和密码
[EVID_CSRF_TOKEN_ABSENT]      POST /user/profile 未找到 Token 验证
[EVID_CSRF_MIDDLEWARE_BYPASS]  路由在 $except 数组中 → CSRF 可行
```

---

## 3. 开放重定向

### 3.1 可控模式

```php
header("Location: " . $_GET['url']);                            // 完全可控
header("Location: https://example.com/" . $_GET['path']);       // 路径拼接
return redirect($request->input('next'));                        // 框架 redirect
```

### 3.2 parse_url 绕过清单

| 绕过方式 | 输入 | parse_url host | 浏览器行为 |
|----------|------|---------------|-----------|
| 协议相对 | `//evil.com` | `evil.com` | 跳转 |
| 三斜线 | `///evil.com` | `null` | 部分浏览器跳转 |
| 反斜线 | `\evil.com` | `null` | IE/Edge 跳转 |
| 认证字段 | `https://legit.com@evil.com` | `evil.com` | 跳转 |
### 3.3 安全白名单实现

```php
// 错误: strpos 前缀检查 → https://example.com.evil.com 绕过
if (strpos($url, 'https://example.com') === 0) { ... }

// 正确: 解析 host 精确匹配 + scheme 限制
$parsed = parse_url($url);
$allowed = ['example.com', 'sub.example.com'];
if (!$parsed || !in_array($parsed['host'] ?? '', $allowed)
    || !in_array($parsed['scheme'] ?? '', ['http','https'])) {
    $url = '/';
}
```

---

## 4. CRLF 注入 (HTTP 响应拆分)

### 4.1 PHP 版本行为差异

```php
// PHP < 7.0: header() 不检测 \r\n → 可注入
header("X-User: " . $_GET['name']);  // name=%0d%0aSet-Cookie:%20admin=1

// PHP 7.0+: header() 检测 \r\n 并拒绝，但 7.0-7.3 允许单独 \r 或 \n
// setcookie() 到 PHP 8.0 才完善防护:
setcookie("lang", $_GET['lang']);    // PHP < 8.0 时 lang=%0d%0a → 可注入
```

### 4.2 响应头注入利用

```
// Session 固定: %0d%0aSet-Cookie:%20PHPSESSID=attacker_value
// XSS 变种:    %0d%0a%0d%0a<script>alert(document.cookie)</script>
// 改变解析:    %0d%0aContent-Type:%20text/html%0d%0a%0d%0a<script>...</script>
```

### 4.3 CRLF EVID 证据示例

```
[EVID_CRLF_HEADER_CALL]      ResponseHelper.php:23 | header("X-Redirect-By: " . $source)
[EVID_CRLF_USER_INPUT]       $source=$_GET['ref']，未过滤 \r\n
[EVID_CRLF_PHP_VERSION]      PHP 5.6.40 → header() 无内置防护 → 可利用
```

---

## 5. 会话与 Cookie 安全

### 5.1 session.* 安全配置审计清单

| 配置项 | 安全值 | 风险 |
|--------|--------|------|
| `session.cookie_httponly` | `1` | 关闭时 JS 可读 Session ID |
| `session.cookie_secure` | `1` | 关闭时 HTTP 明文传输 |
| `session.cookie_samesite` | `Lax`/`Strict` | `None` 允许跨站携带 |
| `session.use_strict_mode` | `1` | 关闭时接受未知 Session ID |
| `session.use_only_cookies` | `1` | 关闭时允许 URL 传递 Session ID |
| `session.use_trans_sid` | `0` | 开启时自动附加到 URL |

审计方式: 检查 `php.ini`、`.htaccess` 的 `php_value`、代码 `ini_set()`，以最终生效值为准。

### 5.2 session_regenerate_id 调用时机

```php
// 正确: 登录成功后 regenerate(true) — true 删除旧 Session 文件
if (verify_password($user, $password)) {
    session_regenerate_id(true);
    $_SESSION['user_id'] = $user->id;
}
// 缺陷 1: 未调用 → 攻击者预设的 Session ID 登录后仍有效
// 缺陷 2: 未传 true → 旧文件残留，竞争条件下可被利用
```

### 5.3 Cookie 属性审计

```php
// 审计 setcookie 四属性: secure / httponly / samesite / path+domain
setcookie('auth', $token, [
    'secure'=>true, 'httponly'=>true, 'samesite'=>'Lax', 'path'=>'/'
]);
// 旧式参数顺序容易遗漏:
setcookie('auth', $token, time()+3600, '/', '', false, false); // secure=false, httponly=false

// Laravel: config/session.php
'secure' => env('SESSION_SECURE_COOKIE', false), // 生产应为 true
```

### 5.4 自定义 Session Handler 安全性

```php
// 危险: DB 存储 Session 时 read() 拼接 SQL
// $id 在 use_strict_mode=0 时客户端可控
$this->db->query("SELECT data FROM sessions WHERE id = '$id'");
// 安全: 预编译
$stmt = $this->db->prepare("SELECT data FROM sessions WHERE id = ?");
$stmt->execute([$id]);
```

### 5.5 Session EVID 证据示例

```
[EVID_SESSION_CONFIG]         php.ini: cookie_httponly=0, cookie_secure=0
[EVID_SESSION_FIXATION]       LoginController.php:67 | 登录后未调用 session_regenerate_id
[EVID_COOKIE_ATTRIBUTES]      setcookie('remember_me',...,false,false) → secure/httponly 缺失
```
