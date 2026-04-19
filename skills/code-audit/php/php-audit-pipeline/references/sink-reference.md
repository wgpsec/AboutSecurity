# PHP 危险函数分类速查表

按漏洞类型分类，列出 PHP 中常见的 Sink 函数及其审计要点。审计时以此表为索引进行全局关键字扫描，快速定位潜在漏洞代码区域。

---

## SQL 注入（SQL）

**Sink 函数**: `mysqli_query`, `mysqli_multi_query`, `PDO::query`, `PDO::exec`, `pg_query`, `pg_query_params`（参数位拼接时）, `sqlite_query`, `$wpdb->query`, `$wpdb->prepare`（格式化拼接时）, ORM 原生方法: `DB::raw`, `whereRaw`, `orderByRaw`, `selectRaw`, `havingRaw`, `groupByRaw`

**危险模式**: 用户输入通过字符串拼接进入 SQL 语句。特别注意 ORM 的 Raw 方法——开发者容易误以为 ORM 天然安全而在 Raw 方法中直接拼接变量。

**安全验证**: 是否使用参数化查询/预编译语句; `intval()`/`(int)` 类型强转; `addslashes()` 在 GBK 编码下可被宽字节绕过，不算安全过滤。

**对应审计 skill**: `php-injection-audit`

---

## 命令注入（CMD）

**Sink 函数**: `exec`, `system`, `shell_exec`, `passthru`, `proc_open`, `popen`, `pcntl_exec`, 反引号运算符 `` ` ``

**危险模式**: 用户输入拼入命令字符串。即使使用了 `escapeshellarg()`，在某些上下文（如命令参数注入 `--option=value`）中仍可能存在风险。

**安全验证**: `escapeshellarg()` + `escapeshellcmd()` 是否同时使用（单独使用可能不够）; 白名单验证; 参数是否在引号内; 是否存在管道符/分号等元字符注入可能。

**对应审计 skill**: `php-injection-audit`

---

## SSRF

**Sink 函数**: `curl_exec`, `curl_multi_exec`, `file_get_contents`, `fopen`（远程 URL）, `fsockopen`, `pfsockopen`, `SoapClient`, `get_headers`, `copy`（远程 URL）

**危险模式**: 用户可控的 URL 被用于服务端发起请求。注意 `file_get_contents` 同时是文件读取和 SSRF 的 Sink。

**安全验证**: URL 白名单/黑名单验证; DNS Rebinding 防护; 协议限制（是否允许 `gopher://`、`dict://`、`file://`）; 是否禁用了 302 跟随。

**对应审计 skill**: `php-injection-audit`

---

## XSS

**Sink 函数**: `echo`, `print`, `printf`, `sprintf`（输出到 HTML 时）, 模板引擎 raw 输出: Blade `{!! !!}`, Twig `{{ var|raw }}` / `{% autoescape false %}`, Smarty `{$var nofilter}`

**危险模式**: 用户输入未经 HTML 编码直接输出到页面。注意区分输出上下文: HTML 正文、HTML 属性、JavaScript 块、URL 中需要不同的编码方式。

**安全验证**: `htmlspecialchars()` 是否带 `ENT_QUOTES` 和正确编码参数; 模板引擎是否默认开启自动转义; JavaScript 上下文中 `htmlspecialchars()` 不够——需要 JSON 编码或 JS 特定转义。

**对应审计 skill**: `php-frontend-audit`

---

## 文件读取/包含（FILE）

**Sink 函数**: `include`, `include_once`, `require`, `require_once`, `file_get_contents`, `readfile`, `file`, `fopen`, `fread`, `highlight_file`, `show_source`, `parse_ini_file`

**危险模式**: 用户输入影响文件路径。文件包含漏洞（LFI/RFI）比单纯的文件读取危害更大，因为包含的文件会被当作 PHP 执行。注意 `php://filter` 和 `php://input` 等伪协议的利用。

