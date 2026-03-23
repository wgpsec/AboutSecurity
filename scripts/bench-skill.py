#!/usr/bin/env python3
"""
bench-skill.py — Skill quality benchmark runner for AboutSecurity Skills.

Runs eval scenarios with_skill (skill content injected) and without_skill (baseline),
using `claude -p` or any compatible CLI agent as the executor.

Usage:
    # Benchmark a single skill
    python scripts/bench-skill.py --skill Skills/exploit/sql-injection-methodology

    # Benchmark with 3 runs per config (for variance analysis)
    python scripts/bench-skill.py --skill Skills/exploit/sql-injection-methodology --runs 3

    # Use a specific model
    python scripts/bench-skill.py --skill Skills/exploit/idor-methodology --model claude-sonnet-4-20250514

    # Benchmark all skills that have evals
    python scripts/bench-skill.py --all

    # Grade only (skip running, just grade existing outputs)
    python scripts/bench-skill.py --skill Skills/exploit/sql-injection-methodology --grade-only

    # Custom executor (instead of claude -p)
    python scripts/bench-skill.py --skill Skills/exploit/ssti-detect --executor "kitsune agent"

Output:
    Creates workspace at benchmarks/<skill-name>/<timestamp>/
    with grading.json, benchmark.json, and benchmark.md per iteration.

    Use skill-creator's generate_review.py for browser-based review.
"""

import argparse
import json
import math
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO_ROOT / "Skills"


def parse_skill_md(skill_path: Path) -> tuple[str, str, str]:
    """Parse a SKILL.md file, returning (name, description, body_content)."""
    content = (skill_path / "SKILL.md").read_text(encoding="utf-8")
    lines = content.split("\n")

    if lines[0].strip() != "---":
        raise ValueError(f"SKILL.md missing frontmatter: {skill_path}")

    end_idx = None
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end_idx = i
            break

    if end_idx is None:
        raise ValueError(f"SKILL.md missing closing ---: {skill_path}")

    name = ""
    description = ""
    for line in lines[1:end_idx]:
        if line.startswith("name:"):
            name = line[len("name:"):].strip().strip('"').strip("'")
        elif line.startswith("description:"):
            description = line[len("description:"):].strip().strip('"').strip("'")

    body = "\n".join(lines[end_idx + 1:]).strip()
    return name, description, body


def load_evals(skill_path: Path) -> dict:
    """Load evals/evals.json from skill directory."""
    evals_file = skill_path / "evals" / "evals.json"
    if not evals_file.exists():
        raise FileNotFoundError(f"No evals found: {evals_file}")
    return json.loads(evals_file.read_text(encoding="utf-8"))


def run_with_claude(prompt: str, timeout: int = 120, model: str = None) -> dict:
    """Run a prompt via `claude -p` and capture output + metrics."""
    cmd = ["claude", "-p", prompt, "--output-format", "json"]
    if model:
        cmd.extend(["--model", model])

    env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}

    start = time.time()
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout,
            cwd=str(REPO_ROOT), env=env,
        )
        duration = time.time() - start

        try:
            output_data = json.loads(result.stdout)
            output_text = output_data.get("result", result.stdout)
            tokens = output_data.get("total_tokens", 0)
        except (json.JSONDecodeError, TypeError):
            output_text = result.stdout
            tokens = 0

        return {
            "output": output_text,
            "tokens": tokens,
            "duration_seconds": round(duration, 1),
            "exit_code": result.returncode,
            "error": result.stderr[:500] if result.returncode != 0 else "",
        }
    except subprocess.TimeoutExpired:
        return {
            "output": "",
            "tokens": 0,
            "duration_seconds": timeout,
            "exit_code": -1,
            "error": "timeout",
        }
    except FileNotFoundError:
        return {
            "output": "",
            "tokens": 0,
            "duration_seconds": 0,
            "exit_code": -2,
            "error": "claude CLI not found. Install: https://docs.anthropic.com/en/docs/claude-cli",
        }


def run_with_kitsune(prompt: str, timeout: int = 120, **kwargs) -> dict:
    """Run a prompt via kitsune agent (placeholder for custom executor)."""
    # Users can extend this for kitsune or other agents
    raise NotImplementedError("Kitsune executor not yet implemented. Use --executor claude")


