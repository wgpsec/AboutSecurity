# PHP 序列化与模板类漏洞审计模式参考

3 类漏洞的危险代码 / 安全代码对比 + EVID_* 证据格式示例。

---

## 1. 反序列化

### 1.1 unserialize 危险调用模式

```php
// 危险: Cookie / POST / 缓存 / 数据库 — 数据用户可控或可被投毒
$profile = unserialize($_COOKIE['user_profile']);
$data = unserialize(base64_decode($_POST['session_data']));
$obj = unserialize($redis->get('user:' . $userId));
$config = unserialize($pdo->query("SELECT config FROM settings")->fetchColumn());

// 安全: json_decode 替代 | allowed_classes 限制（PHP 7.0+）
$profile = json_decode($_COOKIE['user_profile'], true);
$obj = unserialize($data, ['allowed_classes' => false]);           // 禁止所有类
$obj = unserialize($data, ['allowed_classes' => ['AllowedClass']]); // 白名单
```

### 1.2 allowed_classes 配置

| 值 | 行为 | 安全性 |
|----|------|--------|
| `true`（默认） | 允许所有类实例化 | 不安全，等同无限制 |
| `false` | 所有对象转为 `__PHP_Incomplete_Class` | 安全，阻止所有 Gadget |
| `['ClassName']` | 仅允许白名单中的类 | 取决于白名单类是否含危险方法 |

缺省第二参数等于 `allowed_classes => true`，搜索 `unserialize` 时必须检查。

### 1.3 Phar 反序列化触发函数（40+）

Phar metadata 在文件系统函数处理 `phar://` 路径时自动反序列化，无需 `unserialize`。

| 分类 | 函数 |
|------|------|
| 文件信息 | `file_exists`, `is_file`, `is_dir`, `is_link`, `is_readable`, `is_writable`, `is_executable`, `fileatime`, `filectime`, `filemtime`, `filesize`, `filetype`, `fileperms`, `fileowner`, `filegroup`, `fileinode` |
| 文件读写 | `fopen`, `file_get_contents`, `file_put_contents`, `readfile`, `file`, `fgets`, `fread`, `fpassthru` |
| 文件操作 | `copy`, `rename`, `unlink`, `stat`, `lstat`, `touch`, `mkdir` |
| 目录/哈希 | `opendir`, `scandir`, `glob`, `md5_file`, `sha1_file`, `hash_file`, `hash_hmac_file` |
| 图像/包含 | `getimagesize`, `exif_read_data`, `include`, `require`, `include_once`, `require_once` |
| SPL/其他 | `parse_ini_file`, `realpath`, `SplFileObject`, `SplFileInfo`, `DirectoryIterator` |

```php
// 危险: 路径用户可控 → phar://./uploads/evil.jpg 触发反序列化
if (file_exists($_GET['avatar'])) { ... }
$size = getimagesize($_POST['image_url']);

// 安全: 协议过滤 + 路径白名单
if (preg_match('/^phar:\/\//i', $userInput)) { die('blocked'); }
```

### 1.4 POP 链构造方法论

**入口魔术方法**:

| 方法 | 触发时机 |
|------|----------|
| `__destruct` | 对象销毁（最常见，GC 回收时自动触发） |
| `__wakeup` | `unserialize()` 完成后立即调用 |
| `__toString` | 对象被当作字符串使用（echo/拼接/比较） |
| `__call`/`__get`/`__set`/`__invoke` | 不存在的方法/属性/函数调用（链中跳板） |

**链搜索策略**: (1) 正向 — 从 `__destruct`/`__wakeup` 出发追踪 `$this->xxx->yyy()` 可控属性调用; (2) 反向 — 从危险 Sink 回溯到魔术方法触发路径; (3) Composer 依赖 — 检查 `vendor/` 中 Monolog/Guzzle/Doctrine 等已知 Gadget 链。

**常见 Gadget 特征**: `__destruct` 中 `$this->handler->close()` 可重定向任意类; `__toString` 中 `$this->formatter->format()` 格式化器链; 析构中 `unlink($this->tempFile)` 任意删除; 日志 `file_put_contents($this->logFile, ...)` 任意写入。

### 1.5 EVID_DESER 证据格式

```
[EVID_DESER_UNSERIALIZE_CALL]  CacheService.php:87 | unserialize($cached)
[EVID_DESER_DATA_SOURCE]  :82-86 | $cached=$redis->get('sess:'.$sid) | Cookie 可控
[EVID_DESER_ALLOWED_CLASSES]  未设置（默认 true）→ 可实例化任意类
[EVID_DESER_POP_CHAIN_ENTRY]  vendor/monolog/.../BufferHandler.php
  __destruct()→$this->handler->close()→StreamHandler→file_put_contents→任意写入
[EVID_DESER_PHAR_TRIGGER]  AvatarController.php:45 | file_exists($_GET['path']) | phar://未过滤
```

---

## 2. XXE（XML 外部实体注入）

### 2.1 PHP XML 解析器安全配置矩阵

| 解析器 | PHP 8.0+ 默认安全 | PHP < 8.0 默认安全 | 危险标志 |
|--------|:---:|:---:|----------|
| `DOMDocument::loadXML` | 是 | 否 | `LIBXML_NOENT` |
| `simplexml_load_string/file` | 是 | 否 | `LIBXML_NOENT` |
| `XMLReader::xml/open` | 是 | 否 | `LIBXML_NOENT` |
| `DOMDocument::load` | 是 | 否 | `LIBXML_NOENT`, `LIBXML_DTDLOAD` |
| `xml_parse` (expat) | 是 | 是 | 无（不解析外部实体） |

### 2.2 LIBXML 标志详解

