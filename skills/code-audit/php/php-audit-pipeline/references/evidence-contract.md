# 证据合约系统

## 为什么需要证据合约

AI 进行源码审计时容易"看到危险函数就报漏洞"，忽略上游过滤、参数可控性、路径可达性，导致大量误报。证据合约系统强制要求每个漏洞结论附带完整数据流证明。

**核心原则**: 没有从 Source 到 Sink 的完整证据链，就不能将漏洞标记为"已确认可利用"。

## EVID_* 命名规则

格式: `EVID_{漏洞类型}_{证据维度}`。漏洞类型用大写缩写（SQL、CMD、XSS 等），证据维度描述该点证明的内容（EXEC_POINT=执行点、USER_PARAM=用户参数来源）。

## 各漏洞类型证据点定义

### SQL 注入
| 证据点 | 含义 |
|--------|------|
| `EVID_SQL_EXEC_POINT` | SQL 语句的实际执行位置（文件:行号 + 函数调用） |
| `EVID_SQL_STRING_CONSTRUCTION` | SQL 字符串的拼接/构造方式（拼接 vs 参数化） |
| `EVID_SQL_USER_PARAM_TO_SQL_FRAGMENT` | 用户输入进入 SQL 片段的完整路径 |

### 命令注入
| 证据点 | 含义 |
|--------|------|
| `EVID_CMD_EXEC_POINT` | 命令执行函数的调用位置 |
| `EVID_CMD_COMMAND_STRING_CONSTRUCTION` | 命令字符串的拼接方式 |
| `EVID_CMD_USER_PARAM_TO_CMD_FRAGMENT` | 用户输入进入命令字符串的路径 |

### SSRF
| 证据点 | 含义 |
|--------|------|
| `EVID_SSRF_URL_NORMALIZATION` | URL 的规范化/解析过程 |
| `EVID_SSRF_FINAL_URL_HOST_PORT` | 最终请求的目标主机和端口 |
| `EVID_SSRF_DNSIP_AND_INNER_BLOCK` | DNS 解析结果及内网限制检查 |

### XSS
| 证据点 | 含义 |
|--------|------|
| `EVID_XSS_OUTPUT_POINT` | 输出到 HTML 的位置和上下文 |
| `EVID_XSS_USER_INPUT_INTO_OUTPUT` | 用户输入到达输出点的路径 |
| `EVID_XSS_ESCAPE_OR_RAW_CONTROL` | 转义/编码处理或 raw 输出控制 |

### 文件读取/包含
| 证据点 | 含义 |
|--------|------|
| `EVID_FILE_WRAPPER_PREFIX` | 协议包装器（php://、phar://） |
| `EVID_FILE_RESOLVED_TARGET` | 最终解析的文件路径 |
| `EVID_FILE_INCLUDE_REQUIRE_EXEC_BOUNDARY` | include/require 的执行边界 |

### 文件写入
| 证据点 | 含义 |
|--------|------|
| `EVID_WRITE_WRITE_CALLSITE` | 写入函数的调用位置 |
| `EVID_WRITE_DESTPATH_RESOLVED_TARGET` | 目标路径的解析结果 |
| `EVID_WRITE_CONTENT_SOURCE_INTO_WRITE` | 写入内容的来源追踪 |
| `EVID_WRITE_EXECUTION_ACCESSIBILITY_PROOF` | 写入文件是否可被 Web 访问执行 |

### 文件上传
| 证据点 | 含义 |
|--------|------|
| `EVID_UPLOAD_DESTPATH` | 上传文件的存储目标路径 |
| `EVID_UPLOAD_FILENAME_EXTENSION_PARSING_SANITIZE` | 文件名和扩展名的解析与过滤逻辑 |
| `EVID_UPLOAD_ACCESSIBILITY_PROOF` | 上传文件是否可被 Web 直接访问 |

### XXE
| 证据点 | 含义 |
|--------|------|
| `EVID_XXE_PARSER_CALL` | XML 解析器的调用位置和类型 |
| `EVID_XXE_EXTERNAL_ENTITY_CONFIG` | 外部实体加载的配置状态 |
| `EVID_XXE_USER_INPUT_INTO_XML` | 用户输入进入 XML 解析的路径 |