def build_with_skill_prompt(eval_prompt: str, skill_body: str, skill_name: str) -> str:
    """Build prompt with skill content injected."""
    return f"""你是一个 AI 安全测试 Agent。你有以下安全测试方法论可以参考：

<skill name="{skill_name}">
{skill_body}
</skill>

请根据以上方法论回答以下问题。你的回答应该体现系统化的方法论，而不是随机尝试。

{eval_prompt}"""


def build_without_skill_prompt(eval_prompt: str) -> str:
    """Build baseline prompt without skill content."""
    return f"""你是一个 AI 安全测试 Agent。

请回答以下问题。你的回答应该体现系统化的方法论。

{eval_prompt}"""


def grade_output(output: str, expectations: list[str]) -> dict:
    """
    Grade an output against expectations using keyword/pattern matching.

    For more sophisticated grading, use grade_eval.py with an LLM grader.
    This is a fast heuristic that checks if expectation keywords appear in the output.
    """
    results = []
    for expectation in expectations:
        # Extract key phrases from expectation for matching
        # Simple heuristic: check if the core terms appear in output
        passed = check_expectation(output, expectation)
        results.append({
            "text": expectation,
            "passed": passed,
            "evidence": f"{'Found' if passed else 'Not found'} in output ({len(output)} chars)",
        })

    passed_count = sum(1 for r in results if r["passed"])
    total = len(results)
    return {
        "expectations": results,
        "summary": {
            "passed": passed_count,
            "failed": total - passed_count,
            "total": total,
            "pass_rate": round(passed_count / total, 4) if total > 0 else 0.0,
        }
    }


def check_expectation(output: str, expectation: str) -> bool:
    """
    Check if an expectation is met in the output.

    Supports two formats:
    1. Free-text expectation: "提到了 UNION SELECT 注入"
       → checks if key terms ("UNION", "SELECT") appear in output
    2. Keyword list (pipe-separated): "UNION|union select|联合查询"
       → checks if any keyword appears

    Override with LLM grading for subjective expectations.
    """
    output_lower = output.lower()

    # If expectation contains | separator, treat as keyword alternatives
    if "|" in expectation:
        keywords = [k.strip().lower() for k in expectation.split("|")]
        return any(kw in output_lower for kw in keywords if kw)

    # Extract meaningful terms (>= 2 chars, skip common words)
    skip_words = {"的", "了", "是", "在", "有", "和", "或", "与", "到", "从", "对", "把", "被",
                  "the", "a", "an", "is", "are", "was", "were", "in", "on", "at", "to", "for",
                  "提到", "使用", "包含", "应该", "需要", "方法", "策略"}
    terms = []
    for word in expectation.split():
        word_clean = word.strip("（）()\"'`，。、；：")
        if len(word_clean) >= 2 and word_clean.lower() not in skip_words:
            terms.append(word_clean.lower())

    if not terms:
        return False

    # Require at least 60% of terms to match
    matched = sum(1 for t in terms if t in output_lower)
    return matched >= max(1, len(terms) * 0.6)


def calculate_stats(values: list[float]) -> dict:
    """Calculate mean, stddev, min, max."""
    if not values:
        return {"mean": 0.0, "stddev": 0.0, "min": 0.0, "max": 0.0}
    n = len(values)
    mean = sum(values) / n
    stddev = math.sqrt(sum((x - mean) ** 2 for x in values) / (n - 1)) if n > 1 else 0.0
    return {
        "mean": round(mean, 4),
        "stddev": round(stddev, 4),
        "min": round(min(values), 4),
        "max": round(max(values), 4),
    }