| 标志 | 效果 | 风险 |
|------|------|------|
| `LIBXML_NOENT` | 展开所有实体引用（含外部） | **Critical** — 直接导致 XXE |
| `LIBXML_DTDLOAD` | 允许加载外部 DTD | High — 外部 DTD 可定义恶意实体 |
| `LIBXML_DTDATTR` | 使用 DTD 默认属性值 | Medium — 可能间接引入实体 |
| `LIBXML_NONET` | 禁止网络访问 | 防护性标志 |

```php
// 危险: LIBXML_NOENT
$dom->loadXML($userXml, LIBXML_NOENT);            // 任何 PHP 版本均 XXE
// 危险: PHP < 8.0 未禁用
simplexml_load_string($userXml);                    // PHP 7.x 默认不安全

// 安全: PHP < 8.0
libxml_disable_entity_loader(true);
$dom->loadXML($userXml);
// 安全: PHP 8.0+ 不传 LIBXML_NOENT
$dom->loadXML($userXml);                           // 默认安全
```

### 2.3 XXE payload 类型

| 类型 | 用途 | 条件 |
|------|------|------|
| 文件读取 | `<!ENTITY xxe SYSTEM "file:///etc/passwd">` | 回显到响应 |
| SSRF | `<!ENTITY xxe SYSTEM "http://internal:8080/">` | 可发起网络请求 |
| DoS | Billion Laughs 递归实体膨胀 | 实体展开未限制 |
| 盲 XXE+带外 | 参数实体 + 外部 DTD 回传数据 | 无回显但允许外连 |

盲 XXE OOB 模式: 恶意 XML 引用攻击者 DTD → DTD 用 `php://filter` 读文件 → 通过 HTTP 参数外传。即使无回显，服务器可外连即可利用。

### 2.4 PHP 8.x libxml 行为变化

- PHP 8.0: `libxml_disable_entity_loader()` 废弃，默认不加载外部实体
- PHP 8.0+: 不传 `LIBXML_NOENT` 时安全；传入 `LIBXML_NOENT` 仍然危险
- 审计策略: PHP 8.0+ 只搜 `LIBXML_NOENT`；PHP < 8.0 检查全局 `libxml_disable_entity_loader`

### 2.5 EVID_XXE 证据格式

```
[EVID_XXE_PARSE_CALL]  XmlImporter.php:34 | $dom->loadXML($xmlInput, LIBXML_NOENT)
[EVID_XXE_INPUT_SOURCE]  :28-33 | $xmlInput=file_get_contents('php://input') | 完全可控
[EVID_XXE_ENTITY_CONFIG]  LIBXML_NOENT 已传入 → 外部实体展开
[EVID_XXE_LIBXML_LOADER]  未调用 libxml_disable_entity_loader | PHP 7.4
[EVID_XXE_OUTPUT_CHANNEL]  :52 $dom->saveXML() 回显 → 非盲 XXE
```

---

## 3. SSTI（服务端模板注入）

### 3.1 Twig 注入

```php
// 危险: 用户输入直接作为模板字符串
$twig->createTemplate("Hello " . $userInput)->render([]);

// 安全: 沙箱 + 严格策略
$policy = new \Twig\Sandbox\SecurityPolicy(['if','for'], ['escape','upper'], [], [], []);
$twig->addExtension(new \Twig\Extension\SandboxExtension($policy, true));
```

注入 payload: `_self.env.registerUndefinedFilterCallback("system")` (Twig 1.x); `{{['id']|map('system')}}` (Twig 3.x); `{{app.request.server.all|join}}` (信息泄露)。

审计: 搜索 `createTemplate` / `Environment::render`，追踪模板字符串是否含用户输入。`.twig` 文件 + 变量传递模式下 `{{ var }}` 自动转义是安全的。

### 3.2 Smarty 注入

```php
// 危险: 模板字符串拼接 → {if} 表达式注入
$tpl = '{if ' . $_GET['expr'] . '}{/if}';
$smarty->display('string:' . $tpl);   // expr=system('id') → RCE

// 安全: Security Policy
$smarty->enableSecurity('Smarty_Security');
```

审计重点: `display('string:' . $userInput)` 直接注入; `security_policy` 是否禁用 `{php}`/`{include}`/`{fetch}`; `{if}` 中表达式可控性（区分变量赋值 vs 模板拼接）。

### 3.3 Blade 注入

```php
{!! $userComment !!}   // 未转义输出 → 若用户可控则 XSS
@php ... @endphp       // 若模板文件可被用户写入（CMS）→ RCE
{{ $safe }}            // 自动转义，安全
```

审计: `{!! $var !!}` 变量来源; CMS 是否允许编辑 `.blade.php`; `Blade::compileString($userInput)` 极少见但致命。

### 3.4 自定义模板引擎

```php
// 模式 1: str_replace + eval — 自研引擎最常见致命组合
$tpl = str_replace('{{content}}', $userContent, file_get_contents($path));
eval('?>' . $tpl);    // $userContent 含 <?php system('id');?> → RCE

// 模式 2: extract + include — 变量覆盖导致 LFI
extract($_POST);
include $templateFile; // $templateFile 被覆盖
```

审计: 搜索 `eval` + 模板关键词（template/tpl/render/compile），检查用户输入是否在 eval 前被注入。

### 3.5 EVID_TPL 证据格式

```
[EVID_TPL_RENDER_CALL]  PageController.php:67 | $twig->createTemplate($greeting)->render()
[EVID_TPL_TEMPLATE_SOURCE]  :62-66 | $greeting="Welcome, ".$request->input('name')."!"
  用户输入直接拼入模板字符串
[EVID_TPL_ENGINE_CONFIG]  Twig 3.8 | 未启用 SandboxExtension
[EVID_TPL_INJECTION_VECTOR]  name={{['id']|map('system')}} → RCE | 未认证路由
```
