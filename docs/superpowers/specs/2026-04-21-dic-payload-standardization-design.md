# Dic & Payload Standardization Design

> Make Dic/Payload as AI-searchable as Skills by adding naming consistency and structured metadata.

## Problem

Skills are self-describing (YAML frontmatter with name, description, tags, category, mitre_attack). Dic (231 files) and Payload (65 files) rely entirely on file paths for discovery. `build_index.py` only indexes `"{category} {filename}"` into FTS5 -- the search surface is paper-thin. AI searches like "XSS parameter fuzz" or "weak password top 100" fail to match because there are no descriptions, tags, or usage annotations.

Additional issues:
- 5 naming conventions coexist in Dic (`Fuzz_`, `Top`, bare, full Chinese, mixed)
- ~20 Chinese filenames break cross-platform compatibility
- Inconsistent casing across directories (`SVG/` vs `html/`, `SQL-Inj` vs `upload`)
- Typos (`pingyin` instead of `pinyin`)
- Utility scripts (`.py`) mixed in with data files
- `Payload/Burp/` contains tool config, not attack payloads

## Approach

**B: Rename + Metadata** -- standardize file/directory names and add per-directory `_meta.yaml` files consumed by `build_index.py`.

## 1. Naming Convention

### Directories

- All lowercase, hyphen-separated
- Examples: `File_Backup` -> `file-backup`, `SQL-Inj` -> `sqli`, `api_param` -> `api-param`
- Fix typos: `pingyin` -> `pinyin`

### Files

- All English, lowercase, hyphen-separated
- Drop `Fuzz_` prefix (carries no semantic value -- nearly all files are fuzz lists)
- Chinese filenames translated to semantic English names

| Before | After |
|---|---|
| `Fuzz_pass01-100.txt` | `password-top100.txt` |
| `至少一个大写字母一个小写字母一个数字的8位数密码.txt` | `complex-8char-upper-lower-digit.txt` |
| `Fuzz_cn_email.txt` | `cn-email.txt` |
| `Top100_asp.txt` | `top100-asp-path.txt` |
| `Fuzz_xss_Payload2.txt` | `xss-tag-event-full.txt` |
| `Source_姓.txt` | `cn-surname-pinyin.txt` |
| `xff-403.txt` | `xff-bypass.txt` |

### Scripts

- `姓名转拼音.py`, `加斜杠用.py` -- move to repo-level `scripts/` or delete. Data directories contain only data files.

## 2. Directory Structure

### Dic/

Keep existing 5 top-level categories (auth, network, port, regular, web). Fix casing and sub-directory names:

```
dic/
├── _meta.yaml
├── auth/
│   ├── _meta.yaml
│   ├── password/
│   │   ├── _meta.yaml
│   │   ├── top100.txt
│   │   ├── top1000.txt
│   │   ├── top10000.txt
│   │   ├── top100000.txt
│   │   ├── admin-common.txt
│   │   ├── sql-keyword.txt
│   │   ├── complex-8char-upper-lower-digit.txt
│   │   ├── ...
│   │   └── wpa/
│   │       ├── _meta.yaml
│   │       └── ...
│   └── username/
│       ├── _meta.yaml
│       ├── cn-top100.txt
│       ├── cn-email.txt
│       ├── cn-phone.txt
│       └── pinyin/                 # fix: pingyin -> pinyin
│           ├── _meta.yaml
│           ├── cn-surname.txt
│           └── cn-firstname.txt
├── network/
│   ├── _meta.yaml
│   └── ...
├── port/
│   ├── _meta.yaml
│   └── {mysql,redis,ssh,...}/      # already well-structured
├── regular/
│   ├── _meta.yaml
│   ├── letter/
│   ├── number/
│   └── address/
└── web/
    ├── _meta.yaml
    ├── api-param/                  # api_param -> api-param
    ├── cms/                        # CMS -> cms
    ├── ctf/                        # CTF -> ctf
    ├── directory/
    │   ├── asp/
    │   ├── jsp/
    │   ├── php/
    │   └── ...
    ├── dns/
    ├── file-backup/                # File_Backup -> file-backup
    ├── http/
    ├── middleware/
    ├── service/
    ├── upload/
    └── webshell/
```

### Payload/

Lowercase all directories. Merge/clean:
- `403/` -> `access-bypass/` (renamed, contents are auth bypass payloads)
- `ai/` -> `prompt-injection/` (clearer semantics)
- `Burp/Proxifier_filter.txt` -> move to `Dic/web/` or delete (not a payload)
- `SQL-Inj/` -> `sqli/`
- All caps dirs (`CORS`, `HPP`, `LFI`, `RCE`, `SSI`, `SSRF`, `XSS`, `XXE`) -> lowercase
- `Format/` -> `format/`
- `XSS/SVG/` -> `xss/svg/`