### 反序列化
| 证据点 | 含义 |
|--------|------|
| `EVID_DESER_UNSERIALIZE_CALL` | 反序列化函数的调用位置 |
| `EVID_DESER_USER_INPUT_SOURCE` | 反序列化数据的用户输入来源 |
| `EVID_DESER_GADGET_CHAIN` | 可用的 Gadget Chain 及触发路径 |

### 其他类型简表
| 类型 | 证据点 |
|------|--------|
| 重定向 (REDIR) | `EVID_REDIR_TARGET_URL`, `EVID_REDIR_USER_INPUT_INTO_URL`, `EVID_REDIR_VALIDATION_CHECK` |
| CRLF | `EVID_CRLF_HEADER_CALL`, `EVID_CRLF_USER_INPUT_INTO_HEADER`, `EVID_CRLF_NEWLINE_FILTER` |
| CSRF | `EVID_CSRF_STATE_CHANGE_ACTION`, `EVID_CSRF_TOKEN_ABSENCE`, `EVID_CSRF_IMPACT_SCOPE` |
| LDAP | `EVID_LDAP_QUERY_CALL`, `EVID_LDAP_FILTER_CONSTRUCTION`, `EVID_LDAP_USER_INPUT_INTO_FILTER` |
| 表达式 (EXPR) | `EVID_EXPR_EVAL_CALL`, `EVID_EXPR_STRING_CONSTRUCTION`, `EVID_EXPR_USER_INPUT_INTO_EXPR` |
| 模板 (TPL) | `EVID_TPL_RENDER_CALL`, `EVID_TPL_RAW_OUTPUT_USAGE`, `EVID_TPL_USER_INPUT_INTO_TEMPLATE` |

## 证据引用格式示例

完整 SQL 注入证据引用样例:
```
漏洞: SQL 注入 | 文件: app/Controllers/UserController.php | 严重度: High (Score: 2.55)

[EVID_SQL_EXEC_POINT]
  位置: app/Models/User.php:87 | 调用: $db->query($sql)

[EVID_SQL_STRING_CONSTRUCTION]
  位置: app/Models/User.php:85-86
  代码: $sql = "SELECT * FROM users WHERE id = '" . $id . "'"
  方式: 字符串直接拼接，未使用预编译

[EVID_SQL_USER_PARAM_TO_SQL_FRAGMENT]
  Source: app/Controllers/UserController.php:23 — $id = $_GET['id']
  传递: UserController::show($id) → User::getUserById($id) → $sql 拼接
  过滤: 无 | 结论: 用户输入直接拼入 SQL，可利用
```

## 证据缺失处理规则

| 缺失情况 | 处理方式 | 标记状态 |
|----------|----------|----------|
| Sink 存在但无法追溯 Source | 记录 Sink 位置，标注数据来源不明 | 待验证 |
| Source→Sink 路径中有未知函数 | 记录已知部分，标注断点位置 | 待验证 |
| 存在过滤但无法确认可否绕过 | 记录过滤逻辑，列出潜在绕过思路 | 待验证 |
| 完整路径已追踪且过滤不充分 | 提供全部 EVID_* 证据 | 已确认 |
| 完整路径已追踪且过滤充分 | 记录过滤方式，说明安全原因 | 安全 |

关键原则: "待验证"比"误报为已确认"的代价低得多。不确定时保守标记。

## 严重度评分公式

### 三维度评分

**可达性 R（Reachability, 0-3）**: 0=管理员+特定配置, 1=普通用户认证, 2=未认证但需特定条件, 3=未认证直接可达

**影响范围 I（Impact, 0-3）**: 0=非敏感信息泄露, 1=敏感信息泄露, 2=数据篡改/部分控制, 3=RCE/完全控制

**利用复杂度 C（Complexity, 0-3, 反向评分）**: 0=多步+竞态, 1=特定环境/多步, 2=简单构造, 3=直接拼 payload

### 计算与映射

**加权公式**: `Score = R * 0.40 + I * 0.35 + C * 0.25`

**CVSS 3.1 近似映射**: `CVSS ≈ Score / 3.0 * 10.0`

| Score 范围 | CVSS 近似 | 等级 |
|-----------|-----------|------|
| 2.50 - 3.00 | 8.3 - 10.0 | Critical |
| 2.00 - 2.49 | 6.7 - 8.3 | High |
| 1.25 - 1.99 | 4.2 - 6.6 | Medium |
| 0.50 - 1.24 | 1.7 - 4.1 | Low |
| 0.00 - 0.49 | 0.0 - 1.6 | Info |
