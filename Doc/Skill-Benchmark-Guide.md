# Skill 质量基准测试指南

本项目提供两套互补的 Skill 测试工具：

| 维度 | 工具 | 问题 | 位置 |
|------|------|------|------|
| **触发率** | skill-creator 脚本 | description 写得好不好？Agent 会不会主动读取这个 Skill？ | `.github/skills/skill-creator/scripts/` |
| **内容质量** | bench-skill 脚本 | Skill 内容有没有用？读了之后回答质量是否真的提升？ | `scripts/` |

两者可以独立使用，也可以串联使用（先优化触发率，再验证内容质量）。

---

## 前置要求

```bash
# 必须：Claude CLI（两套工具都依赖它）
# 安装：https://docs.anthropic.com/en/docs/claude-cli
claude --version

# 可选：PyYAML（仅 quick_validate.py 需要）
pip install pyyaml
```

确认你在项目根目录：

```bash
cd /path/to/AboutSecurity
```

---

## 第一部分：触发率测试（Skill Description 优化）

> 测试目标：**Agent 是否会在正确的场景触发读取你的 Skill**
>
> 工具来源：`.github/skills/skill-creator/scripts/`

### 1.1 原理

Claude Code 的 skill 触发机制：Agent 看到用户 query → 匹配 skill description → 决定是否 read_skill。如果 description 不够 "pushy"，Agent 可能在该用的时候不触发。

触发率测试会：
1. 把你的 Skill 注册为 Claude Code command
2. 发送一组 query（应触发 + 不应触发）
3. 检测 Agent 是否读取了你的 Skill
4. 统计触发率

### 1.2 编写触发率测试集

创建 `trigger-eval.json`（放在你的 Skill 目录下或任意位置）：

```json
[
  {
    "query": "这个网站有 SQL 注入漏洞，帮我利用一下",
    "should_trigger": true
  },
  {
    "query": "我发现一个 UNION SELECT 注入点，但被 WAF 拦截了",
    "should_trigger": true
  },
  {
    "query": "帮我搜索一下这个域名的子域名",
    "should_trigger": false
  },
  {
    "query": "帮我写一个 Python 脚本",
    "should_trigger": false
  }
]
```

**规则：**
- `should_trigger: true` — 这个 query 应该让 Agent 读取你的 Skill
- `should_trigger: false` — 这个 query 不应该触发（负样本）
- 负样本不要太离谱（"写个斐波那契"对 SQL 注入 Skill 来说太简单了，不考验区分能力）
- 建议至少 6 条（3 正 3 负）

### 1.3 运行触发率测试

```bash
# 基本用法
python -m scripts.run_eval \
  --eval-set Skills/exploit/sql-injection-methodology/trigger-eval.json \
  --skill-path Skills/exploit/sql-injection-methodology \
  --verbose

# 每条 query 跑 3 次（减少随机性）
python -m scripts.run_eval \
  --eval-set Skills/exploit/sql-injection-methodology/trigger-eval.json \
  --skill-path Skills/exploit/sql-injection-methodology \
  --runs-per-query 3 \
  --verbose

# 指定模型
python -m scripts.run_eval \
  --eval-set Skills/exploit/sql-injection-methodology/trigger-eval.json \
  --skill-path Skills/exploit/sql-injection-methodology \
  --model claude-sonnet-4-20250514 \
  --verbose

# 测试一个新的 description（不修改 SKILL.md）
python -m scripts.run_eval \
  --eval-set Skills/exploit/sql-injection-methodology/trigger-eval.json \
  --skill-path Skills/exploit/sql-injection-methodology \
  --description "新的 description 文本" \
  --verbose
```

> **注意：** 以上命令需要在 `.github/skills/skill-creator/` 目录下运行，或将该目录加入 PYTHONPATH。

