---
name: c2-evasion-methodology
description: "C2框架免杀方法论：分析C2源码、搜索检测规则(YARA/Sigma/Snort)、逐规则分析、修改源码绕过检测。当需要C2免杀、YARA规则分析、Beacon/Implant源码修改时使用。"
metadata:
  tags: "c2,evasion,yara,sigma,beacon,implant,detection-bypass,免杀,source-modification"
  difficulty: "hard"
  icon: "🛡️"
  category: "免杀对抗"
---

# C2 框架免杀方法论

## 深入参考

以下参考资料**按需加载**，到达对应 Phase 时读取：

| Phase | 参考文档 | 用途 |
|-------|----------|------|
| 2 | `read_skill(id="c2-evasion-methodology", path="references/detection-search.md")` | YARA/Sigma/网络规则搜索命令 |
| 3 | `read_skill(id="c2-evasion-methodology", path="references/rule-analysis.md")` | 逐规则分析与免杀策略制定 |
| 3.5 | `read_skill(id="c2-evasion-methodology", path="references/hex-analysis.md")` | Hex 模式深度分析 |
| 3.6 | `read_skill(id="c2-evasion-methodology", path="references/binary-analysis.md")` | 二进制资产（shellcode/资源/配置）分析 |
| 3.7 | `read_skill(id="c2-evasion-methodology", path="references/string-search.md")` | 敏感字符串主动搜索 |
| 4 | `read_skill(id="c2-evasion-methodology", path="references/source-modify.md")` | 源码修改模式与编译器标志 |

---

## 6 步决策流程

```
Phase 1: 识别 C2 组件
├─ 找到 implant/beacon/agent 目录
└─ 识别语言（C/Go/Rust/Python）

Phase 2: 检测规则搜索 → ⛔必读 references/detection-search.md
├─ YARA 规则（VirusTotal/GitHub/Elastic/ESET）
├─ Sigma 规则（日志行为检测）
└─ 网络规则（Snort/Suricata/Zeek）

Phase 3: 逐规则分析 → ⛔必读 references/rule-analysis.md
├─ 解析每个 $s1/$a1/hex pattern
├─ 定位源码中产生该 pattern 的位置
├─ 制定免杀策略（优先级: 编译器标志 > 构建配置 > 源码修改 > 重构）
│
├─ Phase 3.5: Hex 分析 → references/hex-analysis.md
├─ Phase 3.6: 二进制资产 → references/binary-analysis.md
└─ Phase 3.7: 字符串搜索 → references/string-search.md

Phase 4: 靶向修改 → ⛔必读 references/source-modify.md
├─ ⛔ 编译器标志优先！（-O2, -fomit-frame-pointer, -fno-ident）
├─ 字符串混淆（XOR 加密）
├─ 函数重命名
└─ Makefile/构建链修改

Phase 5: 验证
└─ grep 确认所有检测 pattern 已消除

Phase 6: 文档
└─ 生成 modifications_summary.md
```

## 优先级框架

| 优先级 | 组件 | 动作 |
|--------|------|------|
| 1 (最高) | Implant/Beacon/Agent 二进制 | 必须修改 |
| 2 (高) | 网络特征暴露 | 必须修改 |
| 3 (跳过) | 内部字符串（不影响检测） | 可跳过 |

## 免杀策略决策矩阵

| Pattern 类型 | 编译器标志 | 源码修改 | 两者都需要 |
|-------------|-----------|---------|-----------|
| 函数序言（prologue） | ✅ 通常足够 | ✅ 备选 | 少见 |
| 字符串字节 | ❌ 无效 | ✅ 必须 | — |
| API 调用序列 | ⚠️ 可能有效 | ✅ 必须 | 有时 |
| 配置结构体 | ❌ 无效 | ✅ 必须 | — |

## 字符串混淆
- 混淆后必须验证：编译通过、功能正常、不影响运行
- 自动化处理：脚本批量替换，非手动逐个修改