```
payload/
├── _meta.yaml
├── access-bypass/                  # 403/ merged + renamed
├── cors/
├── email/
├── format/
├── hpp/
├── lfi/
├── prompt-injection/               # ai/ -> prompt-injection
├── rce/
├── sqli/                           # SQL-Inj -> sqli
├── ssi/
├── ssrf/
├── upload/
├── xss/
│   ├── svg/
│   ├── html/
│   ├── pdf/
│   └── xml/
└── xxe/
```

## 3. `_meta.yaml` Schema

One file per directory that contains data files:

```yaml
# Required: directory-level fields
category: auth                       # top-level category, matches dir name
subcategory: password                # optional, for nested dirs
description: "常见弱口令及按复杂度规则生成的密码字典"
tags: "password,弱口令,爆破,brute-force,login,credential"

# Required: per-file entries
files:
  - name: top100.txt                 # must match actual filename
    lines: 100                       # approximate line count
    description: "最常见的100个弱口令"
    usage: "登录爆破初筛、快速验证默认口令"
    tags: "top,common,weak"

  - name: complex-8char-upper-lower-digit.txt
    lines: 12000
    description: "8位，含至少1个大写+1个小写+1个数字"
    usage: "针对有复杂度策略的系统进行密码爆破"
    tags: "complex,policy,8char"
```

### Field Reference

| Field | Level | Required | Description |
|---|---|---|---|
| `category` | directory | yes | Top-level category, matches directory name |
| `subcategory` | directory | no | Sub-category for nested directories |
| `description` | both | yes | Directory: overview. File: specific content description |
| `tags` | both | yes | Comma-separated, bilingual (Chinese + English) |
| `files[].name` | file | yes | Exact filename, must match file on disk |
| `files[].lines` | file | yes | Approximate line count |
| `files[].usage` | file | yes | When/why to use this file (for AI decision-making) |

## 4. `build_index.py` Changes

### New indexing logic for Dic/Payload

```
Walk Dic/ and Payload/ directories:
  If _meta.yaml exists in directory:
    Parse YAML
    For each files[] entry:
      name        = relative_path + file.name
      category    = meta.category
      description = file.description
      tags        = meta.tags (dir-level) + "," + file.tags (file-level)
      body        = tokenize(description + " " + usage + " " + tags)
  Else:
    Fallback to current logic (path-derived category + filename)
```

### Search surface comparison

| FTS Column | Before | After |
|---|---|---|
| `name` | `Web/api_param/Fuzz_param_XSS.txt` | `web/api-param/xss-param-fuzz.txt` |
| `description` | `Web dictionary: Fuzz_param_XSS.txt` | `XSS漏洞常见可注入参数名` |
| `tags` | NULL | `xss,parameter,fuzz,注入,参数` |
| `body` | `tokenize("Web Fuzz_param_XSS.txt")` | `tokenize("XSS漏洞常见可注入参数名 反射型XSS参数枚举 xss,parameter,fuzz")` |

## 5. Migration Strategy

### Tooling: `scripts/migrate-dicts-payloads.py`

**Step 1: Auto-rename**
- Directory names: lowercase, underscore -> hyphen, fix typos
- File names: drop `Fuzz_` prefix, lowercase, underscore -> hyphen
- Chinese filenames: generate `rename-map.yaml` for manual English name assignment (~20 files)
- Execute via `git mv` to preserve history

**Step 2: Generate skeleton `_meta.yaml`**
- Scan renamed directory structure
- Auto-fill: `category` (from path), `files[].name`, `files[].lines` (via `wc -l`)
- Leave empty: `description`, `usage`, `tags`
- Output: ~40 `_meta.yaml` skeleton files

**Step 3: AI-assisted metadata fill**
- Read first 20 lines of each file + filename + directory context
- Generate draft `description`, `usage`, `tags`
- Human reviews and corrects

### Execution order

1. Run Step 1 -> batch `git mv` renames
2. Manually fill ~20 Chinese filename translations -> `git mv` again
3. Run Step 2 -> generate skeleton `_meta.yaml`
4. Run Step 3 (AI-assisted) -> fill metadata drafts
5. Human review all `_meta.yaml`
6. Update `build_index.py` to consume `_meta.yaml`
7. Rebuild index, end-to-end test

## 6. Out of Scope

- Skills directory: already standardized, no changes needed
- Tools directory: already has YAML metadata, no changes in this round
- `context1337` MCP tool API changes: existing `get_dict`, `get_payload`, `search_dicts`, `search_payload` APIs remain unchanged -- they benefit automatically from richer index data
- Content quality of individual wordlists (dedup, pruning, expansion) -- separate effort
