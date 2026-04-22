---
name: argocd-tactics
description: |
  ArgoCD 后渗透方法论：Redis缓存投毒集群接管、SSO认证绕过、未授权API枚举、恶意Application部署、Webhook SSRF、默认凭据利用。
  当用户提到ArgoCD漏洞、ArgoCD利用、ArgoCD RCE、ArgoCD Redis、ArgoCD未授权、ArgoCD检测、GitOps安全时，必须使用此技能。
  也适用于用户提到K8s持续交付、Kubernetes GitOps、ArgoCD集群接管、ArgoCD缓存投毒等场景。
metadata:
  tags: "ArgoCD,Kubernetes,GitOps,Redis,缓存投毒,SSO绕过,SSRF,K8s集群接管,持续交付,未授权API"
  category: "postexploit"
  mitre_attack: "T1190,T1078"
---

# ArgoCD 漏洞利用技能

- **产品**: Argo CD (Kubernetes声明式GitOps持续交付工具)
- **默认端口**: 80/443 (Web UI), 8080 (Server), 6379 (Redis)
- **识别特征**: 页面标题 "Argo CD"，`/api/v1/version` 返回版本信息
- **默认凭据**: admin / auto-generated初始密码
- **FOFA**: `app="Argo-CD"` | **Shodan**: `http.title:"Argo CD"`

## 漏洞总览

| CVE | 影响版本 | 类型 | 条件 | 危害 |
|-----|---------|------|------|------|
| CVE-2024-31989 | <2.11.5 | Redis缓存投毒→K8s接管 | Redis未认证 | Critical (9.1) |
| CVE-2022-29165 | <2.3.1 | SSO认证绕过 | 配置OIDC SSO | High (8.8) |
| CVE-2023-22482 | 多版本 | Redis信息泄露 | Redis未认证 | High (7.5) |
| CVE-2024-40638 | 多版本 | Webhook SSRF | 已认证用户 | High (7.2) |
| 默认凭据 | 全版本 | 初始admin密码 | 获取初始密码 | Critical |

## 利用决策树

```
1. 识别ArgoCD → /api/v1/version
2. 未授权API → /api/v1/applications, /api/v1/clusters
3. CVE-2024-31989 (优先) → Redis缓存投毒 → 集群接管
4. 默认凭据 → admin + 初始密码 → 完全控制
5. CVE-2022-29165 (SSO环境) → redirect_uri绕过
6. CVE-2024-40638 → Webhook SSRF
7. 已认证后利用 → 恶意Application / 注入Manifest / 越权
```

## 利用链优先级

```
1. Redis未授权 → CVE-2024-31989缓存投毒 → K8s集群接管
2. 默认凭据/弱口令 → ArgoCD完全控制
3. 未授权API → 应用/集群/仓库信息泄露
4. CVE-2022-29165 → SSO认证绕过
5. CVE-2024-40638 → Webhook SSRF → 内部服务探测
6. 已认证 → 创建恶意Application → 特权Pod部署
```

## 常用端点速查

| 端点 | 方法 | 用途 | 认证 |
|------|------|------|------|
| `/api/v1/version` | GET | 版本信息 | 不需要 |
| `/api/v1/applications` | GET | 应用列表 | 可选 |
| `/api/v1/clusters` | GET | 集群列表 | 可选 |
| `/api/v1/repositories` | GET | 仓库列表 | 可选 |
| `/api/v1/account` | GET | 账户信息 | 可选 |
| `/auth/login` | GET | 登录页面 | 不需要 |
| `Redis 6379` | - | 缓存服务 | 默认无密码 |

## 详细参考

- [检测脚本与后利用手法](references/detection-and-post-exploit.md) - 未授权API检测、综合扫描脚本、已认证后利用技术
