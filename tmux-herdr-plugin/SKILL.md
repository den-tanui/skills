---
name: tmux-herdr-plugin
description: >-
  Port tmux plugins to Herdr plugins. Use this skill whenever the user wants to convert or port a
  tmux plugin to a Herdr plugin — given a tmux plugin GitHub URL or local path, analyze its
  features, keybindings, tmux commands, configuration options, and dependencies, then produce a
  spec document, implementation plan, and fully working Herdr plugin. Also use when the user asks
  how a specific tmux feature maps to Herdr, wants to understand what a tmux plugin does in Herdr
  terms, or wants to recreate a tmux workflow as a Herdr plugin. Do NOT use this skill for general
  Herdr plugin authoring — that is the herdr-plugin-dev skill's domain.
license: MIT
metadata:
  herdr_min_version: "0.7.0"
allowed-tools:
  - read
  - bash
  - write
  - edit
  - ast_grep_search
  - ast_grep_dump
  - web_fetch
  - web_search
  - ask_user_question
  - Agent
  - todo
---

# Tmux → Herdr Plugin Porting

A structured workflow for porting tmux plugins to Herdr plugins. The skill reads a tmux plugin,
analyzes every tmux command and feature it uses, maps each to Herdr equivalents, consults you on
ambiguous mappings, produces a spec, plans the implementation, and builds the Herdr plugin.

---

## Workflow Overview

```
1. INGEST  ──► 2. ANALYZE  ──► 3. SPEC  ──► 4. REVIEW  ──► 5. PLAN  ──► 6. IMPLEMENT
                   │                              │
                   └─► flag ambiguous mappings     └─► you approve / request changes
```

Each step produces output before the next begins. You can request changes at the spec and plan
stages. The workflow is sequential — no step is skipped.

---

## Step 1: Ingest

Given a tmux plugin (GitHub URL or local path):

### If GitHub URL (`owner/repo` or `https://github.com/owner/repo`)

```bash
# Clone to a temp directory
git clone --depth 1 https://github.com/owner/repo /tmp/tmux-port-<name>
cd /tmp/tmux-port-<name>
```

### If local path

Verify the path exists and is a directory containing a tmux plugin
(has `*.tmux` scripts, `scripts/` directory, or a `tmux` plugin file).

### List files and assess complexity

```bash
find /tmp/tmux-port-<name> -type f | head -50
```

**Simple plugin** (≤5 files, all bash/shell): read every file fully.  
**Complex plugin** (multiple languages, many files): read the entry point and key scripts, then
use `ag` (ast-grep CLI) for semantic code search across the codebase. Check if it's installed
and understand the pattern syntax first:

### ast-grep metavariable syntax

| Syntax | Matches | Named? |
|--------|---------|--------|
| `$X` | single AST node | yes — captures the value |
| `$$$` | zero or more nodes | no — unnamed wildcard |
| `$$$NAME` | zero or more nodes | yes — captures the list |

Patterns match code structure, not text. `$X` matches any single expression;
`$$$` matches everything between known parts. Results show captures below each match.

### Check and use ast-grep

```bash
# Check if ast-grep is installed (binary: ag or ast-grep)
if command -v ag >/dev/null 2>&1; then
  AG=ag
elif command -v ast-grep >/dev/null 2>&1; then
  AG=ast-grep
else
  echo "ast-grep not installed, falling back to grep"
  AG=
fi

# --- Bash plugins ---

# Find all tmux command invocations
if [ -n "$AG" ]; then
  # tmux followed by any arguments
  "$AG" run -p 'tmux $$$ARGS' --lang bash /tmp/tmux-port-<name>

  # run-shell calls (tmux plugin pattern)
  "$AG" run -p 'run-shell $$$ARGS' --lang bash /tmp/tmux-port-<name>

  # if-shell condition + command
  "$AG" run -p 'if-shell $$$ARGS' --lang bash /tmp/tmux-port-<name>

  # display-popup / display-menu
  "$AG" run -p 'display-popup $$$ARGS' --lang bash /tmp/tmux-port-<name>
  "$AG" run -p 'display-menu $$$ARGS' --lang bash /tmp/tmux-port-<name>

  # bind-key / unbind-key
  "$AG" run -p 'bind-key $$$ARGS' --lang bash /tmp/tmux-port-<name>
  "$AG" run -p 'unbind-key $$$ARGS' --lang bash /tmp/tmux-port-<name>

  # Plugin option patterns (@-variables)
  "$AG" run -p 'set $$$ARGS @' --lang bash /tmp/tmux-port-<name>

  # Variable assignments (for env vars, config)
  "$AG" run -p '$X="$$$VALUE"' --lang bash /tmp/tmux-port-<name>
else
  # fallback: text grep
  grep -rn 'tmux' /tmp/tmux-port-<name> --include='*.sh' --include='*.tmux' --include='*.bash'
fi
```

