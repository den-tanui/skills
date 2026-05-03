# Advanced Patterns from Popular Plugins

Real-world patterns extracted from well-known OpenCode plugins.

---

## Pattern 1: Agent Orchestration (oh-my-opencode-slim)

Managing multiple AI agents with specialized roles.

### Key Concepts

```typescript
// From oh-my-opencode-slim/src/agents/orchestrator.ts
import type { Plugin } from '@opencode-ai/plugin'

// Agent registry
const agents = {
  coder: { model: 'anthropic/claude-3-5-sonnet', tools: ['read', 'write', 'bash'] },
  reviewer: { model: 'anthropic/claude-3-5-haiku', tools: ['read', 'grep'] },
  tester: { model: 'anthropic/claude-3-5-sonnet', tools: ['bash', 'read'] },
}

// Multiplexer: route tasks to appropriate agent
export function getMultiplexer() {
  return {
    route: (task: string) => {
      if (task.includes('test')) return 'tester'
      if (task.includes('review')) return 'reviewer'
      return 'coder'
    }
  }
}
```

### Session State Management

```typescript
// Track state across a session
const sessionState = new Map<string, {
  filesModified: string[]
  tasksCompleted: number
  currentAgent: string
}>()

export const StatefulPlugin: Plugin = async (ctx) => {
  return {
    "session.created": async ({ session_id }) => {
      sessionState.set(session_id, {
        filesModified: [],
        tasksCompleted: 0,
        currentAgent: 'coder'
      })
    },

    "session.deleted": async ({ session_id }) => {
      sessionState.delete(session_id)
    },

    "tool.execute.after": async (input) => {
      const state = sessionState.get(input.sessionID)
      if (!state) return

      if (input.tool === 'write' || input.tool === 'edit') {
        state.filesModified.push(input.args?.filePath)
      }
    },

    event: async ({ event }) => {
      // React to events with access to session state
      if (event.type === 'session.idle') {
        const state = sessionState.get(event.session_id)
        console.log(`Session ${event.session_id}: ${state?.tasksCompleted} tasks done`)
      }
    }
  }
}
```

---

## Pattern 2: Tool Factory & Auto-Install (opencode-skill-creator)

Creating tools dynamically and auto-installing bundled assets.

### Tool Factory Pattern

```typescript
// From opencode-skill-creator/plugin/skill-creator.ts
import { tool } from "@opencode-ai/plugin"

function createTools({ ctx, config }) {
  const tools: Record<string, unknown> = {}

  // Conditionally add tools based on config
  if (config.enableEval) {
    tools.skill_eval = tool({
      description: "Test skill trigger accuracy",
      args: {
        evalSetPath: tool.schema.string(),
        skillPath: tool.schema.string(),
      },
      async execute(args) {
        return await runEval(args)
      }
    })
  }

  // Always add core tools
  tools.skill_validate = tool({
    description: "Validate SKILL.md structure",
    args: { skillPath: tool.schema.string() },
    async execute(args) {
      return validateSkill(args.skillPath)
    }
  })

  return tools
}
```

### Auto-Install Bundled Skills

```typescript
// From opencode-skill-creator — auto-install bundled skills to global dir
import { existsSync, mkdirSync, copyFileSync, readdirSync } from "fs"
import { join, dirname } from "path"
import { homedir } from "os"

function copyDirRecursive(src: string, dest: string): void {
  mkdirSync(dest, { recursive: true })
  for (const entry of readdirSync(src)) {
    const srcPath = join(src, entry)
    const destPath = join(dest, entry)
    if (statSync(srcPath).isDirectory()) {
      copyDirRecursive(srcPath, destPath)
    } else {
      copyFileSync(srcPath, destPath)
    }
  }
}

function ensureSkillInstalled(): void {
  const configDir = process.env.XDG_CONFIG_HOME || join(homedir(), ".config")
  const skillsDir = join(configDir, "opencode", "skills", "skill-creator")

  // Skip if already installed with same version
  const marker = join(skillsDir, "SKILL.md")
  if (existsSync(marker)) return

  // Copy bundled skills from plugin package
  const bundledDir = join(dirname(import.meta.path), "skill")
  if (!existsSync(bundledDir)) return

  copyDirRecursive(bundledDir, skillsDir)
}

export const MyPlugin: Plugin = async (ctx) => {
  // Auto-install on plugin load
  ensureSkillInstalled()

  return { /* hooks */ }
}
```

