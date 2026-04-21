#!/usr/bin/env python3
"""
migrate.py — One-time migration tool for Dic/Payload standardization.

Subcommands:
    rename-dirs       Rename directories to lowercase-hyphen
    rename-files      Rename files (drop Fuzz_ prefix, lowercase, underscore->hyphen)
    gen-chinese-map   Generate rename-map.yaml for Chinese-named files
    apply-chinese-map Apply rename-map.yaml
    gen-meta          Generate skeleton _meta.yaml for each directory with data files
    fill-meta         Fill empty description/usage/tags with heuristic drafts

Usage:
    python3 scripts/migrate.py rename-dirs --dry-run
    python3 scripts/migrate.py rename-files --dry-run
    python3 scripts/migrate.py gen-chinese-map
    python3 scripts/migrate.py apply-chinese-map --dry-run
    python3 scripts/migrate.py gen-meta
    python3 scripts/migrate.py fill-meta
"""

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

import yaml

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent

# Directory renames: depth-first order (deepest first).
DIR_RENAMES = [
    # Dic: deep subdirs first
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
    # Payload: deep subdirs first
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

# Chinese character range for detection
_CJK_RE = re.compile(r"[\u4e00-\u9fff]")

RENAME_MAP_FILE = REPO_ROOT / "rename-map.yaml"

# Directories to scan for data files
DATA_ROOTS = ["Dic", "Payload"]

# File extensions considered "data files" (for _meta.yaml generation)
DATA_EXTENSIONS = {
    ".txt", ".csv", ".json", ".xml", ".yaml", ".yml",
    ".md", ".html", ".svg", ".pdf", ".py",
    ".doc", ".xlsx", ".zip",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _git_mv(src: Path, dst: Path, dry_run: bool = False) -> bool:
    """Run ``git mv src dst``, creating parent dirs as needed.

    Handles case-only renames on case-insensitive filesystems via two-step
    rename through a temporary name.

    Returns True on success, False on skip/failure.
    """
    if not src.exists():
        print(f"  [SKIP] source missing: {src}")
        return False

    # Detect case-only rename via inode comparison
    try:
        is_case_only = dst.exists() and os.path.samefile(str(src), str(dst))
    except OSError:
        is_case_only = False

    if dry_run:
        tag = " (case-only)" if is_case_only else ""
        print(f"  [DRY-RUN] git mv {src.relative_to(REPO_ROOT)} -> {dst.relative_to(REPO_ROOT)}{tag}")
        return True

    if is_case_only:
        # Two-step rename: src -> tmp -> dst
        tmp = src.with_name(src.name + "_tmp_migrate")
        r1 = subprocess.run(
            ["git", "mv", str(src), str(tmp)],
            cwd=str(REPO_ROOT), capture_output=True, text=True,
        )
        if r1.returncode != 0:
            print(f"  [ERROR] case-only step 1 failed: {r1.stderr.strip()}")
            return False
        dst.parent.mkdir(parents=True, exist_ok=True)
        r2 = subprocess.run(
            ["git", "mv", str(tmp), str(dst)],
            cwd=str(REPO_ROOT), capture_output=True, text=True,
        )
        if r2.returncode != 0:
            print(f"  [ERROR] case-only step 2 failed: {r2.stderr.strip()}")
            return False
        print(f"  [OK] {src.relative_to(REPO_ROOT)} -> {dst.relative_to(REPO_ROOT)} (case-only)")
        return True

    dst.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        ["git", "mv", str(src), str(dst)],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"  [ERROR] git mv failed: {result.stderr.strip()}")
        return False

    print(f"  [OK] {src.relative_to(REPO_ROOT)} -> {dst.relative_to(REPO_ROOT)}")
    return True


def _has_chinese(name: str) -> bool:
    """Return True if *name* contains CJK characters."""
    return bool(_CJK_RE.search(name))


def _rename_file_stem(filename: str) -> str | None:
    """Apply file rename rules to *filename*.

    Returns the new filename, or None if the file contains Chinese characters
    (needs manual mapping).

    Rules applied in order:
    1. If filename contains Chinese chars -> return None
    2. Split into stem + extension
    3. Drop ``Fuzz_`` prefix
    4. ``Top<N>_`` -> ``top<N>-``
    5. Lowercase
    6. Underscore -> hyphen
    7. Collapse multiple hyphens
    8. Strip leading/trailing hyphens from stem
    9. Rejoin stem + lowercased extension
    """
    if _has_chinese(filename):
        return None

    stem, ext = os.path.splitext(filename)

    # Drop Fuzz_ prefix
    stem = re.sub(r"^Fuzz_", "", stem)

    # Top<N>_ -> top<N>-
    stem = re.sub(r"^Top(\d+)_", r"top\1-", stem, flags=re.IGNORECASE)

    # Lowercase
    stem = stem.lower()

    # Underscore to hyphen
    stem = stem.replace("_", "-")

    # Collapse multiple hyphens
    stem = re.sub(r"-{2,}", "-", stem)

    # Strip leading/trailing hyphens
    stem = stem.strip("-")

    return stem + ext.lower()


def _count_lines(path: Path) -> int:
    """Count lines in a text file; return 0 for binary/unreadable files."""
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return sum(1 for _ in f)
    except Exception:
        return 0


def _category_from_path(rel_path: Path) -> tuple[str, str | None]:
    """Extract (category, subcategory) from a relative path under Dic/ or Payload/.

    Example: Dic/auth/password/complex -> ("auth", "password")
             Payload/xss -> ("xss", None)
    """
    parts = rel_path.parts  # e.g. ("Dic", "auth", "password", "complex")
    if len(parts) < 2:
        return (parts[0].lower() if parts else "unknown", None)

    category = parts[1]  # first level after Dic/Payload
    subcategory = parts[2] if len(parts) > 2 else None
    return (category, subcategory)


# ---------------------------------------------------------------------------
# Subcommand: rename-dirs
# ---------------------------------------------------------------------------

def cmd_rename_dirs(args: argparse.Namespace) -> None:
    """Rename directories according to DIR_RENAMES mapping."""
    dry_run = args.dry_run
    mode = "DRY-RUN" if dry_run else "LIVE"
    print(f"\n=== rename-dirs ({mode}) ===\n")

    ok = 0
    skip = 0
    for old_rel, new_rel in DIR_RENAMES:
        src = REPO_ROOT / old_rel
        dst = REPO_ROOT / new_rel

        if src == dst:
            print(f"  [SKIP] no-op: {old_rel}")
            skip += 1
            continue

        if not src.exists():
            print(f"  [SKIP] source missing: {old_rel}")
            skip += 1
            continue

        # Check for genuine destination conflict (not case-only rename)
        if dst.exists() and src != dst:
            try:
                same_file = os.path.samefile(str(src), str(dst))
            except OSError:
                same_file = False

            if not same_file:
                # Genuinely different directory already at dst
                print(f"  [SKIP] destination already exists: {new_rel}")
                skip += 1
                continue
            # else: case-only rename — _git_mv handles it

        if _git_mv(src, dst, dry_run=dry_run):
            ok += 1
        else:
            skip += 1

    print(f"\nSummary: {ok} renamed, {skip} skipped (total {len(DIR_RENAMES)} rules)")


# ---------------------------------------------------------------------------
# Subcommand: rename-files
# ---------------------------------------------------------------------------

def cmd_rename_files(args: argparse.Namespace) -> None:
    """Rename files: drop Fuzz_ prefix, lowercase, underscore->hyphen."""
    dry_run = args.dry_run
    mode = "DRY-RUN" if dry_run else "LIVE"
    print(f"\n=== rename-files ({mode}) ===\n")

    ok = 0
    skip = 0
    chinese = 0

    for root_name in DATA_ROOTS:
        root_dir = REPO_ROOT / root_name
        if not root_dir.exists():
            continue

        for dirpath, _dirnames, filenames in os.walk(root_dir):
            for fname in sorted(filenames):
                if fname.startswith("."):
                    continue

                new_name = _rename_file_stem(fname)

                if new_name is None:
                    print(f"  [CHINESE] {os.path.join(dirpath, fname)}")
                    chinese += 1
                    continue

                if new_name == fname:
                    # No change needed (already lowercase/clean)
                    continue

                src = Path(dirpath) / fname
                dst = Path(dirpath) / new_name

                if _git_mv(src, dst, dry_run=dry_run):
                    ok += 1
                else:
                    skip += 1

    print(f"\nSummary: {ok} renamed, {skip} skipped, {chinese} Chinese (need manual map)")


# ---------------------------------------------------------------------------
# Subcommand: gen-chinese-map
# ---------------------------------------------------------------------------

def cmd_gen_chinese_map(args: argparse.Namespace) -> None:
    """Generate rename-map.yaml listing all Chinese-named files."""
    print("\n=== gen-chinese-map ===\n")

    entries = []
    for root_name in DATA_ROOTS:
        root_dir = REPO_ROOT / root_name
        if not root_dir.exists():
            continue

        for dirpath, _dirnames, filenames in os.walk(root_dir):
            for fname in sorted(filenames):
                if not _has_chinese(fname):
                    continue

                rel = os.path.relpath(os.path.join(dirpath, fname), REPO_ROOT)
                entries.append({
                    "old": rel,
                    "new": "",  # to be filled manually
                    "note": fname,
                })

    if not entries:
        print("No Chinese-named files found.")
        return

    output = {"files": entries}
    with open(RENAME_MAP_FILE, "w", encoding="utf-8") as f:
        yaml.dump(output, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

    print(f"Generated {RENAME_MAP_FILE.relative_to(REPO_ROOT)} with {len(entries)} entries.")
    print("Edit the 'new' field for each entry, then run: migrate.py apply-chinese-map")


# ---------------------------------------------------------------------------
# Subcommand: apply-chinese-map
# ---------------------------------------------------------------------------

def cmd_apply_chinese_map(args: argparse.Namespace) -> None:
    """Apply rename-map.yaml to rename Chinese-named files."""
    dry_run = args.dry_run
    mode = "DRY-RUN" if dry_run else "LIVE"
    print(f"\n=== apply-chinese-map ({mode}) ===\n")

    if not RENAME_MAP_FILE.exists():
        print(f"ERROR: {RENAME_MAP_FILE.relative_to(REPO_ROOT)} not found.")
        print("Run 'migrate.py gen-chinese-map' first.")
        sys.exit(1)

    with open(RENAME_MAP_FILE, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if not data or "files" not in data:
        print("ERROR: rename-map.yaml has no 'files' key.")
        sys.exit(1)

    ok = 0
    skip = 0
    for entry in data["files"]:
        old_rel = entry.get("old", "")
        new_rel = entry.get("new", "")

        if not new_rel:
            print(f"  [SKIP] no mapping: {old_rel}")
            skip += 1
            continue

        src = REPO_ROOT / old_rel
        dst = REPO_ROOT / new_rel

        if _git_mv(src, dst, dry_run=dry_run):
            ok += 1
        else:
            skip += 1

    print(f"\nSummary: {ok} renamed, {skip} skipped (total {len(data['files'])} entries)")


# ---------------------------------------------------------------------------
# Subcommand: gen-meta
# ---------------------------------------------------------------------------

def cmd_gen_meta(args: argparse.Namespace) -> None:
    """Generate skeleton _meta.yaml for each directory containing data files."""
    print("\n=== gen-meta ===\n")

    created = 0
    skipped = 0

    for root_name in DATA_ROOTS:
        root_dir = REPO_ROOT / root_name
        if not root_dir.exists():
            continue

        for dirpath, dirnames, filenames in os.walk(root_dir):
            dirnames[:] = [d for d in dirnames if not d.startswith(".")]

            dp = Path(dirpath)
            meta_path = dp / "_meta.yaml"

            # Collect data files in this directory (not subdirs)
            data_files = []
            for fname in sorted(filenames):
                if fname.startswith(".") or fname.startswith("_"):
                    continue
                ext = Path(fname).suffix.lower()
                if ext in DATA_EXTENSIONS:
                    fpath = dp / fname
                    lines = _count_lines(fpath)
                    data_files.append({
                        "name": fname,
                        "lines": lines,
                        "description": "",
                        "usage": "",
                        "tags": "",
                    })

            if not data_files:
                continue

            if meta_path.exists():
                print(f"  [SKIP] already exists: {meta_path.relative_to(REPO_ROOT)}")
                skipped += 1
                continue

            # Derive category/subcategory from directory path
            rel_path = dp.relative_to(REPO_ROOT)
            category, subcategory = _category_from_path(rel_path)

            meta: dict = {"category": category}
            if subcategory:
                meta["subcategory"] = subcategory
            meta["description"] = ""
            meta["tags"] = ""
            meta["files"] = data_files

            with open(meta_path, "w", encoding="utf-8") as f:
                yaml.dump(meta, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

            print(f"  [OK] {meta_path.relative_to(REPO_ROOT)}")
            created += 1

    print(f"\nSummary: {created} created, {skipped} skipped")


# ---------------------------------------------------------------------------
# Subcommand: fill-meta
# ---------------------------------------------------------------------------

def cmd_fill_meta(args: argparse.Namespace) -> None:
    """Fill empty description/usage/tags in _meta.yaml with heuristic drafts."""
    print("\n=== fill-meta ===\n")

    updated = 0
    skipped = 0

    for root_name in DATA_ROOTS:
        root_dir = REPO_ROOT / root_name
        if not root_dir.exists():
            continue

        for meta_path in sorted(root_dir.rglob("_meta.yaml")):
            with open(meta_path, "r", encoding="utf-8") as f:
                meta = yaml.safe_load(f)

            if not meta:
                continue

            changed = False
            category = meta.get("category", "")
            subcategory = meta.get("subcategory", "")

            # Fill directory-level description
            if not meta.get("description"):
                parts = [category]
                if subcategory:
                    parts.append(subcategory)
                meta["description"] = f"{'/'.join(parts)} dictionaries"
                changed = True

            # Fill directory-level tags
            if not meta.get("tags"):
                tag_parts = [category]
                if subcategory:
                    tag_parts.append(subcategory)
                meta["tags"] = ", ".join(tag_parts)
                changed = True

            # Fill per-file fields
            for fentry in meta.get("files", []):
                fname = fentry.get("name", "")
                stem = Path(fname).stem
                total_lines = fentry.get("lines", 0)

                # description
                if not fentry.get("description"):
                    ctx = f"{category}/{subcategory}" if subcategory else category
                    fentry["description"] = f"{ctx} - {stem} ({total_lines} lines)"
                    changed = True

                # usage
                if not fentry.get("usage"):
                    fentry["usage"] = f"Fuzz/bruteforce wordlist for {stem}"
                    changed = True

                # tags
                if not fentry.get("tags"):
                    tag_parts = [category]
                    if subcategory:
                        tag_parts.append(subcategory)
                    tag_parts.append(stem)
                    fentry["tags"] = ", ".join(tag_parts)
                    changed = True

            if changed:
                with open(meta_path, "w", encoding="utf-8") as f:
                    yaml.dump(meta, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
                print(f"  [UPDATED] {meta_path.relative_to(REPO_ROOT)}")
                updated += 1
            else:
                print(f"  [SKIP] already filled: {meta_path.relative_to(REPO_ROOT)}")
                skipped += 1

    print(f"\nSummary: {updated} updated, {skipped} skipped")


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        prog="migrate.py",
        description="One-time migration tool for Dic/Payload standardization.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # rename-dirs
    p_rd = subparsers.add_parser("rename-dirs", help="Rename directories to lowercase-hyphen")
    p_rd.add_argument("--dry-run", action="store_true", help="Show what would be done without making changes")
    p_rd.set_defaults(func=cmd_rename_dirs)

    # rename-files
    p_rf = subparsers.add_parser("rename-files", help="Rename files (drop Fuzz_ prefix, lowercase, _->-)")
    p_rf.add_argument("--dry-run", action="store_true", help="Show what would be done without making changes")
    p_rf.set_defaults(func=cmd_rename_files)

    # gen-chinese-map
    p_gc = subparsers.add_parser("gen-chinese-map", help="Generate rename-map.yaml for Chinese-named files")
    p_gc.set_defaults(func=cmd_gen_chinese_map)

    # apply-chinese-map
    p_ac = subparsers.add_parser("apply-chinese-map", help="Apply rename-map.yaml")
    p_ac.add_argument("--dry-run", action="store_true", help="Show what would be done without making changes")
    p_ac.set_defaults(func=cmd_apply_chinese_map)

    # gen-meta
    p_gm = subparsers.add_parser("gen-meta", help="Generate skeleton _meta.yaml for each data directory")
    p_gm.set_defaults(func=cmd_gen_meta)

    # fill-meta
    p_fm = subparsers.add_parser("fill-meta", help="Fill empty description/usage/tags with heuristic drafts")
    p_fm.set_defaults(func=cmd_fill_meta)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
