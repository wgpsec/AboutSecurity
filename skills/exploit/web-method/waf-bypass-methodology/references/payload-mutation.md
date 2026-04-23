# Payload 变形（通用技术）

本文档仅包含跨攻击类型通用的 payload 变形技术。
SQLi/XSS/命令注入的专用绕过 payload 见各攻击方法论的 references。

## 通用编码变形

```
# 大小写混合
SeLeCt、ScRiPt、UnIoN — 绕过区分大小写的正则

# NULL 字节插入
SE%00LECT、<scr%00ipt> — 部分 WAF 在 NULL 处截断匹配

# 注释插入（跨类型通用）
关键字中间插入注释打断签名匹配：
UNI/**/ON、SEL/**/ECT、al/**/ert
```

## 空格替代（通用）

```
%09    Tab
%0a    换行
%0c    换页
%0d    回车
/**/   内联注释（SQL/JS 通用）
```

## 字符串拼接/拆分

```
# 通用原理：将敏感关键字拆分成多段，绕过基于完整关键字的签名
# 具体拼接语法因目标语言不同而异，但拆分思路通用
'sel' + 'ect'
'al' + 'ert'
```

## 双重/多重编码

```
# URL 双重编码
' → %27 → %2527
< → %3C → %253C

# Unicode 编码
< → \u003c
' → \u0027

# HTML 实体编码
< → &lt; → &#60; → &#x3c;

# 混合编码（多层叠加）
先 URL 编码再 Unicode，或 HTML 实体嵌套
```

## 请求体格式切换

```
# 利用 WAF 只检查特定 Content-Type 的请求体
# 切换 Content-Type 可能让 payload 逃逸检测

application/x-www-form-urlencoded → multipart/form-data
application/x-www-form-urlencoded → application/json
application/json → application/xml
```