---

## Pattern 3: Command Hooks & Validation (opencode-command-hooks)

Run validations after tool execution.

```typescript
// From opencode-command-hooks
import { $ } from "bun"

export const CommandHooksPlugin: Plugin = async ({ client }) => {
  const argsCache = new Map()

  return {
    "tool.execute.before": async (input, output) => {
      // Cache args for later use in after hook
      if (input.tool === "task") {
        argsCache.set(input.callID, output.args)
      }
    },

    "tool.execute.after": async (input, output) => {
      if (!output && input.tool === "task") return

      const args = argsCache.get(input.callID)
      argsCache.delete(input.callID)

      // Only run for specific subagent types
      if (input.tool !== "task") return
      if (!["engineer", "debugger"].includes(args?.subagent_type)) return

      try {
        // Run validation commands sequentially
        const commands = ["npm run typecheck", "npm run lint"]
        let lastResult = { stdout: "", stderr: "" }

        for (const cmd of commands) {
          const result = await $`sh -c ${cmd}`.nothrow().quiet()
          lastResult = {
            stdout: result.stdout?.toString() || "",
            stderr: result.stderr?.toString() || "",
          }
        }

        // Truncate to match OpenCode's limit
        const truncate = (s: string) =>
          s.length > 30000 ? s.slice(0, 30000) + "\n[Output truncated]" : s

        // Inject results into session
        const message = `Validation (exit ${lastResult.stdout ? 0 : 1})\n${truncate(lastResult.stdout)}\n${truncate(lastResult.stderr)}`
        await client.session.promptAsync({
          path: { id: input.sessionID },
          body: {
            noReply: true,  // Don't trigger LLM response
            parts: [{ type: "text", text: message }],
          },
        })

        // Show toast notification
        await client.tui.showToast({
          body: {
            title: "Validation",
            message: "Completed",
            variant: "info",
          },
        })
      } catch (err) {
        console.error("Hook failed:", err)
      }
    },
  }
}
```

---

## Pattern 4: Self-Contained Plugins & Symlinks (opencode-remote-config)

How to structure plugins that get symlinked.

### The Rule: Self-Contained

```typescript
// ❌ WRONG — will fail when symlinked
import { helper } from "./utils"
import { config } from "../config"

// ✅ CORRECT — bundle inline or use npm
import { z } from "zod"
import type { Plugin } from "@opencode-ai/plugin"

// Bundle helper functions in the same file
function validateInput(input: unknown) {
  // ... implementation
}

export const MyPlugin: Plugin = async (ctx) => {
  // Use bundled helper
  validateInput(ctx)
  return { /* ... */ }
}
```

### Symlink Naming Convention

From `opencode-remote-config` — when your plugin installs remote plugins:

```typescript
// Remote plugins get _remote_ prefix
// plugin/notify.ts in repo my-hooks becomes:
//   ~/.config/opencode/plugin/_remote_my-hooks_notify.ts

function getSymlinkName(repoName: string, filePath: string): string {
  const baseName = filePath
    .replace(/^plugin\//, '')
    .replace(/\.ts$/, '')
    .replace(/\.js$/, '')
    .replace(/\//g, '-')

  return `_remote_${repoName}_${baseName}`
}
```

---

## Pattern 5: Compaction Hook with Context Injection

Preserve domain-specific context across compactions.

```typescript
export const DomainPlugin: Plugin = async (ctx) => {
  // Store domain context
  const domainContext = `
