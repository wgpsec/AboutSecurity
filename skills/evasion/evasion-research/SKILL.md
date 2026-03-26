---
name: evasion-research
description: "GitHub 安全研究方法论：搜索 GitHub 上的免杀/Loader/C2 技术仓库，分析代码模式，提取新技术入库。当需要搜索新免杀技术、分析开源仓库、更新知识库时使用。"
metadata:
  tags: "research,github,evasion,loader,shellcode,technique,knowledge-base,规避研究,检测绕过,bypass研究,规避检测"
  difficulty: "easy"
  icon: "🔍"
  category: "免杀对抗"
---

# GitHub 安全研究方法论

## ⛔ 深入参考

- 完整研究流程与命令 → `read_skill(id="evasion-research", path="references/research-workflow.md")`

---

## 5 步研究流程

```
1. GitHub 搜索 → gh search repos / gh search code
2. 仓库分析 → gh repo view + 读关键文件
3. 模式提取 → 按 6 大类分类
4. 去重检查 → 查已有知识库避免重复
5. 入库保存 → 写入 evasion-techniques-db.json / loader-components-db.json
```

## GitHub 搜索命令速查

```bash
# 搜仓库
gh search repos "shellcode loader language:C stars:>20" --limit 20
gh search repos "AMSI bypass" --limit 15
gh search repos "syscall direct" --language c --limit 15

# 搜代码
gh search code "VirtualAlloc PAGE_EXECUTE_READWRITE" --language c --limit 30
gh search code "NtCreateThreadEx" --language c --limit 20
```

## 6 大技术分类

| 类别 | 搜索关键词 |
|------|-----------|
| 内存分配 | VirtualAlloc, HeapCreate, NtAllocateVirtualMemory, MappedFile |
| 代码执行 | CreateThread, EnumWindows, APC, Fiber, callback |
| API 混淆 | API hashing, PEB walk, dynamic resolve |
| 字符串混淆 | XOR, AES, stack strings, compile-time encryption |
| 反分析 | IsDebuggerPresent, anti-VM, sandbox detection |
| Syscall | direct syscall, indirect syscall, SSN, Hell's Gate |

## 去重规则

| 条件 | 操作 |
|------|------|
| 完全同名 | ❌ 跳过（重复） |
| 同技术不同名 | ❌ 跳过（重复） |
| 同目标不同实现 | ✅ 添加（都有价值） |
| 不同目标类似 API | ✅ 添加（不同用途） |

## 输出格式

```markdown
## 研究报告

### 发现的技术
1. [技术名] - [简述] - 复杂度: simple/medium/complex

### 知识库状态
- 新增: X 条
- 重复跳过: Y 条
- 变体补充: Z 条

### 参考链接
- https://github.com/...
```