**安全验证**: 路径是否经过 `basename()` 处理; 是否存在目录穿越（`../`）过滤及其绕过可能; `open_basedir` 配置; `allow_url_include` 是否开启; 是否使用了白名单限制可包含的文件。

**对应审计 skill**: `php-file-audit`

---

## 文件上传（UPLOAD）

**Sink 函数**: `move_uploaded_file`, `rename`（配合 `$_FILES`）, `copy`（配合 `$_FILES`）

**危险模式**: 用户上传的文件被存储到 Web 可访问目录且保留了可执行扩展名。重点关注扩展名检测逻辑——黑名单容易遗漏 `.phtml`、`.pht`、`.php5` 等。

**安全验证**: 扩展名白名单还是黑名单; 是否检查了 MIME 类型（可伪造但增加利用难度）; 存储目录是否在 Web 根目录外; 是否重命名为随机文件名; 上传目录是否禁止 PHP 执行。

**对应审计 skill**: `php-file-audit`

---

## 文件写入（WRITE）

**Sink 函数**: `file_put_contents`, `fwrite`, `fopen`（`w`/`a` 模式）, `fputs`

**危险模式**: 用户可控的内容写入 Web 可访问的 PHP 文件。常见场景: 配置文件写入、缓存文件生成、日志写入 PHP 文件。

**安全验证**: 写入路径是否用户可控; 写入内容是否用户可控; 目标文件是否在 Web 目录下且可被解析为 PHP; 是否对内容做了危险标签过滤。

**对应审计 skill**: `php-file-audit`

---

## 归档提取（ARCHIVE）

**Sink 函数**: `ZipArchive::extractTo`, `PharData::extractTo`, `tar` 相关操作

**危险模式**: 用户上传的压缩包被解压到 Web 目录，归档内包含恶意 PHP 文件（Zip Slip 攻击）。压缩包中的文件名可能包含 `../../` 实现目录穿越。

**安全验证**: 解压前是否校验了归档内文件名; 解压目标目录是否限制; 是否检查了归档内文件的扩展名。

**对应审计 skill**: `php-file-audit`

---

## XXE

**Sink 函数**: `DOMDocument::loadXML`, `DOMDocument::load`, `SimpleXMLElement`, `simplexml_load_string`, `simplexml_load_file`, `XMLReader::open`, `XMLReader::xml`

**危险模式**: 用户提交的 XML 数据被解析且未禁用外部实体加载。PHP 8.0+ 默认 `libxml_disable_entity_loader(true)` 但旧版本默认允许。

**安全验证**: 是否调用了 `libxml_disable_entity_loader(true)`（PHP < 8.0）; `LIBXML_NOENT` 标志是否被设置（设置了反而危险，会展开实体）; 是否使用 `LIBXML_DTDLOAD` 或 `LIBXML_DTDATTR`。

**对应审计 skill**: `php-serialization-audit`

---

## 反序列化（DESER）

**Sink 函数**: `unserialize`, `phar://` 协议触发函数（`file_exists`, `is_dir`, `is_file`, `file_get_contents`, `fopen`, `filectime`, `filesize`, `stat`, `md5_file`, `sha1_file`, `getimagesize` 等接受 phar:// 路径的函数）

**危险模式**: 用户可控数据进入 `unserialize()`; 或用户可控路径以 `phar://` 前缀触发 Phar 反序列化。关键在于项目中是否存在可利用的 Gadget Chain（`__destruct`、`__wakeup`、`__toString` 等魔术方法链）。

**安全验证**: `unserialize()` 的 `allowed_classes` 参数是否设置; 是否可以用 `json_decode` 替代; Phar 场景下路径前缀是否可控; 项目依赖中是否存在已知 Gadget（如 Monolog、Guzzle、Laravel 链）。

**对应审计 skill**: `php-serialization-audit`

---

## 模板注入（TPL）

**Sink 函数**: Twig `Environment::createTemplate`（用户输入作为模板内容）, Smarty `$smarty->fetch("string:".$input)`, Blade 动态编译

