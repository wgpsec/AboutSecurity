# Portainer 认证突破与认证后RCE

## 一、默认凭据与认证突破

常见默认凭据及弱口令组合用于 Portainer 初始认证突破。

---

## 二、认证后Docker API RCE (特权容器逃逸)

### Portainer API端点速查

| 端点 | 方法 | 用途 |
|------|------|------|
| `/api/auth` | POST | 登录获取JWT Token |
| `/api/endpoints` | GET | 获取Docker端点列表 |
| `/api/endpoints/{id}/docker/images/json` | GET | 列出可用镜像 |
| `/api/endpoints/{id}/docker/containers/create` | POST | 创建容器 |
| `/api/endpoints/{id}/docker/containers/{id}/start` | POST | 启动容器 |
| `/api/endpoints/{id}/docker/containers/{id}/wait` | POST | 等待容器执行完成 |
| `/api/endpoints/{id}/docker/containers/{id}` | DELETE | 删除容器 |
| `/api/endpoints/{id}/docker/images/load` | POST | 上传镜像 |
