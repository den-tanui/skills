# {{NAME}} — Herdr Port Specification

## Source

- **Tmux plugin:** {{URL or local path}}
- **Analysis date:** {{date}}

## Overview

{{2-3 sentence summary of what the plugin does}}

---

## Architecture

**Plugin id:** `{{author}}.{{name}}`
**Language:** bash (preferred for portability)
**Config:** `$HERDR_PLUGIN_CONFIG_DIR/config.toml`

```
{{name}}/
├── herdr-plugin.toml
├── {{script1}}
├── {{script2}}
└── README.md
```

---

## Feature Breakdown

### Feature: {{name}}

**Tmux implementation:**

- Commands used:
- Keybindings:
- Configuration:
- Dependencies:

**Herdr implementation:**

- {{how it maps}}
- {{files affected}}

**User decisions needed:**

- {{any ambiguous mappings}}

---

## Non-portable Features

Features from the tmux plugin that cannot be replicated in Herdr:

| Feature | Reason | Suggested alternative |
|---------|--------|----------------------|
| {{feature}} | {{why}} | {{alternative}} |

---

## User Decisions

| # | Question | Options | Decision |
|---|----------|---------|----------|
| 1 | {{question}} | {{options}} | {{filled during review}} |
| 2 | {{question}} | {{options}} | {{filled during review}} |
