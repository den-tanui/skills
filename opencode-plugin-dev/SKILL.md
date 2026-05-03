---
name: opencode-plugin-dev
description: >
  Guide for creating OpenCode plugins from scratch — scaffolding, implementing tools/hooks/events,
  bundling skills and agents, local testing, and publishing to npm. Use when the user asks to
  create a plugin, extend OpenCode, add custom tools/hooks, develop an extension, or mentions
  plugin development. Also trigger when users say "I want to build a plugin", "add custom
  tools to opencode", "create an opencode extension", or reference @opencode-ai/plugin.
---

# OpenCode Plugin Development Skill

You are helping the user create an OpenCode plugin. Follow this workflow and reference the
supporting documents as needed.

## Workflow

1. **Clarify intent** — What should the plugin do?
   - Custom tools? Event hooks? Tool interception? Bundled skills/agents?
   - Read `references/plugin-anatomy.md` for the full capability map

2. **Scaffold the plugin** — Create the directory structure
   - Use `templates/package.json` as a starting point
   - Set up `tsconfig.json` and `src/index.ts`
   - See "Scaffolding" section below

3. **Implement core functionality**
   - **Tools**: See `references/tools-guide.md` and `templates/plugin-with-tools.ts`
   - **Hooks**: See `references/plugin-anatomy.md` (Events section) and `templates/plugin-with-hooks.ts`
   - **Skills/Agents**: Bundle in `src/skills/` and `src/agents/` directories

4. **Test locally** — Load the plugin without publishing
   - Add to `~/.config/opencode/opencode.json`:
     ```json
     { "plugin": ["file:///path/to/your/plugin"] }
     ```
   - Restart OpenCode completely (kill + restart, not just new session)

5. **Iterate and debug**
   - Check OpenCode logs for plugin loading errors
   - Use `console.log` in your plugin (appears in OpenCode's stderr)
   - Verify tools appear in the agent's toolkit

6. **Publish (optional)** — Share with others
   - See `references/publishing.md` for npm publish steps
   - Users install with: `opencode plugin your-plugin@latest --global`

---

## Scaffolding

Create this directory structure:

```
my-plugin/
├── src/
│   ├── index.ts          # Plugin entry point
│   ├── tools/            # Custom tools (optional)
│   ├── skills/           # Bundled skills (optional)
│   │   └── my-skill/SKILL.md
│   └── agents/           # Bundled agents (optional)
│       └── my-agent.md
├── package.json          # Dependencies: @opencode-ai/plugin
├── tsconfig.json        # TypeScript configuration
└── README.md            # Documentation
```

### Minimal package.json

Copy from `templates/package.json` and modify:
- `name`: kebab-case, preferably with `opencode-` prefix
- `description`: Clear one-liner
- `main`: Points to `dist/index.js`

### TypeScript Config

```json
{
  "compilerOptions": {
    "target": "ESNext",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "outDir": "dist",
    "rootDir": "src"
  },
  "include": ["src/**/*"]
}
```

---

## Quick Examples

### Minimal Plugin (from `templates/basic-plugin.ts`)

```typescript
import type { Plugin } from "@opencode-ai/plugin"

export const MyPlugin: Plugin = async ({ project, client, $, directory, worktree }) => {
  console.log("Plugin initialized!")

  return {
    // Hook implementations go here
    event: async ({ event }) => {
      console.log("Event:", event.type)
    }
  }
}
```

### Adding Custom Tools (from `templates/plugin-with-tools.ts`)

```typescript
import { type Plugin, tool } from "@opencode-ai/plugin"

export const MyPlugin: Plugin = async (ctx) => {
  return {
    tool: {
      mytool: tool({
        description: "What my tool does",
        args: {
          param1: tool.schema.string().describe("Parameter description"),
          param2: tool.schema.number().optional(),
        },
        async execute(args, context) {
          const { directory, worktree } = context
          return `Processed: ${args.param1}`
        },
      }),
    },
  }
}
```

### Intercepting Tool Calls (from `templates/plugin-with-hooks.ts`)

```typescript
export const MyPlugin: Plugin = async (ctx) => {
  return {
    "tool.execute.before": async (input, output) => {
      // Block or modify tool calls before they execute
      if (input.tool === "read" && input.args.filePath.includes(".env")) {
        throw new Error("Do not read .env files")
      }
    },
    "tool.execute.after": async (input, output) => {
      // React to tool execution results
      console.log(`Tool ${input.tool} completed`)
    },
  }
}
```

---

## Advanced Patterns

For complex plugins with multiple tools, agents, or orchestration, see:
- `references/advanced-patterns.md` — Real patterns from popular plugins
- `templates/full-featured.ts` — Complete example with tools + hooks + skills

### Key Plugins to Study

| Plugin | What It Does | Key Pattern |
|--------|---------------|-------------|
| [oh-my-opencode-slim](https://github.com/alvinunreal/oh-my-opencode-slim) | Agent orchestration | Multiplexer, council manager, session state |
| [opencode-skill-creator](https://github.com/antongulin/opencode-skill-creator) | Skill development | Tool factory, auto-install bundled skills |
| [opencode-remote-config](https://github.com/jgordijn/opencode-remote-config) | Git-sync skills/agents | Self-contained plugins, symlink naming |
| [opencode-command-hooks](https://github.com/shanebishop1/opencode-command-hooks) | Command hooks | `tool.execute.after` for validation |

---

## Troubleshooting

**Plugin not loading:**
- Check file is in `~/.config/opencode/plugin/` or `.opencode/plugin/`
- Ensure file extension is `.ts` or `.js`
- Restart OpenCode completely (not just new session)

**"Cannot find module @opencode-ai/plugin":**
- Add `package.json` to your config directory with the dependency
- OpenCode runs `bun install` at startup

**Tools not appearing:**
- Verify you're exporting a named const (not default export)
- Check the plugin loaded (look for console.log output)
- Restart OpenCode after changes

**Import errors in plugins:**
- Plugins must be self-contained (no local `./utils` imports)
- Bundle dependencies or use npm packages
- For `opencode-remote-config` pattern: each file is loaded individually

---

## References

- **Plugin Anatomy**: `references/plugin-anatomy.md` — Context object, all hooks, load order
- **Tools Guide**: `references/tools-guide.md` — tool() helper, Zod schemas, context args
- **Publishing**: `references/publishing.md` — npm publish, local testing, file:// protocol
- **Advanced Patterns**: `references/advanced-patterns.md` — Real code from popular plugins
