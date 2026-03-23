---
name: ctf-pwn
description: "CTF 二进制漏洞利用(Pwn)技术。用于缓冲区溢出、格式化字符串、堆利用(House of Orange/Spirit/tcache)、ROP链、内核利用、沙箱逃逸等 CTF Pwn 类挑战"
metadata:
  tags: "ctf,pwn,binary,exploit,overflow,rop,heap,kernel,shellcode,格式化字符串"
  difficulty: "hard"
  icon: "💥"
  category: "CTF"
---

# CTF 二进制漏洞利用 (Pwn)

## 深入参考

- 栈溢出/ret2win/Canary绕过 → 读 [references/overflow-basics.md](references/overflow-basics.md)
- ROP基础（ret2libc/syscall ROP/坏字符绕过） → 读 [references/rop-and-shellcode.md](references/rop-and-shellcode.md)
- ROP进阶（SROP/seccomp绕过/RETF架构切换） → 读 [references/rop-advanced.md](references/rop-advanced.md)
- 格式化字符串（泄漏/GOT覆写/Blind Pwn） → 读 [references/format-string.md](references/format-string.md)
- 堆利用/UAF/JIT/自定义分配器 → 读 [references/advanced.md](references/advanced.md)
- 高级利用技术 Part1（VM/类型混淆/FSOP） → 读 [references/advanced-exploits.md](references/advanced-exploits.md)
- 高级利用技术 Part2（io_uring/TLS劫持/Windows SEH） → 读 [references/advanced-exploits-2.md](references/advanced-exploits-2.md)
- 高级利用技术 Part3（JIT沙箱/DNS压缩/ELF签名绕过） → 读 [references/advanced-exploits-3.md](references/advanced-exploits-3.md)
- 沙箱逃逸（自定义VM/FUSE/受限Shell） → 读 [references/sandbox-escape.md](references/sandbox-escape.md)
- 内核利用基础（QEMU/堆喷/modprobe_path） → 读 [references/kernel.md](references/kernel.md)
- 内核利用技术（tty_struct/userfaultfd/SLUB） → 读 [references/kernel-techniques.md](references/kernel-techniques.md)
- 内核保护绕过（KASLR/KPTI/SMEP/SMAP） → 读 [references/kernel-bypass.md](references/kernel-bypass.md)

---

## 分类决策树

```
Pwn 题目分析？
├─ 检查保护: checksec binary
│  ├─ PIE 关闭 → 地址固定，直接覆写 GOT/PLT
│  ├─ Partial RELRO → GOT 可写
│  ├─ Full RELRO → 需找替代目标(hooks/vtable/返回地址)
│  ├─ NX 开启 → 不能执行栈/堆shellcode → 用 ROP
│  └─ Canary → 需泄漏或绕过
├─ 漏洞类型
│  ├─ 栈溢出 → references/overflow-basics.md
│  ├─ 格式化字符串 → references/format-string.md
│  ├─ 堆(UAF/double free/tcache) → references/advanced.md
│  ├─ 竞争条件(pthread/usleep) → race exploit
│  └─ 内核模块 → references/kernel.md
└─ 利用链
   ├─ 泄漏 → 计算libc基址 → one_gadget / system
   ├─ ROP → ret2libc / ret2dlresolve / SROP
   └─ 堆 → House of X / tcache poisoning → __free_hook
```

## 保护机制速查

| 保护 | 状态 | 影响 |
|------|------|------|
| PIE | 关闭 | GOT/PLT/函数地址固定 |
| RELRO | Partial | GOT 可写 → GOT覆写 |
| RELRO | Full | GOT 只读 → 需hooks/vtable |
| NX | 开启 | 栈不可执行 → ROP |
| Canary | 有 | 需泄漏canary或用堆 |

## 常见危险函数

```
gets() / scanf("%s") / strcpy()  → 栈溢出
printf(user_input)               → 格式化字符串
free() 后继续使用               → UAF
```

## pwntools 模板

```python
from pwn import *
context.binary = elf = ELF('./binary')
libc = ELF('./libc.so.6')
p = remote('host', port)  # or process('./binary')
# 泄漏 → 计算基址 → 覆写 → getshell
```

## 竞争条件利用

```bash
bash -c '{ echo "cmd1"; echo "cmd2"; sleep 1; } | nc host port'
```
