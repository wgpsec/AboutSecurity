---
id: JUPYTER-NOTEBOOK-RCE
title: Jupyter Notebook 未授权访问RCE漏洞
product: jupyter
vendor: Jupyter
version_affected: "全版本"
severity: CRITICAL
tags: [rce, 无需认证]
fingerprint: ["Jupyter", "Notebook"]
---

## 漏洞描述

Jupyter Notebook 未配置密码时，攻击者可以直接访问 Web 界面创建终端并执行任意 Python 代码和系统命令。

## 影响版本

- Jupyter Notebook 全版本（未配置密码时）

## 前置条件

- 无需认证
- Jupyter 未配置密码

## 利用步骤

1. 访问 Jupyter Web 界面
2. 选择 new -> terminal 创建终端
3. 执行任意命令

## Payload

```bash
# 直接在 Web 界面操作或使用 API
# 访问 http://target:8888
# 点击 "new" -> "terminal"
# 在终端中执行命令
```

## 验证方法

```bash
# 检查是否无需密码即可访问
curl -s http://target:8888 | grep -i "jupyter"
```

## 修复建议

1. 为 Jupyter Notebook 设置强密码
2. 启用 Jupyter 密码认证
3. 限制 Jupyter 访问来源
