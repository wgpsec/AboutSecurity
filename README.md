# AboutSecurity

* **Dic**
    * Auth : 认证字典
        * 账号和密码。
    * Network : 网络
        * 排除的私有 IP 段、本地 IP 段、dns 服务器列表。
    * Port : 端口字典
        * 按照端口渗透的想法,将不同端口承载的服务可爆破点作为字典内容。
    * Regular : 规则字典
        * 各种规则、排列的字典整理。
    * Web : Web 字典
        * web 渗透过程中出现的可爆破点作为字典内容。
* **Payload**
    * Burp
    * CORS
    * email
    * Format
    * HPP
    * LFI
    * OOB
    * SQL-Inj
    * SSI
    * XSS
    * XXE
* **Skills** — AI Agent 技能方法论 (51 skills)
    * recon (5) : 侦察类 — 资产侦察、被动信息收集、子域名深挖、目标画像、社会工程
    * exploit (26) : 漏洞利用类 — SQL 注入、XSS、SSTI、文件上传、反序列化、JWT、GraphQL、SSRF/XXE、CORS、CSRF、OAuth、WebSocket、竞态条件、缓存投毒/请求走私等
    * ctf (5) : CTF 竞赛类 — Web 解题方法论、CTF 侦察、源码审计、Flag 搜索、Flag 校验
    * postexploit (6) : 后渗透类 — Linux/Windows 后渗透、提权检查、凭据喷射、横向移动、持久化
    * lateral (3) : 内网渗透类 — AD 域攻击、内网侦察、多层网络穿透
    * cloud (2) : 云环境类 — 云元数据利用、IAM 权限审计与提权
    * general (4) : 综合类 — 红队评估、移动后端 API、报告生成、供应链审计
    * 📊 **Skill Benchmark**: `python scripts/bench-skill.py --all` — A/B 测试 Skill 对 Agent 的实际效果
* **Tools** — 外部工具声明式 YAML 配置
    * scan : 扫描工具 (nmap, masscan)
    * fuzz : Fuzz 工具 (dirsearch)
* **Doc**
    * **Checklist** : 渗透测试过程中的检查项,杜绝少测、漏测的情况。
    * **Cheatsheet** : 渗透测试信息收集表,渗透测试时直接复制一副作为参考、信息记录、方便团队协作、出报告等。
    * **出报告专用** : 记录部分平常渗透测试遇到的案例。
    * **行业名词**
