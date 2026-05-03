# OpenCode Plugin Development Skill

A comprehensive skill for creating OpenCode plugins from scratch.

## What This Skill Provides

- **SKILL.md**: Step-by-step workflow for plugin development
- **references/plugin-anatomy.md**: Complete reference for plugin context, hooks, and lifecycle
- **references/tools-guide.md**: How to create custom tools with Zod validation
- **references/publishing.md**: npm publish, local testing, distribution
- **references/advanced-patterns.md**: Real patterns from popular plugins like oh-my-opencode-slim, opencode-skill-creator, opencode-remote-config

## Quick Start

1. **Create plugin structure**:
   ```bash
   mkdir -p my-plugin/src/{tools,skills,agents}
   cd my-plugin
   ```

2. **Copy templates** from `templates/`:
   - `package.json` → your plugin
   - `tsconfig.json` → your plugin
   - `basic-plugin.ts` or `plugin-with-tools.ts` → `src/index.ts`

3. **Install dependencies**:
   ```bash
   bun init -y
   bun add @opencode-ai/plugin
   ```

4. **Build and test**:
   ```bash
   bun build src/index.ts --outdir dist --target node --format esm
   ```

5. **Load in OpenCode** (see SKILL.md for details)

## Templates Included

| Template | Description |
|----------|-------------|
| `basic-plugin.ts` | Minimal plugin with event hooks |
| `plugin-with-tools.ts` | Plugin with custom tools (Zod validation) |
| `plugin-with-hooks.ts` | Tool interception (before/after) |
| `full-featured.ts` | All capabilities combined |
| `package.json` | npm package template |
| `tsconfig.json` | TypeScript configuration |

## Key Resources

- **Plugin Docs**: https://opencode.ai/docs/plugins/
- **@opencode-ai/plugin**: https://www.npmjs.com/package/@opencode-ai/plugin
- **Example Plugins**:
  - [oh-my-opencode-slim](https://github.com/alvinunreal/oh-my-opencode-slim)
  - [opencode-skill-creator](https://github.com/antongulin/opencode-skill-creator)
  - [opencode-plugin-template](https://github.com/zenobi-us/opencode-plugin-template)

## FAQ

**Q: Where do I put my plugin files?**
A: Global: `~/.config/opencode/plugin/` | Project: `.opencode/plugin/`

**Q: How do I test without publishing?**
A: Use `"file:///path/to/plugin"` in your `opencode.json` plugin array

**Q: Why isn't my plugin loading?**
A: Make sure to restart OpenCode completely (kill the process, not just new session)

**Q: Can I use Python/other languages in tools?**
A: Yes! Use `Bun.$` or `child_process.exec` to call scripts in any language
