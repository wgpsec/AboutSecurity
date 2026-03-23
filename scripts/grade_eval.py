#!/usr/bin/env python3
"""
grade_eval.py — LLM-based grader for skill benchmark outputs.

Uses `claude -p` to evaluate outputs against expectations with
evidence-based reasoning. More accurate than keyword matching
for subjective or complex assertions.

Usage:
    # Grade a single run
    python scripts/grade_eval.py --run-dir benchmarks/sql-injection-methodology/iteration-1/sqli-basic/with_skill/run-1

    # Grade all runs in a workspace
    python scripts/grade_eval.py --workspace benchmarks/sql-injection-methodology/iteration-1

    # Override grading model
    python scripts/grade_eval.py --workspace benchmarks/sql-injection-methodology/iteration-1 --model claude-haiku-4-20250514
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def grade_with_llm(
    output_text: str,
    expectations: list[dict],
    model: str = None,
    timeout: int = 60,
) -> dict:
    """Grade output against expectations using an LLM."""

    expectations_text = "\n".join(
        f"{i+1}. {exp['text']}" for i, exp in enumerate(expectations)
    )

    prompt = f"""你是一个评估器。请评估以下 AI Agent 输出是否满足给定的期望。

## 待评估的输出

<output>
{output_text[:8000]}
</output>

## 期望列表

{expectations_text}

## 评估要求

对每个期望，判断输出是否满足它。回复严格的 JSON 格式（不要 markdown 代码块）：

{{
  "expectations": [
    {{"text": "期望1的原文", "passed": true/false, "evidence": "在输出中找到的证据或未找到的原因"}}
  ],
  "summary": {{
    "passed": 通过数量,
    "failed": 未通过数量,
    "total": 总数,
    "pass_rate": 通过率(0-1)
  }}
}}"""

    cmd = ["claude", "-p", prompt, "--output-format", "json"]
    if model:
        cmd.extend(["--model", model])

    env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout,
            cwd=str(REPO_ROOT), env=env,
        )

        # Parse the output
        try:
            output_data = json.loads(result.stdout)
            grading_text = output_data.get("result", result.stdout)
        except (json.JSONDecodeError, TypeError):
            grading_text = result.stdout

        # Extract JSON from the grading text
        grading = extract_json(grading_text)
        if grading and "expectations" in grading:
            return grading

    except subprocess.TimeoutExpired:
        pass
    except FileNotFoundError:
        print("Warning: claude CLI not found. Falling back to keyword grading.", file=sys.stderr)

    # Fallback: return the expectations as-is (not graded)
    return {
        "expectations": expectations,
        "summary": {
            "passed": 0,
            "failed": len(expectations),
            "total": len(expectations),
            "pass_rate": 0.0,
        },
        "grading_error": "LLM grading failed, results are from fallback",
    }


def extract_json(text: str) -> dict | None:
    """Extract JSON object from text that may contain surrounding content."""
    # Try direct parse
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        pass

    # Try to find JSON in the text
    if not text:
        return None

    # Find first { and last }
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        try:
            return json.loads(text[start:end + 1])
        except json.JSONDecodeError:
            pass

    return None


def grade_run_dir(run_dir: Path, evals_data: dict, model: str = None) -> dict:
    """Grade a single run directory."""
    output_file = run_dir / "output.txt"
    if not output_file.exists():
        return {"error": f"No output.txt in {run_dir}"}

    output_text = output_file.read_text(encoding="utf-8")

    # Find corresponding eval expectations
    grading_file = run_dir / "grading.json"
    if grading_file.exists():
        existing = json.loads(grading_file.read_text(encoding="utf-8"))
        expectations = existing.get("expectations", [])
    else:
        expectations = []

    if not expectations:
        return {"error": "No expectations to grade against"}

    # Grade with LLM
    grading = grade_with_llm(output_text, expectations, model=model)

    # Preserve timing from existing grading
    if grading_file.exists():
        existing = json.loads(grading_file.read_text(encoding="utf-8"))
        grading["timing"] = existing.get("timing", {})

    # Save updated grading
    grading_file.write_text(
        json.dumps(grading, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    return grading


def grade_workspace(workspace: Path, evals_data: dict = None, model: str = None):
    """Grade all runs in a workspace directory."""
    run_dirs = sorted(workspace.rglob("run-*/"))

    if not run_dirs:
        print(f"No run directories found in {workspace}")
        return

    print(f"Grading {len(run_dirs)} runs in {workspace}")

    for run_dir in run_dirs:
        if not (run_dir / "output.txt").exists():
            continue

        rel = run_dir.relative_to(workspace)
        print(f"  ▸ {rel}...", end=" ", flush=True)

        grading = grade_run_dir(run_dir, evals_data, model=model)

        if "error" in grading:
            print(f"⚠ {grading['error']}")
        else:
            summary = grading.get("summary", {})
            print(f"✓ {summary.get('passed', 0)}/{summary.get('total', 0)} passed")


def main():
    parser = argparse.ArgumentParser(description="LLM-based grader for skill benchmarks")
    parser.add_argument("--run-dir", type=Path, help="Grade a single run directory")
    parser.add_argument("--workspace", type=Path, help="Grade all runs in workspace")
    parser.add_argument("--model", default=None, help="Model for grading")

    args = parser.parse_args()

    if args.run_dir:
        if not args.run_dir.exists():
            print(f"Not found: {args.run_dir}")
            sys.exit(1)
        grading = grade_run_dir(args.run_dir, {}, model=args.model)
        print(json.dumps(grading, indent=2, ensure_ascii=False))

    elif args.workspace:
        if not args.workspace.exists():
            print(f"Not found: {args.workspace}")
            sys.exit(1)
        grade_workspace(args.workspace, model=args.model)

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
