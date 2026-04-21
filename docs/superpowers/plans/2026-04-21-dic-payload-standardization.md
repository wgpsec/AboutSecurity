# Dic & Payload Standardization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Standardize Dic/ and Payload/ naming + add `_meta.yaml` metadata so AI search quality matches Skills.

**Architecture:** Python migration script handles batch rename via `git mv`. Per-directory `_meta.yaml` files provide structured metadata. `build_index.py` is updated to consume `_meta.yaml` when present, falling back to path-based indexing otherwise.

**Tech Stack:** Python 3, PyYAML, git, SQLite FTS5

**Repos:**
- AboutSecurity: `/Users/f0x/pte-project/public/AboutSecurity/` (data + migration script)
- context1337: `/Users/f0x/pte-project/public/context1337/` (build_index.py)

---

### Task 1: Create migration script — directory renames

**Files:**
- Create: `AboutSecurity/scripts/migrate.py`

- [ ] **Step 1: Create the migration script with directory rename logic**

```python
#!/usr/bin/env python3
"""Migrate Dic/ and Payload/ to standardized naming conventions.

Usage:
    python scripts/migrate.py rename-dirs [--dry-run]
    python scripts/migrate.py rename-files [--dry-run]
    python scripts/migrate.py gen-chinese-map
    python scripts/migrate.py gen-meta
"""
import argparse
import os
import re
import subprocess
import sys

import yaml

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Directory renames: processed depth-first (deepest first).
# Keys are relative to BASE. Order matters: parent renames come AFTER children.
DIR_RENAMES = [
    # --- Dic: deep subdirs first ---
    ("Dic/Auth/password/Complex", "Dic/auth/password/complex"),
    ("Dic/Auth/password/WPA", "Dic/auth/password/wpa"),
    ("Dic/Auth/password", "Dic/auth/password"),
    ("Dic/Auth/username/pingyin", "Dic/auth/username/pinyin"),
    ("Dic/Auth/username", "Dic/auth/username"),
    ("Dic/Auth", "Dic/auth"),
    ("Dic/Network", "Dic/network"),
    ("Dic/Port", "Dic/port"),
    ("Dic/Regular/Keyword", "Dic/regular/keyword"),
    ("Dic/Regular", "Dic/regular"),
    ("Dic/Web/api_param", "Dic/web/api-param"),
    ("Dic/Web/CMS", "Dic/web/cms"),
    ("Dic/Web/CTF", "Dic/web/ctf"),
    ("Dic/Web/Directory", "Dic/web/directory"),
    ("Dic/Web/Errors", "Dic/web/errors"),
    ("Dic/Web/File_Backup", "Dic/web/file-backup"),
    ("Dic/Web/Middleware/rabbitMQ", "Dic/web/middleware/rabbitmq"),
    ("Dic/Web/Middleware", "Dic/web/middleware"),
    ("Dic/Web/Service", "Dic/web/service"),
    ("Dic/Web/Upload", "Dic/web/upload"),
    ("Dic/Web/Webshell", "Dic/web/webshell"),
    ("Dic/Web", "Dic/web"),
    # --- Payload: deep subdirs first ---
    ("Payload/XSS/SVG", "Payload/xss/svg"),
    ("Payload/XSS", "Payload/xss"),
    ("Payload/403", "Payload/access-bypass"),
    ("Payload/ai", "Payload/prompt-injection"),
    ("Payload/CORS", "Payload/cors"),
    ("Payload/Format", "Payload/format"),
    ("Payload/HPP", "Payload/hpp"),
    ("Payload/LFI", "Payload/lfi"),
    ("Payload/RCE", "Payload/rce"),
    ("Payload/SQL-Inj", "Payload/sqli"),
    ("Payload/SSI", "Payload/ssi"),
    ("Payload/SSRF", "Payload/ssrf"),
    ("Payload/XXE", "Payload/xxe"),
]


def git_mv(old_abs, new_abs, dry_run=False):
    """Execute git mv, creating parent dirs if needed."""
    parent = os.path.dirname(new_abs)
    if not os.path.exists(parent):
        os.makedirs(parent, exist_ok=True)
    if dry_run:
        print(f"  [dry-run] git mv {os.path.relpath(old_abs, BASE)} -> {os.path.relpath(new_abs, BASE)}")
        return
    subprocess.run(["git", "mv", old_abs, new_abs], cwd=BASE, check=True)
    print(f"  git mv {os.path.relpath(old_abs, BASE)} -> {os.path.relpath(new_abs, BASE)}")


def cmd_rename_dirs(args):
    """Rename directories according to DIR_RENAMES."""
    print("=== Renaming directories ===")
    for old_rel, new_rel in DIR_RENAMES:
        old_abs = os.path.join(BASE, old_rel)
        new_abs = os.path.join(BASE, new_rel)
        if not os.path.isdir(old_abs):
            continue  # already renamed or doesn't exist
        if old_abs == new_abs:
            continue  # no change needed
        git_mv(old_abs, new_abs, dry_run=args.dry_run)
    print("Done. Run 'git status' to verify.")
```