### Non-bash plugins

Adjust `--lang` for the plugin's language:

```bash
# Python: subprocess.run or os.system tmux calls
"$AG" run -p 'tmux $$$ARGS' --lang python /tmp/tmux-port-<name>
"$AG" run -p 'subprocess$$$ARGS' --lang python /tmp/tmux-port-<name>

# TypeScript/JavaScript: tmux through execa/child_process
"$AG" run -p '"tmux"$$$ARGS' --lang typescript /tmp/tmux-port-<name>
"$AG" run -p 'execa($$$ARGS)' --lang typescript /tmp/tmux-port-<name>

# Go: exec.Command or shell invocations
"$AG" run -p 'exec.Command($$$ARGS)' --lang go /tmp/tmux-port-<name>

# Ruby: system() or backtick calls
"$AG" run -p '`tmux $$$ARGS`' --lang ruby /tmp/tmux-port-<name>
"$AG" run -p 'system($$$ARGS)' --lang ruby /tmp/tmux-port-<name>
```

### Debugging zero matches

If an `ag` pattern returns nothing, the AST structure may differ from what you expected:

```bash
# 1. Dump the AST for a small snippet to find correct node kinds
"$AG" dump --lang bash 'tmux bind-key -n M-f run-shell "script"'

# 2. Simplify the pattern and retry
"$AG" run -p 'tmux $$$' --lang bash /tmp/tmux-port-<name>

# 3. If still nothing, use strictness: relaxed (ignores punctuation like trailing semicolons)
"$AG" run -p 'tmux $$$ARGS' --lang bash --strictness relaxed /tmp/tmux-port-<name>

# 4. Final fallback: plain grep
```

### Scoping to specific files

Pass file paths directly instead of a directory to narrow results:

```bash
"$AG" run -p 'tmux $$$ARGS' --lang bash /tmp/tmux-port-<name>/scripts/*.sh
"$AG" run -p 'bind-key $$$ARGS' --lang bash /tmp/tmux-port-<name>/*.tmux
```

Also extract sourced files, plugin options (patterns like `@plugin-name-*`), and
environment variables.

Also extract sourced files, plugin options (patterns like `@plugin-name-*`), and
environment variables.

### Record

Save analysis to a working file:

```
/tmp/tmux-port-<name>/_analysis.json
```

Fields captured:

- `files: []` — every file and its role
- `tmux_commands: []` — every tmux subcommand invoked with args
- `keybindings: []` — bind-key / unbind-key calls
- `options: []` — plugin options (@-variables, env vars, config)
- `dependencies: []` — external tools (fzf, git, gh, jq, etc.)
- `features: []` — high-level features the plugin provides

---

## Step 2: Analyze — Map Concepts

For each feature and command in the analysis, determine the Herdr equivalent.

### Tmux → Herdr Mapping Reference