**危险模式**: 用户输入被当作模板代码编译执行，而非模板变量。区分"模板变量注入"（通常是 XSS）和"模板代码注入"（可 RCE）。

**安全验证**: 用户输入是作为模板变量（安全）还是模板内容（危险）传入; 模板引擎的沙箱模式是否开启; Twig 沙箱的策略配置。

**对应审计 skill**: `php-injection-audit`

---

## LDAP 注入（LDAP）

**Sink 函数**: `ldap_search`, `ldap_list`, `ldap_read`, `ldap_bind`（认证绕过）

**危险模式**: 用户输入拼入 LDAP 过滤器字符串（如 `(&(uid=$input)(userPassword=$pass))`），通过注入 `*`、`)(` 等字符修改查询逻辑。

**安全验证**: 是否对 `(`, `)`, `*`, `\`, `NUL` 做了转义; 是否使用了参数化的 LDAP 过滤器构造函数。

**对应审计 skill**: `php-injection-audit`

---

## 表达式注入（EXPR）

**Sink 函数**: `eval`, `assert`（PHP < 8.0 可执行字符串）, `preg_replace`（`/e` 修饰符，PHP < 7.0）, `create_function`（PHP < 8.0）, `call_user_func` / `call_user_func_array`（回调函数可控时）, `array_map`/`array_filter`/`usort`（回调参数可控时）

**危险模式**: 用户输入被作为 PHP 代码执行。`preg_replace` 的 `/e` 修饰符在 PHP 7.0 已移除但遗留系统仍可能存在。注意 `assert()` 在 PHP 7.0 变为语言结构但在 7.0 前可执行任意字符串。

**安全验证**: 是否存在对输入的白名单验证; 是否可以用更安全的替代方案（如 `preg_replace_callback` 替代 `/e`）; 回调函数名是否硬编码。

**对应审计 skill**: `php-injection-audit`

---

## 重定向（REDIR）

**Sink 函数**: `header("Location: $url")`, `header("Refresh: 0; url=$url")`, 框架方法: `redirect()`, `Redirect::to()`

**危险模式**: 用户输入控制重定向目标 URL，可用于钓鱼攻击（Open Redirect）。在 OAuth 等认证流程中，开放重定向可升级为 Token 窃取。

**安全验证**: 是否仅允许相对路径重定向; 是否有域名白名单; 是否检查了 URL scheme（防止 `javascript:` 协议）。

**对应审计 skill**: `php-frontend-audit`

---

## CRLF 注入

**Sink 函数**: `header()`, `setcookie()`（Cookie 值可控时）

**危险模式**: 用户输入中的 `\r\n`（`%0d%0a`）被带入 HTTP 头，可注入额外响应头或拆分响应体。PHP 5.4.0+ 的 `header()` 函数默认阻止多行头部，但 `setcookie()` 的处理因版本而异。

**安全验证**: PHP 版本是否 >= 5.4.0; 是否手动过滤了 `\r` 和 `\n`; `setcookie` 的值是否经过 URL 编码。

**对应审计 skill**: `php-frontend-audit`

---

## CSRF

**Sink 函数**: 无特定 Sink 函数——审计目标是所有执行状态变更操作（增删改、密码修改、权限变更）的路由/接口。

**危险模式**: 状态变更请求缺少 CSRF Token 验证，且仅依赖 Cookie 认证。注意区分: 纯 API（Bearer Token 认证）天然防 CSRF，Cookie 认证的 Web 接口才需要 CSRF 防护。

**安全验证**: 是否存在 CSRF Token 并在服务端验证; 是否使用了 `SameSite=Strict/Lax` Cookie 属性; 是否检查了 `Referer`/`Origin` 头（辅助防护，不能作为唯一手段）; 框架的 CSRF 中间件是否覆盖了所有状态变更路由。

**对应审计 skill**: `php-frontend-audit`