- [ ] **Step 2: Run dry-run to verify directory renames**

```bash
cd /Users/f0x/pte-project/public/AboutSecurity
python scripts/migrate.py rename-dirs --dry-run
```

Expected: List of `git mv` operations printed, no actual changes.

- [ ] **Step 3: Execute directory renames**

```bash
cd /Users/f0x/pte-project/public/AboutSecurity
python scripts/migrate.py rename-dirs
```

- [ ] **Step 4: Verify and commit**

```bash
cd /Users/f0x/pte-project/public/AboutSecurity
git status
git add -A
git commit -m "refactor(dic,payload): standardize directory names to lowercase-hyphen"
```

---

### Task 2: Add file rename logic to migration script

**Files:**
- Modify: `AboutSecurity/scripts/migrate.py`

- [ ] **Step 1: Add file rename function**

Append to `scripts/migrate.py`:

```python
def is_chinese(text):
    """Check if text contains Chinese characters."""
    return bool(re.search(r'[\u4e00-\u9fff]', text))


def normalize_filename(name):
    """Apply rename rules: drop Fuzz_ prefix, lowercase, underscore->hyphen.

    Returns None for Chinese filenames (need manual mapping).
    """
    if is_chinese(name):
        return None  # needs manual translation

    base, ext = os.path.splitext(name)

    # Drop Fuzz_ prefix
    base = re.sub(r'^Fuzz_', '', base)
    # Drop Top prefix number pattern like Top100_ -> top100-
    base = re.sub(r'^Top(\d+)_', r'top\1-', base)
    # Lowercase
    base = base.lower()
    # Underscore to hyphen
    base = base.replace('_', '-')
    # Collapse multiple hyphens
    base = re.sub(r'-+', '-', base)
    # Strip leading/trailing hyphens
    base = base.strip('-')

    return base + ext.lower()


def cmd_rename_files(args):
    """Rename files in Dic/ and Payload/ using normalize rules."""
    print("=== Renaming files ===")
    chinese_files = []

    for top_dir in ["Dic", "Payload"]:
        abs_top = os.path.join(BASE, top_dir)
        if not os.path.isdir(abs_top):
            continue
        for root, dirs, files in os.walk(abs_top):
            for f in files:
                if f == '_meta.yaml' or f == '.gitkeep':
                    continue
                new_name = normalize_filename(f)
                if new_name is None:
                    chinese_files.append(os.path.relpath(os.path.join(root, f), BASE))
                    continue
                if new_name == f:
                    continue  # no change
                old_abs = os.path.join(root, f)
                new_abs = os.path.join(root, new_name)
                git_mv(old_abs, new_abs, dry_run=args.dry_run)

    if chinese_files:
        print(f"\n{len(chinese_files)} Chinese filenames need manual translation.")
        print("Run 'python scripts/migrate.py gen-chinese-map' to generate the mapping file.")


def cmd_gen_chinese_map(args):
    """Generate rename-map.yaml for Chinese-named files."""
    entries = []
    for top_dir in ["Dic", "Payload"]:
        abs_top = os.path.join(BASE, top_dir)
        if not os.path.isdir(abs_top):
            continue
        for root, dirs, files in os.walk(abs_top):
            for f in files:
                if is_chinese(f):
                    rel = os.path.relpath(os.path.join(root, f), BASE)
                    _, ext = os.path.splitext(f)
                    entries.append({
                        "old_path": rel,
                        "new_name": "",  # fill manually
                        "hint": f"Original: {f}"
                    })

    out_path = os.path.join(BASE, "scripts", "rename-map.yaml")
    with open(out_path, "w", encoding="utf-8") as fh:
        yaml.dump(entries, fh, allow_unicode=True, default_flow_style=False, sort_keys=False)
    print(f"Generated {out_path} with {len(entries)} entries. Fill in 'new_name' for each.")
```

- [ ] **Step 2: Run dry-run for file renames**

```bash
cd /Users/f0x/pte-project/public/AboutSecurity
python scripts/migrate.py rename-files --dry-run
```

Expected: List of file renames + count of Chinese filenames needing manual input.

- [ ] **Step 3: Execute file renames**

```bash
cd /Users/f0x/pte-project/public/AboutSecurity
python scripts/migrate.py rename-files
```

- [ ] **Step 4: Commit auto-renamed files**

