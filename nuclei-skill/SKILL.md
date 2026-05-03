---
name: nuclei-template-generation
description: Use when creating, writing, or generating Nuclei YAML templates for CVE coverage, vulnerability detection, exposure detection, misconfiguration checks, or security scanning workflows
---

# Nuclei Template Generation

## Overview

Nuclei templates are YAML definitions that describe how to detect vulnerabilities, misconfigurations, or exposed assets with low false positives. This skill follows the official [TEMPLATE-CREATION-GUIDE.md](TEMPLATE-CREATION-GUIDE.md) in this repository.

## When to Use

- Creating a new template for a CVE or vulnerability
- Writing detection templates for exposed files, panels, or tech stack fingerprinting
- Converting manual PoC/exploit steps into a reusable Nuclei template
- Generating templates for bug bounty or enterprise security workflows

**Don't use for:** Running nuclei scans (use CLI directly), interpreting scan results.

## Template Structure

```yaml
id: template-identifier

info:
  name: Human Readable Vulnerability Name
  author: your-github-username,original-researcher-handle
  severity: critical|high|medium|low|info
  description: |
    Clear explanation of what this template detects and the root cause.
  reference:
    - https://link-to-vulnerability-details
    - https://nvd.nist.gov/vuln/detail/CVE-YYYY-NNNN
  classification:
    cvss-metrics: CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H
    cvss-score: 9.8
    cve-id: CVE-YYYY-NNNN
    cwe-id: CWE-89
  tags: cve,cveYYYY,rce,sqli
  metadata:
    verified: true          # Only if tested yourself
    max-request: 1          # Auto-calculated, don't set manually
    shodan-query: 'http.title:"AppName"'
    fofa-query: 'body="app" && title="App"'
    vendor: vendor-name
    product: product-name

protocol-type:
  - method: GET
    path:
      - "{{BaseURL}}/vulnerable-endpoint"
    matchers:
      - type: word
        words:
          - "vulnerability_indicator"
        part: body
```

## ID Naming Rules

```yaml
# GOOD - clear and specific
id: apache-struts-ognl-injection
id: CVE-2024-1234
id: wp-plugin-name-rce

# BAD - too generic
id: vuln-app-rce
id: test-template
```
- Use kebab-case only
- CVEs: `CVE-YYYY-NNNN`
- WordPress: `wp-plugin-vuln-type`
- Tech detection: `product-name-detect`

## Severity Levels

| Severity | When to Use |
|----------|-------------|
| `critical` | RCE, auth bypass, full compromise, CVSS 9.0–10.0 |
| `high` | Significant data exposure, file read, CVSS 7.0–8.9 |
| `medium` | Info disclosure, misconfiguration, CVSS 4.0–6.9 |
| `low` | Minor info leak, version detection, CVSS 0.1–3.9 |
| `info` | Tech detection, non-exploitable findings |

## Tags

Always include specific, comprehensive tags separated by commas (no spaces):
- CVEs: `cve,cveYYYY,rce,kev`
- Exposures: `config,exposure,discovery`
- Tech: `tech,product,discovery`
- WordPress: `wp-plugin,wp,auth-bypass`

## Matcher Best Practices

### Avoid Weak Matchers

```yaml
# BAD - too generic, high false positive risk
matchers:
  - type: word
    words:
      - "error"
      - "admin"
      - "login"
    part: body
```

### Use Strong, Specific Matchers

```yaml
# GOOD - specific to the vulnerability
matchers-condition: and
matchers:
  - type: word
    words:
      - "VulnApp Management Console v2.1.0"  # Specific version
      - "Build 2024.03.15"                   # Specific build
    part: body
  - type: status
    status: [200]
  - type: word
    words:
      - "OGNL_INJECTION_SUCCESS_{{randstr}}"  # PoC proof
      - "java.lang.ProcessBuilder"            # Technical indicator
    part: body
    condition: or
```

### Multi-Layer Verification Strategy