**输出示例：**
```
Evaluating: SQL注入检测和利用...
Results: 5/6 passed
  [PASS] rate=3/3 expected=True:  这个网站有 SQL 注入漏洞...
  [PASS] rate=3/3 expected=True:  我发现一个 UNION SELECT 注入点...
  [PASS] rate=0/3 expected=False: 帮我搜索一下这个域名的子域名
  [FAIL] rate=2/3 expected=False: 帮我检查一下这个网站的安全性
```

### 1.4 自动优化 Description

如果触发率不理想，可以让 AI 自动优化 description：

```bash
# 步骤 1：先跑一次 eval，保存结果
python -m scripts.run_eval \
  --eval-set Skills/exploit/sql-injection-methodology/trigger-eval.json \
  --skill-path Skills/exploit/sql-injection-methodology \
  --runs-per-query 3 \
  --verbose > eval_results.json

# 步骤 2：基于结果自动生成改进版 description
python -m scripts.improve_description \
  --eval-results eval_results.json \
  --skill-path Skills/exploit/sql-injection-methodology \
  --model claude-sonnet-4-20250514 \
  --verbose
```

### 1.5 自动循环优化（run_loop）

全自动模式：反复 eval → improve → eval 直到全部通过：

```bash
python -m scripts.run_loop \
  --eval-set Skills/exploit/sql-injection-methodology/trigger-eval.json \
  --skill-path Skills/exploit/sql-injection-methodology \
  --model claude-sonnet-4-20250514 \
  --max-iterations 5 \
  --runs-per-query 3 \
  --holdout 0.4 \
  --verbose \
  --report auto
```

**参数说明：**
| 参数 | 含义 |
|------|------|
| `--max-iterations 5` | 最多优化 5 轮 |
| `--runs-per-query 3` | 每条 query 跑 3 次取平均 |
| `--holdout 0.4` | 40% 的 query 作为测试集（防过拟合） |
| `--report auto` | 自动打开 HTML 报告 |

### 1.6 辅助工具

```bash
# 格式校验（检查 SKILL.md frontmatter 是否合法）
python .github/skills/skill-creator/scripts/quick_validate.py \
  Skills/exploit/sql-injection-methodology

# 打包 Skill 为 .skill 文件
python .github/skills/skill-creator/scripts/package_skill.py \
  Skills/exploit/sql-injection-methodology
```

---

## 第二部分：内容质量测试（Skill A/B 对比）

> 测试目标：**Skill 的方法论内容是否真的提升了 Agent 的回答质量**
>
> 工具来源：`scripts/`

### 2.1 原理

A/B 对比测试：
- **with_skill**：把 SKILL.md 的方法论内容注入到 prompt 中，让 Agent 回答
- **without_skill**：不注入内容（baseline），让 Agent 仅凭自身知识回答
- 对比两组的 **断言通过率**、**耗时**、**token 用量**

如果 with_skill 的通过率显著高于 without_skill → 说明 Skill 内容确实有效。

### 2.2 编写内容质量测试集

在 Skill 目录下创建 `evals/evals.json`：

```json
{
  "skill_name": "sql-injection-methodology",
  "evals": [
    {
      "id": 1,
      "name": "sqli-detection-basic",
      "prompt": "你在测试一个 Web 应用。你发现 /search?q=test 接口可以搜索商品。请详细描述你如何系统性地测试这个接口是否存在 SQL 注入漏洞。",
      "expected_output": "系统化的 SQL 注入检测流程",
      "expectations": [
        "UNION SELECT|UNION 注入|联合查询",
        "时间盲注|SLEEP|BENCHMARK|time-based",
        "布尔盲注|Boolean|1=1",
        "报错注入|EXTRACTVALUE|UPDATEXML|error-based",
        "单引号|'|闭合测试"
      ]
    },
    {
      "id": 2,
      "name": "sqli-waf-bypass",
      "prompt": "你发现一个 SQL 注入点，但 UNION SELECT 被 WAF 拦截了（返回 403）。请详细描述你的绕过策略。",
      "expected_output": "多种 WAF 绕过技术",
      "expectations": [
        "大小写|UniOn SeLeCt|混合大小写",
        "注释|/**/|内联注释",
        "编码|URL编码|双重编码",
        "替代语法|时间盲注|盲注作为备选"
      ]
    }
  ]
}
```