```bash
cd /Users/f0x/pte-project/public/AboutSecurity
git add -A
git commit -m "refactor(dic,payload): standardize file names — drop Fuzz_ prefix, lowercase, hyphen-separated"
```

---

### Task 3: Handle Chinese filename translations

**Files:**
- Create: `AboutSecurity/scripts/rename-map.yaml` (generated, then manually edited)
- Modify: `AboutSecurity/scripts/migrate.py`

- [ ] **Step 1: Generate Chinese filename map**

```bash
cd /Users/f0x/pte-project/public/AboutSecurity
python scripts/migrate.py gen-chinese-map
```

- [ ] **Step 2: Fill in English names in `rename-map.yaml`**

The generated file will contain ~20 entries. Fill `new_name` for each:

```yaml
# Dic/auth/password/complex/ files
- old_path: Dic/auth/password/complex/符合四个条件的6位数密码.txt
  new_name: complex-6char-all-four-rules.txt
  hint: "Original: 符合四个条件的6位数密码.txt"

- old_path: Dic/auth/password/complex/符合四个条件的8位数密码.txt
  new_name: complex-8char-all-four-rules.txt

- old_path: Dic/auth/password/complex/复杂Top100.txt
  new_name: complex-top100.txt

- old_path: Dic/auth/password/complex/复杂Top1000.txt
  new_name: complex-top1000.txt

- old_path: Dic/auth/password/complex/复杂Top30.txt
  new_name: complex-top30.txt

- old_path: Dic/auth/password/complex/数字和字母同时存在的6位数密码.txt
  new_name: alphanum-6char.txt

- old_path: Dic/auth/password/complex/数字和字母同时存在的8位数密码.txt
  new_name: alphanum-8char.txt

- old_path: Dic/auth/password/complex/四个条件至少满足三个的6位数密码.txt
  new_name: complex-6char-three-of-four.txt

- old_path: Dic/auth/password/complex/四个条件至少满足三个的8位数密码.txt
  new_name: complex-8char-three-of-four.txt

- old_path: Dic/auth/password/complex/至少一个大写字母一个小写字母一个数字不能有三个相同的字符和特殊符号的6位数密码.txt
  new_name: complex-6char-upper-lower-digit-no-repeat.txt

- old_path: Dic/auth/password/complex/至少一个大写字母一个小写字母一个数字不能有三个相同的字符和特殊符号的8位数密码.txt
  new_name: complex-8char-upper-lower-digit-no-repeat.txt

- old_path: Dic/auth/password/complex/至少一个大写字母一个小写字母一个数字的6位数密码.txt
  new_name: complex-6char-upper-lower-digit.txt

- old_path: Dic/auth/password/complex/至少一个大写字母一个小写字母一个数字的8位数密码.txt
  new_name: complex-8char-upper-lower-digit.txt

- old_path: Dic/auth/password/complex/至少一个字母一个数字一个特殊符号的6位数密码.txt
  new_name: complex-6char-alpha-digit-special.txt

- old_path: Dic/auth/password/complex/至少一个字母一个数字一个特殊符号的8位数密码.txt
  new_name: complex-8char-alpha-digit-special.txt

# Dic/auth/username/pinyin/ files
- old_path: Dic/auth/username/pinyin/Source_姓.txt
  new_name: cn-surname.txt

- old_path: Dic/auth/username/pinyin/Source_名.txt
  new_name: cn-firstname.txt

# Dic/port/smtp/ files
- old_path: Dic/port/smtp/美国邮箱用户名.txt
  new_name: us-email-username.txt

- old_path: Dic/port/smtp/中国邮箱用户名.txt
  new_name: cn-email-username.txt

# Dic/port/ file
- old_path: Dic/port/端口列表.md
  new_name: port-list.md
```

- [ ] **Step 3: Add apply-chinese-map command to migrate.py**

Append to `scripts/migrate.py`:

```python
def cmd_apply_chinese_map(args):
    """Apply rename-map.yaml to rename Chinese-named files."""
    map_path = os.path.join(BASE, "scripts", "rename-map.yaml")
    if not os.path.exists(map_path):
        print("Error: scripts/rename-map.yaml not found. Run gen-chinese-map first.")
        sys.exit(1)

    with open(map_path, "r", encoding="utf-8") as fh:
        entries = yaml.safe_load(fh)

    for entry in entries:
        new_name = entry.get("new_name", "")
        if not new_name:
            print(f"  SKIP (no new_name): {entry['old_path']}")
            continue
        old_abs = os.path.join(BASE, entry["old_path"])
        if not os.path.exists(old_abs):
            print(f"  SKIP (not found): {entry['old_path']}")
            continue
        new_abs = os.path.join(os.path.dirname(old_abs), new_name)
        git_mv(old_abs, new_abs, dry_run=args.dry_run)
```

