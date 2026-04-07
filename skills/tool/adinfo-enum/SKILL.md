---
name: adinfo-enum
description: "使用 Adinfo 进行 Active Directory 信息收集。当获得域用户凭据后需要快速收集域环境信息时使用。Adinfo 是一个快速 AD 信息收集工具，一条命令输出域控列表、域管用户、信任关系、GPO、SPN、委派配置等关键信息——比手动 LDAP 查询快得多。发现域环境后第一步信息收集使用此技能"
metadata:
  tags: "adinfo,ad,domain,ldap,域,信息收集,枚举,域控,域管,SPN,委派,GPO,活动目录"
  category: "tool"
---

# Adinfo AD 信息快速收集

Adinfo 的价值在于**一条命令完成域环境全景信息收集**——域控、域管、信任、SPN、委派、GPO 等关键信息全部输出，省去手动写 LDAP 查询的麻烦。

项目地址：https://github.com/lzzbb/Adinfo

## 基本用法

```bash
# 使用域用户凭据收集
adinfo -d DOMAIN -u user -p password -dc DC_IP

# 使用 NTLM 哈希
adinfo -d DOMAIN -u user -H NTLM_HASH -dc DC_IP
```

## 输出内容

Adinfo 会自动收集并输出以下信息：

| 类别 | 内容 |
|------|------|
| 基本信息 | 域名、域 SID、功能级别 |
| 域控列表 | 所有 DC 的主机名和 IP |
| 域管用户 | Domain Admins / Enterprise Admins 成员 |
| 信任关系 | 域信任类型和方向 |
| 密码策略 | 最小长度、复杂度、锁定阈值 |
| SPN 账户 | 可 Kerberoast 的服务账户 |
| 委派配置 | 非约束委派 / 约束委派 / RBCD |
| AS-REP | 不需要预认证的账户 |
| GPO | 组策略列表 |
| OU 结构 | 组织单元层级 |
| 计算机账户 | 域内计算机列表 |

## 实战流程

```
获得域用户凭据后：
│
├─ 1. adinfo 快速收集全景信息
│     └→ 识别域管用户、SPN 账户、委派配置
│
├─ 2. 根据 adinfo 输出选择攻击路径
│     ├─ 有 SPN 账户 → Kerberoast (GetUserSPNs.py)
│     ├─ 有 AS-REP 账户 → AS-REP Roast (GetNPUsers.py)
│     ├─ 有非约束委派 → 委派攻击
│     ├─ 有信任关系 → 跨域攻击
│     └─ 密码策略弱 → 密码喷洒
│
├─ 3. 深入枚举（需要更详细信息时）
│     ├─ BloodHound → 可视化攻击路径
│     ├─ nxc ldap → 特定 LDAP 查询
│     └─ ldapsearch → 自定义过滤器
│
└─ 4. 横向移动 + 提权
```

## 与其他 AD 工具对比

| 工具 | 优势 | 适用场景 |
|------|------|---------|
| Adinfo | 一命令全景、输出精简 | 初始域信息收集 |
| BloodHound | 可视化攻击路径 | 复杂域环境路径分析 |
| nxc ldap | 灵活查询、模块丰富 | 特定信息查询 |
| ldapsearch | 原生 LDAP、最灵活 | 自定义复杂查询 |
