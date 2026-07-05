# My Skills Index

This is an automatically generated index of all skills in this repository.

## Skills List

### [fzf](fzf/SKILL.md)

Comprehensive patterns and documentation for building advanced, interactive CLI tools using fzf in shell scripts. Updated description for testing.

### [fzf-advanced](fzf/skill-fzf/SKILL.md)

Advanced fzf patterns and techniques for building robust shell scripts with interactive selection.

### [fzf-advanced](fzf-advanced/SKILL.md)

Production-grade fzf patterns for robust, defensive shell scripts

### [fzf-to-bash-refactor](fzf-bash/SKILL.md)

Convert fzf workflows into portable Bash scripts using numbered menus and read input, removing TUI dependencies while maintaining functionality.

### [go-tui-architecture](go-tui-architecture/SKILL.md)

Scaffold a Go TUI application with clean layered architecture — Bubbletea + tview, config, persistence, plugin system, themes, and CI/CD. Use when starting a new Go TUI project, scaffolding a Bubbletea app, or creating a terminal UI with separation of concerns.

### [herdr](herdr-agent-skill/SKILL.md)

Control herdr from inside it. Manage workspaces and tabs, split panes, spawn agents, read output, and wait for state changes — all via CLI commands that talk to the running herdr instance over a local unix socket. Use when running inside herdr (HERDR_ENV=1).

### [herdr-cli](herdr-cli/SKILL.md)

Reference for the Herdr CLI — every command, flag, and output format. Use this skill whenever the user asks how to do something with the herdr command: construct a specific command invocation, control workspaces/tabs/panes/agents programmatically, script Herdr automation, parse JSON output, install or link plugins, understand available flags, or figure out the right command for a task. Also use when the user wants to pipe herdr output, filter workspace/pane/agent lists, invoke plugin actions from scripts, send keys or text to panes, create worktrees, wait for agent status, attach the terminal directly, or configure integrations. Do NOT use this skill for plugin development questions — that is the herdr-plugin-dev skill's domain.

### [herdr-plugin-dev](herdr-plugin-dev/SKILL.md)

Develop, modify, test, and publish Herdr plugins from scratch. Use this skill whenever the user wants to create a new Herdr plugin, add actions/events/panes/link handlers to an existing plugin, understand or write a herdr-plugin.toml manifest, build or test a plugin with `herdr plugin link`, debug plugin logs, troubleshoot plugin env vars or HERDR_BIN_PATH issues, learn how plugins call back into Herdr via the CLI or socket, or publish a plugin to the Herdr marketplace. Also use when asked about herdr-plugin.toml fields, plugin directory structure, plugin build commands, [[actions]]/[[events]]/[[panes]]/[[link_handlers]] manifest sections, or the HERDR_PLUGIN_* environment variables. Do NOT use this skill for general Herdr usage questions — that's the Herdr docs domain.

### [mcp-tui-test](mcp-tui-test/SKILL.md)

Test Terminal User Interface (TUI) applications programmatically using MCP. Like Playwright but for TUIs, supporting both stream mode for CLI tools and buffer mode for full TUI applications.

### [nuclei-template-generation](nuclei-skill/SKILL.md)

Use when creating, writing, or generating Nuclei YAML templates for CVE coverage, vulnerability detection, exposure detection, misconfiguration checks, or security scanning workflows

### [opencode-plugin-dev](opencode-plugin-dev/SKILL.md)

Guide for creating OpenCode plugins from scratch — scaffolding, implementing tools/hooks/events, bundling skills and agents, local testing, and publishing to npm. Use when the user asks to create a plugin, extend OpenCode, add custom tools/hooks, develop an extension, or mentions plugin development. Also trigger when users say "I want to build a plugin", "add custom tools to opencode", "create an opencode extension", or reference @opencode-ai/plugin.

### [skill-creator](.agents/skills/skill-creator/SKILL.md)

Create new skills, modify and improve existing skills, and measure skill performance. Use when users want to create a skill from scratch, edit, or optimize an existing skill, run evals to test a skill, benchmark skill performance with variance analysis, or optimize a skill's description for better triggering accuracy.

### [tmux-herdr-plugin](tmux-herdr-plugin/SKILL.md)

Port tmux plugins to Herdr plugins. Use this skill whenever the user wants to convert or port a tmux plugin to a Herdr plugin — given a tmux plugin GitHub URL or local path, analyze its features, keybindings, tmux commands, configuration options, and dependencies, then produce a spec document, implementation plan, and fully working Herdr plugin. Also use when the user asks how a specific tmux feature maps to Herdr, wants to understand what a tmux plugin does in Herdr terms, or wants to recreate a tmux workflow as a Herdr plugin. Do NOT use this skill for general Herdr plugin authoring — that is the herdr-plugin-dev skill's domain.

---

*Generated on 2026-07-05*

*Total skills: 13*