**expectations 格式：**
- 用 `|` 分隔关键词替代项，满足任一即通过
- 例：`"UNION SELECT|联合查询"` → 输出包含 "UNION SELECT" **或** "联合查询" 即 PASS
- 编写好的 expectation 应该是 with_skill 容易通过、without_skill 不容易通过的（否则无法区分 Skill 的价值）

**已有 evals 的 Skills（可直接测试）：**
```
Skills/exploit/sql-injection-methodology/evals/evals.json  (4 evals)
Skills/exploit/idor-methodology/evals/evals.json           (3 evals)
Skills/exploit/ssti-detect/evals/evals.json                (3 evals)
```

### 2.3 运行内容质量测试

```bash
# 测试单个 Skill（默认 1 次运行）
python scripts/bench-skill.py \
  --skill Skills/exploit/sql-injection-methodology

# 多次运行（方差分析，推荐 3 次）
python scripts/bench-skill.py \
  --skill Skills/exploit/sql-injection-methodology \
  --runs 3

# 指定模型
python scripts/bench-skill.py \
  --skill Skills/exploit/sql-injection-methodology \
  --model claude-sonnet-4-20250514

# 测试所有有 evals 的 Skills
python scripts/bench-skill.py --all

# 仅重新评分（不重新运行，用于调整 expectations 后）
python scripts/bench-skill.py \
  --skill Skills/exploit/sql-injection-methodology \
  --grade-only
```

**输出示例：**
```
🎯 Benchmarking: sql-injection-methodology
📂 Workspace: benchmarks/sql-injection-methodology/iteration-20260323-143904
📋 Evals: 4 scenarios × 3 runs × 2 configs

━━━ Eval 1: sqli-detection-basic ━━━
  ▸ with_skill run-1... ✓ (18.2s, 3800 tokens)
  ▸ with_skill run-2... ✓ (15.7s, 3200 tokens)
  ▸ with_skill run-3... ✓ (17.1s, 3500 tokens)
  ▸ without_skill run-1... ✓ (12.3s, 2100 tokens)
  ▸ without_skill run-2... ✓ (11.8s, 1900 tokens)
  ▸ without_skill run-3... ✓ (13.0s, 2200 tokens)

📊 Results:
  With Skill: 85% ± 5% pass rate
  Without Skill: 40% ± 8% pass rate
  Delta: +0.45 pass rate

  benchmark.json: benchmarks/sql-injection-methodology/iteration-.../benchmark.json
  benchmark.md:   benchmarks/sql-injection-methodology/iteration-.../benchmark.md
```

### 2.4 使用 LLM 评分（更准确）

默认评分使用关键词匹配（快速但有限）。对于复杂断言，用 LLM 评分：

```bash
# 对某次运行结果使用 LLM 重新评分
python scripts/grade_eval.py \
  --workspace benchmarks/sql-injection-methodology/iteration-20260323-143904

# 指定评分模型（推荐用较便宜的模型）
python scripts/grade_eval.py \
  --workspace benchmarks/sql-injection-methodology/iteration-20260323-143904 \
  --model claude-haiku-4-20250514
```

### 2.5 使用 skill-creator 的浏览器查看器

bench-skill 的输出兼容 skill-creator 的 viewer：

```bash
# 启动浏览器查看器（需要在 skill-creator 目录下）
python .github/skills/skill-creator/eval-viewer/generate_review.py \
  benchmarks/sql-injection-methodology/iteration-20260323-143904 \
  --skill-name "sql-injection-methodology" \
  --benchmark benchmarks/sql-injection-methodology/iteration-20260323-143904/benchmark.json

# 无浏览器环境：生成静态 HTML
python .github/skills/skill-creator/eval-viewer/generate_review.py \
  benchmarks/sql-injection-methodology/iteration-20260323-143904 \
  --skill-name "sql-injection-methodology" \
  --benchmark benchmarks/sql-injection-methodology/iteration-20260323-143904/benchmark.json \
  --static report.html
```

