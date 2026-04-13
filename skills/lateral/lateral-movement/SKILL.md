---
name: lateral-movement
description: "横向移动技术。当已获取凭据（密码/哈希/密钥/票据）需要从当前主机移动到其他主机时使用。覆盖 SSH、RDP、WMI、PSExec、PTH、PTT、DCOM 等技术。根据目标操作系统和可用凭据类型选择最佳移动方式"
metadata:
  tags: "lateral,横向移动,ssh,rdp,wmi,psexec,pth,pass the hash,dcom,winrm,pivot"
  category: "lateral"
---

# 横向移动方法论

## ⛔ 深入参考（必读）

- 需要 WinRM/PSExec/WMI/DCOM/RDP/PTT 各技术的具体命令 → [references/movement-techniques.md](references/movement-techniques.md)

---

## Phase 1: 目标发现

```bash
arp -a                              # 已通信的主机
naabu -host 10.0.0.0/24 -p 22,80,135,445,3389,5985 -silent
```

| 目标 | 价值 |
|------|------|
| 域控 | 极高（控制整个域） |
| 数据库/文件/备份服务器 | 高（敏感数据） |
| 跳板机 | 中（连接更多网段） |

## Phase 2: 技术选择决策树

```
凭据类型 + 目标 OS？
├─ Linux
│   └─ SSH 密码/密钥（chmod 600!）
├─ Windows + 明文密码
│   └─ WinRM > WMI > PSExec（按隐蔽性）
├─ Windows + NTLM 哈希
│   └─ PTH via WinRM/WMI/PSExec
├─ Kerberos 票据
│   └─ PTT（mimikatz kerberos::ptt）
├─ 跨网段
│   └─ SSH 隧道/SOCKS 代理
└─ 需要图形界面
    └─ RDP
详细命令 → [references/movement-techniques.md](references/movement-techniques.md)
```

## Phase 3: 移动后操作

1. 确认权限 — `whoami /all` 或 `id`
2. 重复后渗透流程 — 参考 `post-exploit-linux` 或 `post-exploit-windows`
3. 收集新凭据 — 可能发现更高权限凭据
4. 评估下一步目标

## 注意事项
- **PSExec 创建服务 → 有明显日志**，优先用 WMI/WinRM
- PTH 只对 NTLM 认证有效（Kerberos-only 环境不行）
- 多次失败可能触发告警，控制尝试频率

## SSH 密钥认证横向
- SSH 密钥/私钥（id_rsa）发现后直接登录
- 注意文件权限：权限太宽松（如 0644 / too open）SSH 会拒绝
- SSH 安全要求：私钥文件权限必须为 600