```yaml
# Layer 1: Identify the application
# Layer 2: Confirm vulnerable version
# Layer 3: Prove vulnerability exists
matchers-condition: and
matchers:
  - type: word                    # Layer 1: App identification
    words:
      - "Apache Struts Framework"
      - "struts-tags"
    part: body
  - type: regex                   # Layer 2: Version detection
    regex:
      - 'Struts 2\.[0-4]\.[0-9]+'  # Vulnerable version range
    part: body
  - type: word                    # Layer 3: Exploitation proof
    words:
      - "ognl.OgnlException"
      - "java.lang.SecurityException"
    part: body
    condition: or
```

## Matcher Types

| Type | Description | Example |
|------|-------------|---------|
| `status` | HTTP status code | `status: [200, 302]` |
| `word` | Substring match | `words: ["root:x:0:0"]` |
| `regex` | Regex pattern | `regex: ["TVS-[0-9]{4}"]` |
| `binary` | Hex pattern | `binary: ["504B0304"]` |
| `dsl` | Expression | `dsl: ["status_code==200 && len(body)<1024"]` |
| `xpath` | XML/HTML query | `xpath: ["//title[contains(.,'Admin')]"]` |

### Matcher Conditions

```yaml
matchers:
  - type: word
    words: ["admin", "dashboard"]
    condition: and   # both must match (default: or)
    part: body
```

### Multiple Matchers

```yaml
matchers-condition: and   # or (default)
matchers:
  - type: status
    status: [200]
  - type: word
    words: ["secret"]
    part: body
```

### Negative Matchers

```yaml
matchers:
  - type: word
    words: ["PHPSESSID"]
    part: header
    negative: true   # match when NOT found
```

## Extractors (Data Extraction)

| Type | Purpose | Example |
|------|---------|---------|
| `regex` | Pattern extraction | `regex: ["([0-9]{1,3}\\.){3}[0-9]{1,3}"]`, `group: 1` |
| `kval` | Header/cookie key-value | `kval: [content_type, server]` |
| `json` | JSON field (JQ syntax) | `json: [".data[].id"]` |
| `xpath` | XML/HTML extraction | `xpath: ["//title/text()"]`, `attribute: href` |
| `dsl` | Expression result | `dsl: ["len(body)"]` |

```yaml
extractors:
  - type: regex
    name: version
    regex:
      - 'Version: ([0-9\.]+)'
    group: 1
```

## Variables & Built-ins

```yaml
variables:
  username: "admin"
  cmd: "whoami"
  marker: "{{rand_base(8)}}"
  payload: "{{rand_int(111, 999)}}"
```

Common built-ins: `{{BaseURL}}`, `{{Hostname}}`, `{{Host}}`, `{{Port}}`, `{{interactsh-url}}`, `{{randstr}}`, `{{rand_base(N)}}`, `{{rand_int(MIN, MAX)}}`

## Common Vulnerability Patterns

### SQL Injection
```yaml
http:
  - method: POST
    path:
      - "{{BaseURL}}/search"
    body: "q={{payload}}"
    payloads:
      payload:
        - "1' OR '1'='1"
        - "1' UNION SELECT version()--"
    matchers:
      - type: word
        words:
          - "mysql_fetch_array(): supplied argument"
          - "You have an error in your SQL syntax"
          - "Microsoft OLE DB Provider for ODBC"
        part: body
```

### Remote Code Execution (RCE)
```yaml
variables:
  cmd: "whoami"
  marker: "{{rand_base(8)}}"

http:
  - method: POST
    path:
      - "{{BaseURL}}/execute"
    body: |
      command={{cmd}} && echo {{marker}}
    matchers:
      - type: word
        words: ["{{marker}}"]
        part: body
      - type: regex
        regex: ['root|administrator|www-data']
        part: body
```

### Local File Inclusion (LFI)
```yaml
http:
  - method: GET
    path:
      - "{{BaseURL}}/view?file=../../../etc/passwd"
      - "{{BaseURL}}/view?file=..\\..\\windows\\win.ini"
    matchers:
      - type: regex
        regex:
          - 'root:.*?:[0-9]*:[0-9]*:'  # Linux /etc/passwd
          - '\[fonts\]'                 # Windows win.ini
        part: body
```