- [ ] **Step 4: Execute Chinese file renames**

```bash
cd /Users/f0x/pte-project/public/AboutSecurity
python scripts/migrate.py apply-chinese-map
```

- [ ] **Step 5: Commit**

```bash
cd /Users/f0x/pte-project/public/AboutSecurity
git add -A
git commit -m "refactor(dic,payload): translate Chinese filenames to English"
```

---

### Task 4: Clean up non-data files

**Files:**
- Move: `Dic/web/directory/加斜杠用.py` -> `scripts/add-trailing-slash.py`
- Move: `Dic/auth/username/pinyin/姓名转拼音.py` -> `scripts/name-to-pinyin.py`
- Move: `Payload/Burp/Proxifier_filter.txt` -> `Dic/web/http/proxifier-filter.txt` (or delete)

- [ ] **Step 1: Move utility scripts out of data directories**

```bash
cd /Users/f0x/pte-project/public/AboutSecurity
git mv "Dic/auth/username/pinyin/姓名转拼音.py" scripts/name-to-pinyin.py
git mv "Dic/web/directory/加斜杠用.py" scripts/add-trailing-slash.py
```

- [ ] **Step 2: Move Burp filter to Dic/web/http/**

```bash
cd /Users/f0x/pte-project/public/AboutSecurity
git mv Payload/Burp/Proxifier_filter.txt Dic/web/http/proxifier-filter.txt
# Remove empty Burp directory (git removes it automatically)
```

- [ ] **Step 3: Commit**

```bash
cd /Users/f0x/pte-project/public/AboutSecurity
git add -A
git commit -m "refactor: move utility scripts to scripts/, relocate Burp filter to dic/web/http"
```

---

### Task 5: Add argparse CLI to migration script

**Files:**
- Modify: `AboutSecurity/scripts/migrate.py`

- [ ] **Step 1: Add main() with subcommands**

Append to `scripts/migrate.py`:

```python
def main():
    parser = argparse.ArgumentParser(description="Dic/Payload migration tool")
    sub = parser.add_subparsers(dest="command")

    p1 = sub.add_parser("rename-dirs", help="Rename directories")
    p1.add_argument("--dry-run", action="store_true")

    p2 = sub.add_parser("rename-files", help="Rename files (auto rules)")
    p2.add_argument("--dry-run", action="store_true")

    p3 = sub.add_parser("gen-chinese-map", help="Generate rename-map.yaml for Chinese filenames")

    p4 = sub.add_parser("apply-chinese-map", help="Apply rename-map.yaml")
    p4.add_argument("--dry-run", action="store_true")

    p5 = sub.add_parser("gen-meta", help="Generate skeleton _meta.yaml files")

    args = parser.parse_args()

    commands = {
        "rename-dirs": cmd_rename_dirs,
        "rename-files": cmd_rename_files,
        "gen-chinese-map": cmd_gen_chinese_map,
        "apply-chinese-map": cmd_apply_chinese_map,
        "gen-meta": cmd_gen_meta,
    }

    if args.command in commands:
        commands[args.command](args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Verify CLI works**

```bash
cd /Users/f0x/pte-project/public/AboutSecurity
python scripts/migrate.py --help
python scripts/migrate.py rename-dirs --help
```

- [ ] **Step 3: Commit migration script**

```bash
cd /Users/f0x/pte-project/public/AboutSecurity
git add scripts/migrate.py
git commit -m "feat: add migration script for dic/payload standardization"
```

---

### Task 6: Generate skeleton `_meta.yaml` files

**Files:**
- Modify: `AboutSecurity/scripts/migrate.py` (add `cmd_gen_meta`)
- Create: ~40 `_meta.yaml` files across `Dic/` and `Payload/`

- [ ] **Step 1: Add gen-meta command to migrate.py**

Append before `main()`:

```python
def count_lines(path):
    """Count lines in a file."""
    try:
        with open(path, 'rb') as f:
            return sum(1 for _ in f)
    except Exception:
        return 0


def cmd_gen_meta(args):
    """Generate skeleton _meta.yaml for each directory containing data files."""
    print("=== Generating _meta.yaml skeletons ===")
    data_exts = {'.txt', '.md', '.json', '.html', '.xml', '.svg', '.pdf',
                 '.doc', '.xlsx', '.zip', '.png'}
    skip_files = {'_meta.yaml', '.gitkeep', '.DS_Store'}
    count = 0

    for top_dir in ["Dic", "Payload"]:
        abs_top = os.path.join(BASE, top_dir)
        if not os.path.isdir(abs_top):
            continue

        for root, dirs, files in os.walk(abs_top):
            # Filter to data files only
            data_files = [f for f in sorted(files)
                          if f not in skip_files
                          and os.path.splitext(f)[1].lower() in data_exts]
            if not data_files:
                continue

            meta_path = os.path.join(root, "_meta.yaml")
            if os.path.exists(meta_path):
                print(f"  SKIP (exists): {os.path.relpath(meta_path, BASE)}")
                continue

            # Derive category from path
            rel_root = os.path.relpath(root, abs_top)
            parts = rel_root.split(os.sep) if rel_root != "." else []
            category = parts[0] if parts else os.path.basename(root)
            subcategory = parts[1] if len(parts) > 1 else ""

            file_entries = []
            for f in data_files:
                fpath = os.path.join(root, f)
                lines = count_lines(fpath)
                file_entries.append({
                    "name": f,
                    "lines": lines,
                    "description": "",   # TODO: fill
                    "usage": "",         # TODO: fill
                    "tags": "",          # TODO: fill
                })

            meta = {
                "category": category,
                "description": "",       # TODO: fill
                "tags": "",              # TODO: fill
            }
            if subcategory:
                meta["subcategory"] = subcategory
            meta["files"] = file_entries

            with open(meta_path, "w", encoding="utf-8") as fh:
                yaml.dump(meta, fh, allow_unicode=True, default_flow_style=False, sort_keys=False)
            print(f"  Created: {os.path.relpath(meta_path, BASE)}")
            count += 1

    print(f"\nGenerated {count} _meta.yaml files. Fill in description/usage/tags for each.")
```

- [ ] **Step 2: Run gen-meta**

```bash
cd /Users/f0x/pte-project/public/AboutSecurity
python scripts/migrate.py gen-meta
```

Expected: ~40 `_meta.yaml` files created, each with `lines` auto-filled, `description`/`usage`/`tags` empty.

- [ ] **Step 3: Verify a generated file**

```bash
cat Dic/auth/password/_meta.yaml
```

Expected output like:
```yaml
category: auth
subcategory: password
description: ''
tags: ''
files:
- name: password-top100.txt
  lines: 100
  description: ''
  usage: ''
  tags: ''
- name: admin-common.txt
  lines: 57
  description: ''
  usage: ''
  tags: ''
```

- [ ] **Step 4: Commit skeletons**

```bash
cd /Users/f0x/pte-project/public/AboutSecurity
git add -A
git commit -m "feat(dic,payload): add skeleton _meta.yaml files for all directories"
```

---

### Task 7: AI-assisted metadata fill

**Files:**
- Modify: All `_meta.yaml` files in `Dic/` and `Payload/`

This task uses AI to read each data file's first lines + filename + directory context and generate draft metadata. Then human reviews.

- [ ] **Step 1: Add fill-meta command to migrate.py**

This command reads each `_meta.yaml`, for files with empty description, reads the first 20 lines of the data file, and generates a draft description/usage/tags.

Append before `main()`:

```python
def generate_file_metadata(filepath, category, subcategory=""):
    """Read first lines of a file and generate draft metadata.

    Returns (description, usage, tags) tuple.
    This is a heuristic-based generator. Human review required.
    """
    _, ext = os.path.splitext(filepath)
    fname = os.path.basename(filepath)

    # Read first 20 lines for context
    lines = []
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            for i, line in enumerate(f):
                if i >= 20:
                    break
                lines.append(line.rstrip())
    except Exception:
        pass

    sample = "\n".join(lines)
    total = count_lines(filepath)

    # Build basic description from filename
    base = os.path.splitext(fname)[0]
    desc = f"{category}"
    if subcategory:
        desc += f"/{subcategory}"
    desc += f" - {base} ({total} lines)"

    usage = ""
    tags = category
    if subcategory:
        tags += f",{subcategory}"

    return desc, usage, tags


def cmd_fill_meta(args):
    """Fill empty description/usage/tags in _meta.yaml with draft values."""
    print("=== Filling _meta.yaml with draft metadata ===")
    updated = 0

    for top_dir in ["Dic", "Payload"]:
        abs_top = os.path.join(BASE, top_dir)
        if not os.path.isdir(abs_top):
            continue

        for root, dirs, files in os.walk(abs_top):
            meta_path = os.path.join(root, "_meta.yaml")
            if not os.path.exists(meta_path):
                continue

            with open(meta_path, 'r', encoding='utf-8') as fh:
                meta = yaml.safe_load(fh)

            if not meta or 'files' not in meta:
                continue

            changed = False
            cat = meta.get('category', '')
            subcat = meta.get('subcategory', '')

            # Fill directory-level description if empty
            if not meta.get('description'):
                meta['description'] = f"{cat} {subcat} dictionaries".strip()
                changed = True

            for entry in meta['files']:
                if entry.get('description'):
                    continue  # already filled
                fpath = os.path.join(root, entry['name'])
                if not os.path.exists(fpath):
                    continue
                desc, usage, tags = generate_file_metadata(fpath, cat, subcat)
                entry['description'] = desc
                entry['usage'] = usage
                entry['tags'] = tags
                changed = True

            if changed:
                with open(meta_path, 'w', encoding='utf-8') as fh:
                    yaml.dump(meta, fh, allow_unicode=True, default_flow_style=False, sort_keys=False)
                updated += 1
                print(f"  Updated: {os.path.relpath(meta_path, BASE)}")

    print(f"\nUpdated {updated} _meta.yaml files with draft metadata.")
    print("IMPORTANT: Review and improve all description/usage/tags manually!")
```

Also add `"fill-meta": cmd_fill_meta` to the commands dict in `main()`, and add the subparser:

```python
p6 = sub.add_parser("fill-meta", help="Fill empty metadata fields with drafts")
```

- [ ] **Step 2: Run fill-meta to generate drafts**

```bash
cd /Users/f0x/pte-project/public/AboutSecurity
python scripts/migrate.py fill-meta
```

- [ ] **Step 3: Manually review and improve all `_meta.yaml` files**

Use AI in a separate session to iterate through each `_meta.yaml` and improve:
- `description`: One sentence in Chinese describing what the file contains
- `usage`: When/why to use this file (e.g., "登录爆破初筛", "WAF绕过测试")
- `tags`: Bilingual comma-separated keywords

Focus on high-value directories first:
1. `Dic/auth/password/` — most commonly used
2. `Payload/xss/` — largest payload collection
3. `Payload/sqli/` — most payload files
4. `Dic/web/api-param/` — parameter fuzzing
5. `Dic/web/directory/` — path discovery

- [ ] **Step 4: Commit filled metadata**

```bash
cd /Users/f0x/pte-project/public/AboutSecurity
git add -A
git commit -m "feat(dic,payload): fill _meta.yaml with descriptions, usage, and tags"
```

---

### Task 8: Update `build_index.py` to consume `_meta.yaml`

**Files:**
- Modify: `context1337/build/build_index.py:128-167`
- Create: `context1337/build/test_build_index.py`

- [ ] **Step 1: Write the test for _meta.yaml-based indexing**

Create `context1337/build/test_build_index.py`:

```python
#!/usr/bin/env python3
"""Tests for _meta.yaml-based dict/payload indexing."""
import os
import sqlite3
import tempfile
import shutil
import sys
import unittest

import yaml

# Add parent dir to path so we can import build_index
sys.path.insert(0, os.path.dirname(__file__))
import build_index


class TestMetaYamlIndexing(unittest.TestCase):
    def setUp(self):
        """Create temp dirs simulating AboutSecurity structure."""
        self.tmpdir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.tmpdir, "test.db")

        # Create Dic structure with _meta.yaml
        dic_dir = os.path.join(self.tmpdir, "data", "Dic", "auth", "password")
        os.makedirs(dic_dir)

        # Create data file
        with open(os.path.join(dic_dir, "top100.txt"), "w") as f:
            f.write("\n".join(f"pass{i}" for i in range(100)))

        # Create _meta.yaml
        meta = {
            "category": "auth",
            "subcategory": "password",
            "description": "常见弱口令字典集合",
            "tags": "password,弱口令,brute-force,login",
            "files": [{
                "name": "top100.txt",
                "lines": 100,
                "description": "最常见的100个弱口令",
                "usage": "登录爆破初筛、快速验证默认口令",
                "tags": "top,common,weak"
            }]
        }
        with open(os.path.join(dic_dir, "_meta.yaml"), "w") as f:
            yaml.dump(meta, f)

        # Create Dic file WITHOUT _meta.yaml (fallback)
        fallback_dir = os.path.join(self.tmpdir, "data", "Dic", "network")
        os.makedirs(fallback_dir)
        with open(os.path.join(fallback_dir, "dns-servers.txt"), "w") as f:
            f.write("8.8.8.8\n1.1.1.1\n")

        # Create Payload with _meta.yaml
        pay_dir = os.path.join(self.tmpdir, "data", "Payload", "xss")
        os.makedirs(pay_dir)
        with open(os.path.join(pay_dir, "js-event-list.txt"), "w") as f:
            f.write("onerror\nonload\nonfocus\n")
        pay_meta = {
            "category": "xss",
            "description": "XSS payload集合",
            "tags": "xss,cross-site scripting",
            "files": [{
                "name": "js-event-list.txt",
                "lines": 3,
                "description": "JavaScript事件属性名列表",
                "usage": "属性注入场景枚举可用事件",
                "tags": "event,attribute"
            }]
        }
        with open(os.path.join(pay_dir, "_meta.yaml"), "w") as f:
            yaml.dump(pay_meta, f)

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def _build_db(self):
        """Build index from temp data."""
        conn = sqlite3.connect(self.db_path)
        build_index.create_schema(conn)
        # Mock jieba with simple split
        build_index._tokenize_fn = lambda t: t
        data_dir = os.path.join(self.tmpdir, "data")
        build_index.index_dicts(conn, data_dir)
        build_index.index_payloads(conn, data_dir)
        conn.commit()
        return conn

    def test_dict_with_meta_yaml(self):
        """Dict with _meta.yaml gets rich metadata indexed."""
        conn = self._build_db()
        row = conn.execute(
            "SELECT description, tags, category FROM resources WHERE type='dict' AND name LIKE '%top100%'"
        ).fetchone()
        self.assertIsNotNone(row, "top100.txt should be indexed")
        self.assertIn("弱口令", row[0])  # description from _meta.yaml
        self.assertIn("password", row[1])  # tags merged
        self.assertEqual("auth", row[2])   # category from meta
        conn.close()

    def test_dict_fallback_without_meta(self):
        """Dict without _meta.yaml falls back to path-based indexing."""
        conn = self._build_db()
        row = conn.execute(
            "SELECT description, category FROM resources WHERE type='dict' AND name LIKE '%dns%'"
        ).fetchone()
        self.assertIsNotNone(row, "dns-servers.txt should be indexed")
        self.assertEqual("network", row[1])  # category from path
        conn.close()

    def test_payload_with_meta_yaml(self):
        """Payload with _meta.yaml gets rich metadata."""
        conn = self._build_db()
        row = conn.execute(
            "SELECT description, tags, category FROM resources WHERE type='payload' AND name LIKE '%js-event%'"
        ).fetchone()
        self.assertIsNotNone(row, "js-event-list.txt should be indexed")
        self.assertIn("事件", row[0])
        self.assertIn("xss", row[1])
        self.assertEqual("xss", row[2])
        conn.close()

    def test_meta_tags_merged(self):
        """Directory-level and file-level tags are merged."""
        conn = self._build_db()
        row = conn.execute(
            "SELECT tags FROM resources WHERE type='dict' AND name LIKE '%top100%'"
        ).fetchone()
        tags = row[0]
        # Should contain both dir-level tags and file-level tags
        self.assertIn("password", tags)    # dir-level
        self.assertIn("common", tags)      # file-level
        conn.close()


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test — verify it fails**

```bash
cd /Users/f0x/pte-project/public/context1337
python -m pytest build/test_build_index.py -v
```

Expected: FAIL — `_tokenize_fn` not found, no `_meta.yaml` parsing in `index_dicts`/`index_payloads`.

- [ ] **Step 3: Implement _meta.yaml-aware indexing in build_index.py**

Replace `index_dicts` (lines 128-146) and `index_payloads` (lines 149-167) with:

```python
def _load_meta_yaml(directory):
    """Load _meta.yaml from a directory if it exists. Returns dict or None."""
    meta_path = os.path.join(directory, "_meta.yaml")
    if not os.path.exists(meta_path):
        return None
    try:
        with open(meta_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception:
        return None


def _index_data_dir(conn, base_dir, subdir, resource_type):
    """Index dict or payload files, using _meta.yaml when available.

    Falls back to path-based indexing for directories without _meta.yaml.
    """
    data_dir = os.path.join(base_dir, subdir)
    if not os.path.isdir(data_dir):
        return 0

    skip_files = {'_meta.yaml', '.gitkeep', '.DS_Store'}
    count = 0

    for root, dirs, files in os.walk(data_dir):
        data_files = [f for f in files if f not in skip_files]
        if not data_files:
            continue

        meta = _load_meta_yaml(root)

        if meta and "files" in meta:
            # Build lookup: filename -> file entry
            file_lookup = {entry["name"]: entry for entry in meta["files"]}
            dir_tags = meta.get("tags", "")
            dir_cat = meta.get("category", "")

            for f in data_files:
                path = os.path.join(root, f)
                rel = os.path.relpath(path, data_dir)
                entry = file_lookup.get(f)

                if entry:
                    # Rich indexing from _meta.yaml
                    file_tags = entry.get("tags", "")
                    merged_tags = ",".join(filter(None, [dir_tags, file_tags]))
                    desc = entry.get("description", "")
                    usage = entry.get("usage", "")
                    body_text = f"{desc} {usage} {merged_tags}"

                    conn.execute(
                        "INSERT OR REPLACE INTO resources "
                        "(type,name,source,file_path,category,tags,description,body) "
                        "VALUES (?,?,?,?,?,?,?,?)",
                        (resource_type, rel, "builtin", path, dir_cat,
                         tokenize(merged_tags), tokenize(desc),
                         tokenize(body_text)),
                    )
                else:
                    # File exists but not in _meta.yaml — fallback
                    _index_file_fallback(conn, resource_type, data_dir, root, f)
                count += 1
        else:
            # No _meta.yaml — fallback to path-based
            for f in data_files:
                _index_file_fallback(conn, resource_type, data_dir, root, f)
                count += 1

    return count


def _index_file_fallback(conn, resource_type, data_dir, root, filename):
    """Fallback: index a file using only its path for metadata."""
    path = os.path.join(root, filename)
    rel = os.path.relpath(path, data_dir)
    parts = rel.split(os.sep)
    cat = parts[0] if len(parts) > 1 else ""
    label = "dictionary" if resource_type == "dict" else "payload"
    conn.execute(
        "INSERT OR REPLACE INTO resources "
        "(type,name,source,file_path,category,description,body) "
        "VALUES (?,?,?,?,?,?,?)",
        (resource_type, rel, "builtin", path, cat,
         f"{cat} {label}: {filename}", tokenize(f"{cat} {filename}")),
    )


def index_dicts(conn, base_dir):
    """Index dictionary files, using _meta.yaml when available."""
    return _index_data_dir(conn, base_dir, "Dic", "dict")


def index_payloads(conn, base_dir):
    """Index payload files, using _meta.yaml when available."""
    return _index_data_dir(conn, base_dir, "Payload", "payload")
```

- [ ] **Step 4: Run the tests — verify they pass**

```bash
cd /Users/f0x/pte-project/public/context1337
python -m pytest build/test_build_index.py -v
```

Expected: All 4 tests pass.

- [ ] **Step 5: Run existing Go tests to ensure nothing broke**

```bash
cd /Users/f0x/pte-project/public/context1337
go test ./...
```

Expected: All pass.

- [ ] **Step 6: Commit**

```bash
cd /Users/f0x/pte-project/public/context1337
git add build/build_index.py build/test_build_index.py
git commit -m "feat: support _meta.yaml for rich dict/payload indexing with fallback"
```

---

### Task 9: Rebuild index and end-to-end test

**Files:**
- No new files; uses existing `make` targets

- [ ] **Step 1: Rebuild the FTS5 index**

```bash
cd /Users/f0x/pte-project/public/context1337
make index
```

Expected: `Built data/builtin.db: N skills, N dicts, N payloads, N tools` — dict/payload counts should match pre-migration counts (or close).

- [ ] **Step 2: Start the server**

```bash
cd /Users/f0x/pte-project/public/context1337
make run
```

- [ ] **Step 3: Test search quality with curl**

In another terminal, verify that the enriched metadata improves search results:

```bash
# Test 1: Search for password dictionaries — should match description/tags
curl -s 'http://localhost:8088/api/health' | python3 -m json.tool

# Test 2: Use MCP to search
# In Claude Code: "搜索弱口令字典" -> should match Dic/auth/password via tags
# In Claude Code: "XSS参数Fuzz" -> should match via _meta.yaml description
# In Claude Code: "SQL注入payload" -> should match Payload/sqli via tags
```

- [ ] **Step 4: Verify path-based fallback still works**

Any file without `_meta.yaml` coverage should still appear in search results (using the path-derived category and filename).

- [ ] **Step 5: Final commit for any adjustments**

```bash
cd /Users/f0x/pte-project/public/context1337
git add -A
git commit -m "fix: post-migration index adjustments"
```

---

### Task 10: Update symlinks and documentation

**Files:**
- Modify: `context1337/.gitignore` (if Dic→dic or Payload→payload changed)
- Modify: `context1337/Makefile` (if data dir names changed)
- Modify: `AboutSecurity/README.md` (document new structure)

- [ ] **Step 1: Verify symlinks still work**

The Dic/ and Payload/ top-level directory names are unchanged (only their contents renamed), so existing symlinks should still work. Verify:

```bash
cd /Users/f0x/pte-project/public/context1337
ls -la data/Dic data/Payload
```

- [ ] **Step 2: Update AboutSecurity README if needed**

Add a section to `AboutSecurity/README.md` documenting the naming convention and `_meta.yaml` structure.

- [ ] **Step 3: Commit documentation updates**

```bash
cd /Users/f0x/pte-project/public/AboutSecurity
git add -A
git commit -m "docs: update README with standardized naming convention and _meta.yaml schema"
```