| Tmux | Herdr Equivalent | Notes |
|------|-----------------|-------|
| `display-popup` | `[[panes]] placement = overlay\|split\|tab` | **Ambiguous** — ask user |
| `display-menu` | fzf picker in overlay pane | fzf is the standard choice |
| `display-message` | `herdr notification show` | Uses configured toast delivery |
| `split-window -h` | `herdr pane split --direction right` | |
| `split-window -v` | `herdr pane split --direction down` | |
| `new-window` | `herdr tab create` | |
| `new-session` | `herdr workspace create` | |
| `send-keys` | `herdr pane send-keys` | Key syntax differs |
| `send-keys -X` | `herdr pane send-keys` with key names | Map tmux key names to herdr |
| `capture-pane -p` | `herdr pane read --source recent-unwrapped` | |
| `run-shell` | `[[actions]]` or action script | |
| `bind-key` | `[[keys.command]]` in herdr `config.toml` | Or `plugin_action` type |
| `unbind-key` | Omit or override in herdr config | |
| `set-environment` | Env var in script or `--env` flag | |
| `set -g @option` | Config file in `$HERDR_PLUGIN_CONFIG_DIR/config.toml` | |
| `set -g status-*` | Herdr `[theme]` or `[ui]` config | Note as non-portable |
| `if-shell` | Bash conditional in plugin script | |
| `command-prompt` | `read -p` or fzf prompt | |
| `confirm-before` | `read -n1 -p` confirmation | |
| `wait-for` | `herdr wait output` or `herdr wait agent-status` | |
| `has-session` | `herdr workspace list` + grep | |
| `switch-client` | `herdr workspace focus` | |
| `respawn-pane` | `herdr pane run` | |
| `respawn-window` | Close tab + recreate | Not a direct equivalent |
| `select-pane` | `herdr pane focus` | |
| `select-layout` | `herdr pane layout` | |
| `resize-pane` | `herdr pane resize --amount` | |
| `swap-pane` | `herdr pane swap` | |
| `move-pane` | `herdr pane move` | |
| `kill-pane` | `herdr pane close` | |
| `list-*` | `herdr * list` | Same pattern |
| `copy-mode` | `herdr pane read` | Read, not enter mode |
| `paste-buffer` | `herdr pane send-text` | |
| `load-buffer` | Read file + `herdr pane send-text` | |
| `save-buffer` | `herdr pane read > file` | |
| `choose-tree` | Workspace/tab picker via fzf | |
| `choose-client` | Not applicable in herdr | Single-client model |
| `refresh-client` | `herdr server reload-config` | |
| `source-file` | `herdr plugin link` or config include | |

### Key mapping notes

**popup (display-popup):** Tmux opens a floating terminal at a specific position/size.
Herdr has no floating popup — use `overlay` (full terminal, restores focus) or `split`/`tab`.
**Ask the user** which placement they want for each popup.

**menu (display-menu):** Tmux shows a menu overlay at the cursor. Herdr has no menu primitive.
Map to an fzf picker in an overlay pane. For simple menus (2-3 items), map to multiple actions.

**status bar (status-* options):** Tmux status bar is a core UI feature. Herdr has its own
sidebar/status. Note these as non-portable and suggest herdr equivalents where they exist.

**keybindings:** Tmux `bind-key` uses `prefix + key`. Herdr uses the same `prefix+key` syntax in
`config.toml`. Map directly but adjust for conflicts with herdr defaults.

**plugin options (@-variables):** Tmux plugins use `@plugin-option` namespaced variables.
Map to `config.toml` values under `$HERDR_PLUGIN_CONFIG_DIR/config.toml`.

### Flag ambiguous mappings

When a tmux feature has multiple plausible Herdr mappings, **do not guess**. Note it in the
analysis and present it to the user during the spec review. Examples:

- `display-popup` → overlay, split, or tab?
- `display-menu` → fzf picker, multiple actions, or something else?
- `command-prompt` → fzf, `read`, or argparse?
- Plugin keybindings that conflict with herdr defaults

---

## Step 3: Generate Spec Document

Write a spec document to a file. Use the following structure:

```markdown
# <Plugin Name> — Herdr Port Specification

## Source
- **Tmux plugin:** <URL or path>
- **Analysis date:** <date>

## Overview
<2-3 sentence summary of what the plugin does>

## Architecture
<How the Herdr plugin will be structured — manifest layout, scripts, config>

## Feature Breakdown

### Feature: <name>
**Tmux implementation:** <how it works in tmux>
**Herdr implementation:** <how it will work in herdr>
**Files affected:** <which plugin files this touches>
**User decisions needed:** <any ambiguous mappings for this feature>

### Feature: <name>
...
```

### Include for each feature

- What the feature does (from tmux perspective)
- How it's implemented in tmux (commands, keybindings, options)
- How it maps to Herdr (pane, action, event, config, etc.)
- Any implementation complexity notes
- Whether user input is needed for the mapping

