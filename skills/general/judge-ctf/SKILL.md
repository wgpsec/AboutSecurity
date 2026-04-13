---
name: judge-ctf
description: "CTF flag-capture evaluation checklist for the decision Agent. Evaluates whether a CTF challenge is complete (flag found), analyzes reasons for failure, and provides precise guidance for flag acquisition."
metadata:
  tags: "judge,evaluation,ctf,flag,decision"
  category: "general"
---

# CTF Flag Capture Evaluation Checklist

## Sole Success Criterion

**Has flag{...} been found?**
- Search agent output logs for `flag{`
- Search evidence files for `flag{`
- Search vulns.json detail fields

Found → complete: true, no further evaluation needed.

## Diagnosis When Flag NOT Found

### Step 1: Was any vulnerability discovered?

```
if vuln_count == 0:
    → Insufficient reconnaissance, expand attack surface
    feedback: "No vulnerabilities discovered. Suggestions:
      1. Carefully inspect all HTTP responses for hidden clues
      2. Try directory bruteforce to discover hidden endpoints
      3. Check page source for comments and hidden parameters
      4. Try common default credentials for login"
```

### Step 2: Was the vulnerability exploited?

```
if vulns_found but not_exploited:
    → Insufficient exploitation
    feedback: "Discovered {vuln_type} but did not exploit to get flag. Suggestions:
      - SQLi: Use UNION SELECT to read database tables, find flag table
      - LFI: Read /flag.txt, /home/*/flag, /var/www/flag
      - RCE: find / -name 'flag*' 2>/dev/null
      - IDOR: Enumerate all id values, check each response for flag"
```

### Step 3: Exploited but no flag?

```
if vuln_exploited but no_flag:
    → Flag may not be in expected location
    feedback: "Vulnerability exploited but flag not found. Suggestions:
      1. Database search: SELECT * FROM flags / search all tables
      2. File search: find / grep -r 'flag{' / env | grep FLAG
      3. Check response headers: curl -v for HTTP headers
      4. Check hidden pages: use gained privileges to access /admin, /dashboard
      5. Check source code: decompile/view application source for hardcoded flag"
```

## Common CTF Challenge Patterns

Judge should know these patterns to provide precise feedback:

| Vuln Type | Flag Typically Located |
|-----------|----------------------|
| SQL Injection | A field in some database table |
| LFI/Path Traversal | /flag.txt or /etc/flag or in application directory |
| RCE/Command Injection | Filesystem, requires find/grep |
| IDOR | Content of a specific resource by id |
| Deserialization | Filesystem after gaining RCE |
| SSRF | Response from internal service |
| XSS | Usually no direct flag, unless admin bot exists |
| Info Disclosure | Source comments, backup files, config files |

## Feedback Precision Requirements

**FORBIDDEN**: vague feedback like "keep testing" or "dig deeper".

**MUST** provide specific:
1. Which discovered vulnerability to exploit
2. Concrete exploitation steps (payload-level)
3. Most likely flag location