def generate_benchmark_json(
    skill_name: str,
    skill_path: str,
    all_runs: list[dict],
    model: str,
) -> dict:
    """Generate benchmark.json from collected run data."""
    configs = {}
    for run in all_runs:
        config = run["configuration"]
        if config not in configs:
            configs[config] = []
        configs[config].append(run)

    # Calculate summary stats per config
    run_summary = {}
    for config, runs in configs.items():
        pass_rates = [r["result"]["pass_rate"] for r in runs]
        times = [r["result"]["time_seconds"] for r in runs]
        tokens = [r["result"]["tokens"] for r in runs]
        run_summary[config] = {
            "pass_rate": calculate_stats(pass_rates),
            "time_seconds": calculate_stats(times),
            "tokens": calculate_stats(tokens),
        }

    # Delta between with_skill and without_skill
    config_names = list(configs.keys())
    if len(config_names) >= 2:
        ws = run_summary.get("with_skill", run_summary.get(config_names[0], {}))
        wos = run_summary.get("without_skill", run_summary.get(config_names[1], {}))
        delta_pr = ws.get("pass_rate", {}).get("mean", 0) - wos.get("pass_rate", {}).get("mean", 0)
        delta_time = ws.get("time_seconds", {}).get("mean", 0) - wos.get("time_seconds", {}).get("mean", 0)
        delta_tokens = ws.get("tokens", {}).get("mean", 0) - wos.get("tokens", {}).get("mean", 0)
        run_summary["delta"] = {
            "pass_rate": f"{delta_pr:+.2f}",
            "time_seconds": f"{delta_time:+.1f}",
            "tokens": f"{delta_tokens:+.0f}",
        }

    eval_ids = sorted(set(r["eval_id"] for r in all_runs))

    return {
        "metadata": {
            "skill_name": skill_name,
            "skill_path": skill_path,
            "executor_model": model or "default",
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "evals_run": eval_ids,
            "runs_per_configuration": max(r["run_number"] for r in all_runs) if all_runs else 1,
        },
        "runs": all_runs,
        "run_summary": run_summary,
        "notes": [],
    }


def generate_markdown(benchmark: dict) -> str:
    """Generate human-readable benchmark.md."""
    meta = benchmark["metadata"]
    summary = benchmark["run_summary"]
    configs = [k for k in summary if k != "delta"]
    delta = summary.get("delta", {})

    lines = [
        f"# Skill Benchmark: {meta['skill_name']}",
        "",
        f"**Model**: {meta['executor_model']}",
        f"**Date**: {meta['timestamp']}",
        f"**Evals**: {len(meta['evals_run'])} scenarios × {meta['runs_per_configuration']} runs/config",
        "",
        "## Summary",
        "",
    ]

    # Header
    header = "| Metric |"
    separator = "|--------|"
    for c in configs:
        label = c.replace("_", " ").title()
        header += f" {label} |"
        separator += "------------|"
    header += " Delta |"
    separator += "-------|"
    lines.extend([header, separator])

    # Rows
    for metric, fmt_val, fmt_delta in [
        ("pass_rate", lambda s: f"{s.get('mean',0)*100:.0f}% ± {s.get('stddev',0)*100:.0f}%", lambda d: d),
        ("time_seconds", lambda s: f"{s.get('mean',0):.1f}s ± {s.get('stddev',0):.1f}s", lambda d: f"{d}s"),
        ("tokens", lambda s: f"{s.get('mean',0):.0f} ± {s.get('stddev',0):.0f}", lambda d: d),
    ]:
        row = f"| {metric.replace('_',' ').title()} |"
        for c in configs:
            row += f" {fmt_val(summary.get(c, {}).get(metric, {}))} |"
        row += f" {fmt_delta(delta.get(metric, '—'))} |"
        lines.append(row)

    # Per-eval breakdown
    lines.extend(["", "## Per-Eval Breakdown", ""])
    eval_ids = sorted(set(r["eval_id"] for r in benchmark["runs"]))
    for eval_id in eval_ids:
        eval_runs = [r for r in benchmark["runs"] if r["eval_id"] == eval_id]
        eval_name = eval_runs[0].get("eval_name", f"eval-{eval_id}") if eval_runs else f"eval-{eval_id}"
        lines.append(f"### {eval_name}")
        for config in configs:
            config_runs = [r for r in eval_runs if r["configuration"] == config]
            if config_runs:
                prs = [r["result"]["pass_rate"] for r in config_runs]
                avg_pr = sum(prs) / len(prs) if prs else 0
                lines.append(f"- **{config.replace('_',' ').title()}**: {avg_pr*100:.0f}% pass rate ({len(config_runs)} runs)")
        lines.append("")

    # Notes
    if benchmark.get("notes"):
        lines.extend(["## Notes", ""])
        for note in benchmark["notes"]:
            lines.append(f"- {note}")

    return "\n".join(lines)