### Save location

Save to the tmux plugin clone directory:

```
/tmp/tmux-port-<name>/SPEC.md
```

### Present to the user

Summarize the spec briefly (3-5 bullet points), then highlight any ambiguous mappings
that need their decision. Ask specifically:
> "The spec is at /tmp/tmux-port-<name>/SPEC.md. Here's what needs your input:
>
> 1. [ambiguous mapping 1] — options: A, B, C
> 2. [ambiguous mapping 2] — options: A, B
>
> Once you've read the spec and made your decisions, let me know and I'll create the
> implementation plan."

---

## Step 4: User Review

Wait for the user to:

1. Read the spec
2. Make decisions on flagged items
3. Request any changes

Update the spec with their decisions. If they request major changes, re-present.

---

## Step 5: Create Implementation Plan

Based on the approved spec, create a phased implementation plan:

```markdown
# Implementation Plan: <Plugin Name>

## Phase 1: Scaffold
- [ ] Create plugin directory
- [ ] Write herdr-plugin.toml
- [ ] Create config parser script

## Phase 2: Core Features
- [ ] Implement feature X
- [ ] Implement feature Y

## Phase 3: Keybindings & Polish
- [ ] Document keybinding suggestions
- [ ] Write README
```

Present the plan to the user and wait for approval before implementing.

---

## Step 6: Implement

Create the Herdr plugin in the specified location.

### Directory structure

```
<output-dir>/<plugin-name>/
├── herdr-plugin.toml
├── <scripts...>
├── README.md
└── (optional) config.toml.example
```

### What to generate

1. **`herdr-plugin.toml`** — manifest with actions, panes, events, link handlers
2. **Script files** — bash (preferred for portability) or appropriate language
3. **Config file** — if the plugin has options
4. **README.md** — install, usage, keybindings, config reference

### After implementation

```bash
# Test with herdr plugin link
herdr plugin link <output-dir>/<plugin-name>
herdr plugin action list --plugin <plugin-id>
```

Commit the plugin if it's in a git repo.

---

## Gotchas

- **`display-popup` has no direct equivalent**: Tmux popups float at a position/size.
  Herdr overlays cover the full terminal. Always ask the user what placement they prefer.
  If they want partial-terminal popups, mention that's not possible in plugin v1 and
  suggest overlay as the closest option.

- **Menus are not a Herdr primitive**: Tmux menus (`display-menu`) appear at the cursor.
  Herdr has no equivalent. Fzf in an overlay pane is the standard replacement. For very
  simple menus (2-3 choices), separate actions bound to different keys may be cleaner.

- **Status bar is not portable**: Tmux's `status-*` options have no Herdr equivalent.
  Herdr's sidebar and agent panel serve a different purpose. Note features that rely on
  status bar display as non-portable and suggest alternatives (notifications, pane labels,
  or a dedicated pane).

- **Keybinding conflicts**: Herdr has its own default keybindings (`prefix+c` = new tab,
  `prefix+v` = split, etc.). When porting tmux bindings, check against herdr defaults
  and either override (if the user wants) or suggest alternative keys.

- **Tmux `-l` (live) flag on popups**: Herdr overlays don't support a "live" streaming
  mode in the same way. Determine if the live feature is essential or if a static view
  works.

- **Shell command parsing**: Tmux plugins often embed complex shell commands in
  `run-shell`, `if-shell`, or `bind-key` arguments. Parse these carefully — they may
  need to be extracted into separate script files for the Herdr plugin.

- **Tmux environment variables**: `$TMUX_PANE`, `$TMUX_SESSION_ID`, etc. have no Herdr
  equivalents. Map to `HERDR_PANE_ID`, `HERDR_WORKSPACE_ID`, etc. Create a reference
  table in the spec for every tmux env var the plugin uses.

- **Plugin version detection**: Tmux plugins often check `tmux -V` for feature gates.
  For Herdr, use `herdr --version` or `min_herdr_version` in the manifest.

- **AST parsing for complex plugins**: If the tmux plugin is written in a compiled
  language or uses complex code generation, use `ast_grep_search` with appropriate
  language patterns to extract the tmux commands embedded in the source.