### Authentication Bypass
```yaml
http:
  - method: GET
    path:
      - "{{BaseURL}}/admin"
    headers:
      X-Originating-IP: 127.0.0.1
      X-Forwarded-For: 127.0.0.1
      X-Real-IP: 127.0.0.1
    matchers-condition: and
    matchers:
      - type: word
        words: ["Admin Dashboard", "Administrative Panel"]
        part: body
      - type: status
        status: [200]
```

### Exposed File Detection
```yaml
http:
  - method: GET
    path:
      - "{{BaseURL}}/config.json"
    matchers:
      - type: word
        words: ["api_key", "secret"]
        condition: and
        part: body
```

### Tech Detection (Fingerprinting)
```yaml
http:
  - method: GET
    path:
      - "{{BaseURL}}/favicon.ico"
    matchers:
      - type: dsl
        dsl:
          - "status_code==200 && (\"-12345678\" == mmh3(base64_py(body)))"
```

## Protocol Types

| Protocol | Use Case | Key Fields |
|----------|----------|------------|
| `http` | Web vulnerabilities, exposed files | `method`, `path`, `raw`, `headers`, `body` |
| `dns` | Subdomain takeovers, DNS records | `name`, `type`, `class` |
| `network`/`tcp` | Port-based checks, banners | `host`, `inputs`, `read-size` |
| `file` | Local file analysis | `extensions`, `mime-types` |
| `headless` | JS-rendered pages | `steps` with actions |
| `ssl` | TLS/SSL checks | `host` |

## Conditional Logic with DSL

```yaml
matchers:
  - type: dsl
    dsl:
      - 'status_code == 200'
      - 'contains(body, "vulnerable_pattern")'
      - 'len(body) > 1000'
    condition: and
```

## Network Template (Non-HTTP Services)

```yaml
network:
  - inputs:
      - data: "{{hex_decode('474554202f20485454502f312e310d0a0d0a')}}"
    host:
      - "{{Hostname}}"
    port: 8080
    matchers:
      - type: word
        words: ["Server: VulnServer/1.0"]
        part: data
```

## Testing Checklist

```bash
# Test against known vulnerable instance
nuclei -t your-template.yaml -u http://vulnerable-app.local -debug

# Test against patched/non-vulnerable systems
nuclei -t your-template.yaml -u http://patched-app.local -debug

# Validate YAML syntax
nuclei -validate -t your-template.yaml
```

**Validation checklist:**
- [ ] Detects vulnerability on vulnerable systems
- [ ] No false positives on patched versions of same application
- [ ] No false positives on similar applications from same vendor
- [ ] No false positives on generic web frameworks/CMS
- [ ] Matchers are specific enough to avoid honeypots
- [ ] References are valid and accessible
- [ ] YAML syntax is valid

## Submission Guidelines

1. **Validate**: `nuclei -validate -t your-template.yaml`
2. **Test thoroughly** against vulnerable and non-vulnerable targets
3. **Check for existing templates** — avoid duplication
4. **Follow naming**: place in `cves/YYYY/`, `exposures/`, `misconfiguration/` as appropriate
5. **Pull Request**: Include vulnerability link, affected versions, testing methodology, debug output

## Quality Checklist

- [ ] Template detects the intended vulnerability
- [ ] No false positives on tested systems
- [ ] Original vulnerability discoverer credited in author field
- [ ] All references included and valid
- [ ] Proper CVSS scoring if applicable
- [ ] YAML syntax is valid
- [ ] Follows nuclei template conventions
- [ ] Includes appropriate tags and metadata
- [ ] Tested against vulnerable instance
- [ ] Clear description of what template detects

## Quick Reference

```
Structure: ID + info(name,author,severity,description,reference,classification,tags,metadata) + protocol + matchers + extractors
Matchers: status, word, regex, dsl, binary, xpath  |  condition: and/or  |  negative: true
Extractors: regex, kval, json, xpath, dsl  |  group: N for regex capture groups
Severities: info < low < medium < high < critical
Built-ins: {{BaseURL}}, {{Hostname}}, {{interactsh-url}}, {{randstr}}, {{rand_base(N)}}, {{rand_int(MIN,MAX)}}
```
