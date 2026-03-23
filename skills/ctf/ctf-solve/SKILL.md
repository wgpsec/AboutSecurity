---
name: ctf-solve
description: "CTF 综合解题编排器。自动分析挑战类型并调度对应的专项 skill（pwn/crypto/web/reverse/forensics/osint/malware/misc）。给定 CTF 挑战文件或服务端点时使用"
metadata:
  tags: "ctf,solve,编排,orchestrator,challenge,解题"
  difficulty: "medium"
  icon: "🏁"
  category: "CTF"
---

# CTF 综合解题编排器

## 解题流程

### Step 1: 侦察

```bash
file *                          # 识别文件类型
strings binary | grep -i flag   # 快速字符串搜索
xxd binary | head -20           # Hex 头部
binwalk -e firmware.bin         # 提取嵌入文件
checksec --file=binary          # 检查保护
nc host port                    # 连接远程服务
```

### Step 2: 分类 → 调度 Skill

**按文件类型：**

| 文件类型 | 分类 | 调度 Skill |
|----------|------|-----------|
| .pcap/.evtx/.raw/.dd | 取证 | ctf-forensics |
| ELF/PE + 远程服务 | Pwn | ctf-pwn |
| ELF/PE/APK/.pyc/WASM | 逆向 | ctf-reverse |
| .py/.sage + 数字 | 密码学 | ctf-crypto |
| Web URL/HTML/JS/PHP | Web | ctf-web-methodology |
| 图片/音频/PDF(无明显内容) | 隐写取证 | ctf-forensics |

**按关键词：**

| 关键词 | 分类 |
|--------|------|
| overflow/ROP/shellcode/heap | ctf-pwn |
| RSA/AES/cipher/lattice/LWE | ctf-crypto |
| XSS/SQLi/JWT/SSRF | ctf-web-methodology |
| disk image/memory dump/registry | ctf-forensics |
| find/locate/identify/who/where | ctf-osint |
| obfuscated/C2/malware/beacon | ctf-malware |
| jail/sandbox/encoding/game | ctf-misc |

### Step 3: 卡住时转向

1. **重新分类** — 很多题跨分类（Web+Crypto, Forensics+Crypto, Reverse+Pwn）
2. **检查遗漏** — 隐藏文件、备用端口、响应头、注释、元数据
3. **简化** — 检查是否有更简单路径（默认凭据、已知CVE、逻辑漏洞）

**常见跨分类模式：**
- 取证 + 密码学：PCAP/磁盘中的加密数据
- Web + 逆向：WASM 或混淆 JS
- Web + 密码学：JWT 伪造、自定义签名
- 逆向 + Pwn：先逆向再利用
- OSINT + 隐写：社交媒体 Unicode 同形字

## Flag 格式

常见：`flag{...}` / `CTF{...}` / 自定义前缀（`ENO{...}` / `HTB{...}`）

```bash
grep -rniE '(flag|ctf|eno|htb|pico)\{' .
strings output.bin | grep -iE '\{.*\}'
```
