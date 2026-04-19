---
name: evasion-technique-integrate
description: "免杀技术整合：将免杀技术（API 混淆、字符串加密、Syscall、反调试、AMSI 绕过等）植入已有 Loader 代码。当需要向已有 Loader 添加新加载技术、或现有 Loader 被检测到需要替换组件时使用。先读 references/evasion-techniques-db.json 确认组件库中有你需要的技术，再执行集成"
metadata:
  tags: "evasion,integrate,api-hashing,xor,syscall,anti-debug,amsi,unhooking,bypass"
  category: "evasion"
---

# 免杀技术整合方法论

## ⛔ 深入参考

- 172 条免杀技术库 → [references/evasion-techniques-db.json](references/evasion-techniques-db.json)
- 整合模式与代码示例 → [references/integration-patterns.md](references/integration-patterns.md)

---

## 7 类免杀技术速查

| 类型 | 目的 | 复杂度 | 典型技术 |
|------|------|--------|---------|
| api_obfuscation | 隐藏 API 导入 | medium | API Hashing, IAT 混淆 |
| string_obfuscation | 隐藏敏感字符串 | simple | XOR 加密, 编译期混淆 |
| memory_evasion | 避免 RWX 内存页 | simple | 权限翻转 (RW→RX) |
| execution_evasion | 绕过 Hook | complex | 直接 Syscall, 间接 Syscall |
| anti_analysis | 检测调试/沙箱 | medium | IsDebuggerPresent, 时间差, CPU 核心数 |
| amsi_etw_bypass | 禁用 AMSI/ETW | medium | AmsiScanBuffer Patch, EtwEventWrite Patch |
| unhooking | 恢复被 Hook 的 DLL | complex | NTDLL 重映射 |

## 整合流程

```
1. 读取目标 Loader 源码
2. 查免杀技术库 → references/evasion-techniques-db.json
3. 分析兼容性
   ├─ 使用 RWX？ → 加 memory_evasion（权限翻转）
   ├─ 使用标准 API？ → 加 execution_evasion（Syscall）
   ├─ 有明文字符串？ → 加 string_obfuscation（XOR）
   └─ 无反调试？ → 加 anti_analysis
4. 逐项整合（参考 references/integration-patterns.md）
5. 交叉编译验证
6. 输出变更报告
```

## 兼容性矩阵

| Loader 特征 | 兼容技术 |
|------------|---------|
| 任意 Loader | API 混淆、字符串混淆、反调试 |
| 使用 RWX 内存 | 权限翻转 |
| 使用标准 Win API | Syscall 替换 |
| 未做 Unhook | NTDLL Unhooking |

## 快速代码示例

### 权限翻转（最常用）
```c
// Before: PAGE_EXECUTE_READWRITE（一步到位，易被检测）
LPVOID addr = VirtualAlloc(NULL, size, MEM_COMMIT, PAGE_EXECUTE_READWRITE);

// After: 先 RW 写入，再改 RX 执行
LPVOID addr = VirtualAlloc(NULL, size, MEM_COMMIT, PAGE_READWRITE);
memcpy(addr, shellcode, size);
VirtualProtect(addr, size, PAGE_EXECUTE_READ, &oldProtect);
```

### 字符串 XOR
```c
char dllName[] = { 0x1a, 0x14, 0x07, ... }; // XOR encrypted
for (int i = 0; i < sizeof(dllName); i++) dllName[i] ^= KEY;
```

## RWX 权限分离
- 两步操作：先写后执行（W+X 分离），不使用 RWX 一步到位
- 验证：编译通过、功能正常、验证执行结果