浏览器中会看到两个标签页：
- **Outputs** — 逐个查看每个场景的输出，可以留反馈
- **Benchmark** — 量化对比表（pass_rate, timing, tokens, delta）

### 2.6 输出文件说明

```
benchmarks/
└── sql-injection-methodology/
    └── iteration-20260323-143904/
        ├── benchmark.json          # 结构化统计数据
        ├── benchmark.md            # 人类可读的对比报告
        └── sqli-detection-basic/   # 每个 eval 场景
            ├── with_skill/
            │   ├── run-1/
            │   │   ├── output.txt      # Agent 的回答
            │   │   ├── grading.json    # 断言评估结果
            │   │   └── timing.json     # 耗时和 token
            │   ├── run-2/ ...
            │   └── run-3/ ...
            └── without_skill/
                ├── run-1/ ...
                ├── run-2/ ...
                └── run-3/ ...
```

---

## 第三部分：完整工作流（串联使用）

如果你想对一个 Skill 做完整的质量保证：

```
Step 1: 校验格式
   quick_validate.py → 确保 SKILL.md 格式合法

Step 2: 优化触发率
   run_eval.py → 测试当前触发率
   run_loop.py → 自动优化 description 直到触发率达标

Step 3: 验证内容质量
   bench-skill.py → A/B 测试 with_skill vs without_skill
   grade_eval.py → 用 LLM 精确评分

Step 4: 查看报告
   generate_review.py → 浏览器中查看结果，留反馈

Step 5: 迭代改进
   根据反馈修改 SKILL.md → 回到 Step 2
```

**命令速查：**

```bash
# 1. 校验
python .github/skills/skill-creator/scripts/quick_validate.py Skills/exploit/my-skill

# 2. 触发率测试
cd .github/skills/skill-creator
python -m scripts.run_eval \
  --eval-set ../../../Skills/exploit/my-skill/trigger-eval.json \
  --skill-path ../../../Skills/exploit/my-skill \
  --runs-per-query 3 --verbose
cd ../../..

# 3. 内容质量 A/B
python scripts/bench-skill.py --skill Skills/exploit/my-skill --runs 3

# 4. LLM 精确评分
python scripts/grade_eval.py --workspace benchmarks/my-skill/iteration-xxx

# 5. 浏览器查看
python .github/skills/skill-creator/eval-viewer/generate_review.py \
  benchmarks/my-skill/iteration-xxx \
  --skill-name my-skill \
  --benchmark benchmarks/my-skill/iteration-xxx/benchmark.json
```

---

## FAQ

**Q: 两套测试我都要跑吗？**
A: 看情况。如果你的 Skill 是给 Kitsune 用的（通过 `list_skills`/`read_skill` 手动触发），触发率测试不太重要，重点跑内容质量。如果是给 Claude Code 用的（自动触发），两个都跑。

**Q: 跑一次 bench-skill 要花多少钱？**
A: 取决于 eval 数量和 runs。每次 claude -p 调用大约 3000-5000 tokens。4 evals × 3 runs × 2 configs = 24 次调用 ≈ 72K-120K tokens。用 Sonnet 大约 $0.2-0.4。

**Q: 关键词匹配评分不准怎么办？**
A: 用 `grade_eval.py` 进行 LLM 评分。也可以调整 expectations 的关键词，用 `|` 增加更多同义词。

**Q: benchmark.json 的 delta 怎么解读？**
A: `delta.pass_rate: "+0.45"` 表示 Skill 让通过率提升了 45 个百分点。一般 > +0.20 说明 Skill 有明显效果，< +0.10 说明效果不大需要改进内容。

**Q: benchmarks/ 目录要提交到 Git 吗？**
A: 不用，已在 .gitignore 中排除。这是本地测试产物。