def run_skill_benchmark(
    skill_path: Path,
    runs_per_config: int = 1,
    model: str = None,
    timeout: int = 120,
    grade_only: bool = False,
    verbose: bool = True,
) -> Path:
    """Run full benchmark for a skill. Returns workspace path."""
    name, description, body = parse_skill_md(skill_path)
    evals_data = load_evals(skill_path)
    evals = evals_data.get("evals", [])

    if not evals:
        raise ValueError(f"No evals defined in {skill_path / 'evals' / 'evals.json'}")

    # Create workspace
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    workspace = REPO_ROOT / "benchmarks" / name / f"iteration-{timestamp}"
    workspace.mkdir(parents=True, exist_ok=True)

    if verbose:
        print(f"🎯 Benchmarking: {name}")
        print(f"📂 Workspace: {workspace}")
        print(f"📋 Evals: {len(evals)} scenarios × {runs_per_config} runs × 2 configs")
        print()

    all_runs = []

    for eval_item in evals:
        eval_id = eval_item["id"]
        eval_prompt = eval_item["prompt"]
        eval_name = eval_item.get("name", f"eval-{eval_id}")
        expectations = eval_item.get("expectations", [])

        if verbose:
            print(f"━━━ Eval {eval_id}: {eval_name} ━━━")

        for config in ["with_skill", "without_skill"]:
            for run_num in range(1, runs_per_config + 1):
                run_dir = workspace / eval_name / config / f"run-{run_num}"
                run_dir.mkdir(parents=True, exist_ok=True)

                if grade_only:
                    # Load existing output
                    output_file = run_dir / "output.txt"
                    if not output_file.exists():
                        if verbose:
                            print(f"  ⏭ {config} run-{run_num}: no output file, skipping")
                        continue
                    output_text = output_file.read_text(encoding="utf-8")
                    run_result = {"output": output_text, "tokens": 0, "duration_seconds": 0}
                else:
                    # Build prompt
                    if config == "with_skill":
                        prompt = build_with_skill_prompt(eval_prompt, body, name)
                    else:
                        prompt = build_without_skill_prompt(eval_prompt)

                    if verbose:
                        print(f"  ▸ {config} run-{run_num}...", end=" ", flush=True)

                    run_result = run_with_claude(prompt, timeout=timeout, model=model)

                    if verbose:
                        status = "✓" if run_result["exit_code"] == 0 else "✗"
                        print(f"{status} ({run_result['duration_seconds']}s, {run_result['tokens']} tokens)")

                    # Save output
                    (run_dir / "output.txt").write_text(
                        run_result["output"], encoding="utf-8"
                    )
                    (run_dir / "timing.json").write_text(json.dumps({
                        "total_tokens": run_result["tokens"],
                        "duration_ms": int(run_result["duration_seconds"] * 1000),
                        "total_duration_seconds": run_result["duration_seconds"],
                    }, indent=2), encoding="utf-8")

                    if run_result.get("error"):
                        (run_dir / "error.txt").write_text(
                            run_result["error"], encoding="utf-8"
                        )

                # Grade
                grading = grade_output(run_result.get("output", ""), expectations)
                grading["timing"] = {
                    "total_duration_seconds": run_result.get("duration_seconds", 0),
                }
                (run_dir / "grading.json").write_text(
                    json.dumps(grading, indent=2, ensure_ascii=False), encoding="utf-8"
                )

                # Build run record for benchmark.json
                run_record = {
                    "eval_id": eval_id,
                    "eval_name": eval_name,
                    "configuration": config,
                    "run_number": run_num,
                    "result": {
                        "pass_rate": grading["summary"]["pass_rate"],
                        "passed": grading["summary"]["passed"],
                        "failed": grading["summary"]["failed"],
                        "total": grading["summary"]["total"],
                        "time_seconds": run_result.get("duration_seconds", 0),
                        "tokens": run_result.get("tokens", 0),
                        "tool_calls": 0,
                        "errors": 1 if run_result.get("error") else 0,
                    },
                    "expectations": grading["expectations"],
                    "notes": [],
                }
                all_runs.append(run_record)

    # Generate benchmark.json and benchmark.md
    benchmark = generate_benchmark_json(
        skill_name=name,
        skill_path=str(skill_path.relative_to(REPO_ROOT)),
        all_runs=all_runs,
        model=model or "default",
    )

    benchmark_json_path = workspace / "benchmark.json"
    benchmark_json_path.write_text(
        json.dumps(benchmark, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    benchmark_md_path = workspace / "benchmark.md"
    benchmark_md_path.write_text(
        generate_markdown(benchmark), encoding="utf-8"
    )

    if verbose:
        print()
        print(f"📊 Results:")
        summary = benchmark["run_summary"]
        for config in [k for k in summary if k != "delta"]:
            pr = summary[config]["pass_rate"]
            label = config.replace("_", " ").title()
            print(f"  {label}: {pr['mean']*100:.0f}% ± {pr['stddev']*100:.0f}% pass rate")
        delta = summary.get("delta", {})
        if delta:
            print(f"  Delta: {delta.get('pass_rate', '—')} pass rate")
        print()
        print(f"  benchmark.json: {benchmark_json_path}")
        print(f"  benchmark.md:   {benchmark_md_path}")

    return workspace


def find_skills_with_evals() -> list[Path]:
    """Find all skill directories that have evals/evals.json."""
    skills = []
    for evals_json in SKILLS_DIR.rglob("evals/evals.json"):
        skill_dir = evals_json.parent.parent
        if (skill_dir / "SKILL.md").exists():
            skills.append(skill_dir)
    return sorted(skills)


def main():
    parser = argparse.ArgumentParser(
        description="Benchmark skill quality with A/B testing (with_skill vs baseline)"
    )
    parser.add_argument(
        "--skill", type=Path,
        help="Path to skill directory (relative to repo root or absolute)"
    )
    parser.add_argument("--all", action="store_true", help="Benchmark all skills with evals")
    parser.add_argument("--runs", type=int, default=1, help="Runs per configuration (default: 1)")
    parser.add_argument("--model", default=None, help="Model for claude -p")
    parser.add_argument("--timeout", type=int, default=120, help="Timeout per run in seconds")
    parser.add_argument("--grade-only", action="store_true", help="Skip running, just re-grade")
    parser.add_argument("--quiet", action="store_true", help="Minimal output")

    args = parser.parse_args()

    if args.all:
        skills = find_skills_with_evals()
        if not skills:
            print("No skills with evals/ found. Create evals/evals.json in a skill directory first.")
            sys.exit(1)
        print(f"Found {len(skills)} skills with evals:")
        for s in skills:
            print(f"  {s.relative_to(REPO_ROOT)}")
        print()
        for skill_path in skills:
            try:
                run_skill_benchmark(
                    skill_path,
                    runs_per_config=args.runs,
                    model=args.model,
                    timeout=args.timeout,
                    grade_only=args.grade_only,
                    verbose=not args.quiet,
                )
            except Exception as e:
                print(f"❌ {skill_path.name}: {e}")
                continue

    elif args.skill:
        skill_path = args.skill
        if not skill_path.is_absolute():
            skill_path = REPO_ROOT / skill_path
        if not (skill_path / "SKILL.md").exists():
            print(f"Error: No SKILL.md in {skill_path}")
            sys.exit(1)
        if not (skill_path / "evals" / "evals.json").exists():
            print(f"Error: No evals/evals.json in {skill_path}")
            print("Create eval scenarios first. See CONTRIBUTING.md for format.")
            sys.exit(1)

        run_skill_benchmark(
            skill_path,
            runs_per_config=args.runs,
            model=args.model,
            timeout=args.timeout,
            grade_only=args.grade_only,
            verbose=not args.quiet,
        )

    else:
        parser.print_help()
        print("\nExamples:")
        print("  python scripts/bench-skill.py --skill Skills/exploit/sql-injection-methodology")
        print("  python scripts/bench-skill.py --all --runs 3")
        sys.exit(1)


if __name__ == "__main__":
    main()