## Project-Specific Knowledge
- API endpoints: /api/v1/{resource}
- Always use the apiClient wrapper (never fetch directly)
- Database models are in src/models/
- Tests go in __tests__/ directory
`.trim()

  return {
    "experimental.session.compacting": async (input, output) => {
      // Add domain context to compaction
      output.context.push(domainContext)

      // OR replace the entire compaction prompt:
      // output.prompt = `Custom prompt with ${domainContext}`
    },
  }
}
```

---

## Pattern 6: Using the SDK Client

Common SDK operations from plugins.

```typescript
export const ClientPlugin: Plugin = async ({ client }) => {
  return {
    event: async ({ event }) => {
      if (event.type === "session.created") {
        // Log to OpenCode's app logger
        await client.app.log({
          body: {
            service: 'my-plugin',
            level: 'info',
            message: `Session ${event.session_id} started`
          }
        }).catch(() => {
          // Logger might be unavailable, fall back to stderr
          console.error(`[my-plugin] Session ${event.session_id} started`)
        })
      }
    },

    "tool.execute.after": async (input) => {
      if (input.tool === "some-tool") {
        // Show toast notification
        await client.tui.showToast({
          body: {
            title: "Task Complete",
            message: "The operation finished successfully",
            variant: "success"
          }
        }).catch(() => { /* UI might not be available */ })
      }
    }
  }
}
```

**Important:** Wrap SDK calls in try/catch — the client might be unavailable during certain phases.

---

## Pattern 7: Configuration Loading

Loading and merging plugin configuration.

```typescript
// From oh-my-opencode-slim/src/config/index.ts (simplified)
import { readFileSync } from "fs"
import { join } from "path"

interface PluginConfig {
  agents?: Record<string, unknown>
  tools?: boolean
  hooks?: boolean
}

function loadPluginConfig(directory: string): PluginConfig {
  const configPaths = [
    join(directory, ".opencode", "my-plugin.json"),
    join(process.env.HOME || "~", ".config", "opencode", "my-plugin.json")
  ]

  for (const configPath of configPaths) {
    try {
      const raw = readFileSync(configPath, "utf-8")
      return JSON.parse(raw) as PluginConfig
    } catch {
      // Config file doesn't exist, try next
    }
  }

  return {} // Default config
}

export const ConfigurablePlugin: Plugin = async (ctx) => {
  const config = loadPluginConfig(ctx.directory)

  return {
    // Use config values
    tool: config.tools ? { /* tools */ } : {},
    event: config.hooks ? async (events) => { /* hooks */ } : undefined,
  }
}
```

---

## Pattern 8: Multi-File Plugin Structure

How larger plugins organize their code.

```
my-big-plugin/
├── src/
│   ├── index.ts          # Entry point, assembles everything
│   ├── agents/          # Agent definitions
│   │   ├── index.ts
│   │   ├── coder.ts
│   │   └── reviewer.ts
│   ├── tools/           # Tool factories
│   │   ├── index.ts
│   │   ├── db-tool.ts
│   │   └── api-tool.ts
│   ├── hooks/           # Hook implementations
│   │   ├── index.ts
│   │   ├── session-hooks.ts
│   │   └── tool-hooks.ts
│   ├── config/          # Configuration loading
│   │   └── index.ts
│   └── utils/          # Shared utilities (bundled at build time)
│       └── index.ts
├── package.json
└── tsconfig.json
```

**Important:** When publishing to npm, bundle everything into a single file or ensure all imports resolve at runtime.

### Build for Distribution

```bash
# Bundle everything into dist/index.js
bun build src/index.ts \
  --outdir dist \
  --target node \
  --format esm \
  --external @opencode-ai/plugin \
  --external @opencode-ai/sdk
```

---

## Resources

- [oh-my-opencode-slim](https://github.com/alvinunreal/oh-my-opencode-slim) — Agent orchestration
- [opencode-skill-creator](https://github.com/antongulin/opencode-skill-creator) — Tool factory, auto-install
- [opencode-remote-config](https://github.com/jgordijn/opencode-remote-config) — Self-contained plugins
- [opencode-command-hooks](https://github.com/shanebishop1/opencode-command-hooks) — Tool interception
