# Checklist

---

# 网站前台

## 信息收集

- 子域枚举
- 搜集真实 IP
	- 端口扫描
- IP 反查
- whois 信息
- 目录扫描
- 组件版本信息

## 空白页面 / 403 / 默认 index 页面
- 目录爆破
	- 其他端口目录爆破
- [Bypass-403](https://github.com/iamj0ker/bypass-403) 工具
- protocol based bypass
    ```bash
    http://web.com/admin    # ===> 403
    https://web.com/admin   # ===> 200
    ```
- method based bypass
    ```bash
    OPTIONS
    GET
    HEAD
    POST
    PUT
    DELETE
    TRACE
    TRACK
    CONNECT
    PROPFIND
    PROPPATCH
    MKCOL
    COPY
    MOVE
    LOCK
    UNLOCK
    VERSION-CONTROL
    REPORT
    CHECKOUT
    CHECKIN
    UNCHECKOUT
    MKWORKSPACE
    UPDATE
    LABEL
    MERGE
    BASELINE-CONTROL
    MKACTIVITY
    ORDERPATCH
    ACL
    PATCH
    SEARCH
    ARBITRARY
    ```
- HTTP Header based bypass
    ```bash
    GET /admin HTTP/1.1
    Host: web.com   # ===> 403

    GET /anything HTTP/1.1
    Host: web.com
    X-Original-URL: /admin  # ===> 200

    GET /anything HTTP/1.1
    Host: web.com
    Referer: https://web.com/admin  # ===> 200

    GET https://qq.com HTTP/1.1
    Host: web.com   # ===> SSRF
    ```
- url character/parameter bypass
    ```bash
    /admin/panel    # ===> 403
    /admin/monitor  # ===> 200

    /admin/monitor/;panel   # ===> 302
    ```
    ```bash
    web.com/admin   # ===> 403

    web.com/ADMIN       # ===> 200
    web.com/admin/      # ===> 200
    web.com/admin/.     # ===> 200
    web.com//admin//    # ===> 200
    web.com/./admin/./  # ===> 200
    web.com/./admin/..  # ===> 200
    web.com/admin.json  # ===> 200(ruby)

    web.com/%2f/admin/  # ===> 200
    web.com/%2e/admin   # ===> 200
    web.com/%252e/admin # ===> 200
    web.com/%ef%bc%8fadmin  # ===> 200

    web.com/admin       # ===> 302
    web.com/admin..;/   # ===> 200
    ```
- CORS
- Open Redirect

## 传输过程

- COOKIE 注入
- COOKIE 跨站
- 用户凭证明文传输

## 敏感信息泄露

- 目录浏览
- 前端注释/显错
	- 后台路径、数据库地址泄露
	- 前端 package 打包
	- 报错页面信息泄露 (中间件版本、网站路径)
	- 组件版本信息泄露
- 敏感文件
	- 数据库备份、网站备份
	- 日志文件泄露
	- .SVN 源代码泄露
	- .git 源代码泄露
	- DS_Store 文件泄漏
	- WEB-INF/web.xml 信息泄露
	- idea 文件夹泄露
	- phpinfo 信息泄露
	- JS 敏感信息泄露
- 第三方
	- Github 泄露
- .env 泄露
- 开启 HTTP OPTIONS 方法

## 注册

- 验证码
	- 验证码重复利用
	- 验证码绕过
	- 验证码爆破
	- 验证码可控
	- 短信轰炸
- 恶意用户批量注册
- 反射型 XSS
- 存储型 XSS
- post 注入
- 遍历用户名
- 越权
	- 注册账号时可指定账号类型，存在越权可能

## 登录

- 爆破用户名
	- 撞库
	- 常见手机号
	- 常见登录账号(admin、manager、test、deme)
	- 数字组合(0-9、00-99、000-999、0000-9999、00000-99999)
	- 拼音(zhangsan、zhang.san、zhangs)
	- 中文(张三、李四、张san)
	- 英文名(Tom、Jeo、Cherry)
	- 单位名(zssx123、zssx@123)
	- 地名(beijing123、beijing@123)
	- 组合(地名+单位名)
	- 域名(baidu@123、JD@123)
	- 生日组合
- 错误回显
	- 输入一个错误的账号，提示“该账号不存在”，存在爆破账号可能
- 验证码
	- 验证码重复利用
	- 验证码绕过
	- 验证码爆破
	- 验证码可控
	- 短信轰炸
- XSS
	- 假如管理员在后台可以看到登录失败的日志，那么存在存储型 XSS 的可能
- JWT 复用
- 恶意锁定用户账户
- SQL 注入 (万能密码登录)
- 越权
	- 登录数据包中存在类似 type 的参数，可以修改测试越权

## 密码找回

- 爆破用户名
	- 撞库
	- 常见手机号
	- 常见登录账号(admin、manager、test、deme)
	- 数字组合(0~9、00~99、000~999、0000~9999、00000~99999)
	- 拼音(zhangsan、zhang.san、zhangs)
	- 中文(张三、李四、张san)
	- 英文名(Tom、Jeo、Cherry)
	- 单位名(zssx123、zssx@123)
	- 地名(beijing123、beijing@123)
	- 组合(地名+单位名)
	- 域名(baidu@123、JD@123)
- 验证码
	- 绕过重置密码验证
	- 验证码重复利用
	- 验证码爆破
	- 验证码可控
	- 短信轰炸
	- 短信验证码劫持
	- 用户邮箱劫持篡改
- 越权
	- 重置任意用户登录密码
	- 批量重置用户登录密码
- SQL注入(万能密码登录)

## 客服
- XSS
- 文件上传

## 支付 / 订单 / 充值 / 运费

- 修改 充值金额 / 商品金额
- 修改 购买数量 / 商品数量
- 遍历 订单信息 / 用户信息 / 交易信息
- 泄露 订单信息 / 用户信息 / 交易信息

## 抽奖 / 抢购 / 代金券 / 优惠卷 / 活动

- 盗刷积分
- 修改抽奖结果
- 刷取代金券 / 优惠卷 / 活动奖品 / 刷单 / 修改抽奖次数
- 低价抢购 / 修改代金券金额
- 抢购作弊
- 修改代金券数量
- 爆破兑换码
- 运费绕过

## 评论

- 恶意批量评论
- SQL 注入
- 任意文件上传
- CSRF
- 反射型 XSS
- 存储型 XSS
- 越权评论(冒充管理员)

## 上传点

- 云平台 API key 泄露
- 解析漏洞
	- IIS 解析漏洞
	- Nginx 解析漏洞
	- Apache 解析漏洞
	- CGI 解析漏洞
- 恶意上传
	- zip、mp4 占用资源
	- HTML XSS
- 后缀名Fuzz
    - [AboutSecurity/Dic/Web/Upload/](./Dic/Web/Upload)
    - web通用
        - htm
        - html
        - shtml
    - .net
        - asp
        - aspx
        - asa
        - cer
        - cdx
        - ashx
        - asmx
        - svc
        - cshtml
        - vbhtml
    - java
        - jsp
        - jspa
        - jsps
        - jspx
        - jspf
    - php
        - php
        - php1
        - php2
        - php3
        - php4
        - php5
        - phtml
    - Misc
        - txt
        - svg
        - pdf
        - xml
        - xlsx
- 大小写(windows)
    - `xxx.pHp`、`xxx.Jsp`
- 空格绕过
    - `xxx .php`
    - `xxx.php `
- 点绕过
    - `xxx.php.`
- 换行
    - `xxx.txt%0aphp`
    - `xxx.ph\np`
- .空格. 绕过(windows)
    - `xxx.php .`
    - `xxx.php .jpg`
    - `xxx.php. .jpg`
- 特殊字符
    - `xxx.php::$DATA` (windows)
    - `xxx.php::$DATA......` (windows)
    - `xxx.php/`
    - `xxx.php?`
    - `xxx./php` (linux)
- 特殊字符+白后缀
    - `xxx.php.jpg`
    - `xxx.php_.jpg`
    - `xxx.php/1.jpg`
    - `xxx.php{}.jpg`
    - `xxx.php;jpg`
    - `xxx.php;.jpg`
    - `xxx.php;+x.jpg`
    - `xxx.php:1.jpg`
    - `xxx.php.123`
    - `xxx.jpg/.php`
    - `xxx.jpg/php`
    - `xxx.jpg/1.php`
    - `xxx.jpg{}.php`
- 双写绕过
    - `phpphp.php`
    - `php.php`
    - `xxx.pphphp`
    - `xxx.asaspxpx`
- 00 截断
- .htaccess
- 中间件解析漏洞
- 参数
    - 修改 `filename="xx.php"` 为 `filename==="xxx.php"`
    - 修改 `filename="xx.php"` 为 `filename='xxx.php'`
    - 修改 `filename="xx.php"` 为 `filename=xxx.php`
- 添加图片头
    - `GIF89a`
- 恶意覆盖
	- 覆盖资源文件造成全局XSS
	- 覆盖配置文件修改配置
- Content-Type Fuzz
- 后端二次渲染
	- 图片马
- 访问拦截
	- 路径
		- `xxx.com/test/img/1.png/../../shell.php`
	- 解析
		- `xxx.com/shell.php;/.png`

## 下载 / 导出

- XXE
- 目录遍历
- 任意文件读取
- DOS(打包某个盘)

## CMS框架 / 中间件框架 / WEB组件 / WEB服务 漏洞

- 见 [BS-Exploits](https://github.com/ffffffff0x/1earn/blob/master/1earn/Security/RedTeam/Web%E5%AE%89%E5%85%A8/BS-Exploits.md)

---

# 网站后台

## 第三方商家

- 商家账户遍历
- 越权访问其他商家用户

## 后台配置

- 后台路径泄露
- post 注入
- 数据库备份 getwebshell
- 配置文件写入木马
- 任意文件上传漏洞
- 万能密码登录
- 开源编辑器、插件漏洞
- 后台越权访问
- 暴力破解管理员账号
- CSRF
- 存储型 XSS
- 目录遍历

## 会员系统

- 用户越权访问
- 个人资料信息泄露
- 登录验证绕过
- 重置任意账户密码
- 开源编辑框、插件漏洞
- GET 注入
- 登录框 POST 注入
- CSRF
- 用户组水平越权
- 任意文件上传
- 反射型 XSS
- 存储型 XSS
- 个人资料遍历

## 数据库管理

- 直接执行 SQL 语句
- 数据库备份写 shell

---

# 主机

- 端口扫描

- 系统漏洞
	- windows
		- MS12-020
		- MS15-048
		- MS17-010
		- CVE-2019-0708
	- linux
		- shellshock

- 编程语言
	- Java_RMI
	- jdwp
	- Python_PDB
	- ruby-debug-ide

- 文件服务
	- FTP 弱口令/匿名
	- NFS 弱口令/未授权访问
	- Rsync 弱口令/未授权访问
	- Samba 弱口令/未授权访问

- 数据库
	- CouchDB 未授权访问漏洞/任意命令执行漏洞
	- memcached 未授权访问漏洞
	- MSSQL 弱口令
	- MYSQL 弱口令
	- ORACLE 弱口令、CVE-2012-1675
	- OrientDB 远程代码执行漏洞
	- PostgreSQL 弱口令
	- Redis 未授权访问漏洞

- 容器 & 虚拟化
	- Citrix_Receiver 弱口令 / 未授权访问漏洞
	- Docker 逃逸

- 分布式
	- Hadoop 未授权访问漏洞
	- Kubernetes 未授权访问漏洞
	- Spark 未授权访问漏洞
	- ZooKeeper 未授权访问漏洞

- 集成
	- Phpstudy 后门 RCE/nginx 解析漏洞
	- 宝塔面板 phpMyadmin 未授权访问

---

# 域

- pth/ptt/ptk
- NTDS.DIT
- GPP
- Kerberoast
- Kerberoasting
- 委派
- 毒化 LLMNR 和 NBT-NS 请求
- MS14-068
- cve-2020-1472 Zerologon

---

# 网络设备(路由器、交换机)

- 端口扫描
- SSH、Telnet 弱口令
- web 弱口令
- SNMP 默认字符串
- CVE 漏洞

---

# 安全设备(WAF、EDR)

- 见 [SecDevice-Exploits](https://github.com/ffffffff0x/1earn/blob/master/1earn/Security/RedTeam/%E5%AE%89%E9%98%B2%E8%AE%BE%E5%A4%87/SecDevice-Exploits.md)

---

# 工控 ICS 环境

- 上位机编程软件
	- WebAccess 远程溢出漏洞
	- 组态王远程溢出漏洞
	- EcoStruxure Control Expert 漏洞
- 上位机远程服务
	- RDP
	- MS17-010
	- CVE-2019-0708
- PLC 攻击
	- Siemens
		- snap7
		- step7
	- OpenPLC
		- 弱口令
	- Modbus
		- ModbusPoll
	- Schneider
		- EcoStruxure Control Expert
		- MSF(use auxiliary/admin/scada/modicon_command)

---

# 移动端 / 客户端

- 服务端与客户端交互漏洞
- API 接口漏洞
- XSS - 存储型
- 代码执行
- 内存溢出
- DLL 劫持
- 不安全的加密算法
- 源代码泄露
- 键盘劫持
- XSS - 反射型
- 任意备份
- 二次编译
- 拒绝服务
- XSS - DOM 型
- 内核提权
- 弱证书校验
- 第三方 SDK 漏洞
