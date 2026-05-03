# Plugin Anatomy Reference

Complete reference for OpenCode plugin structure, context object, hooks, and lifecycle.

## Plugin Context Object

Every plugin function receives a `context` object (destructure it to access properties):

```typescript
export const MyPlugin: Plugin = async (ctx) => {
  // Destructure what you need
  const { project, client, $, directory, worktree, serverUrl } = ctx
  // ...
}
```

### Context Properties

| Property | Type | Description |
|----------|------|-------------|
| `project` | `Project` | Current project info (name, path, etc.) |
| `directory` | `string` | Current working directory |
| `worktree` | `string` | Git worktree path (for git operations) |
| `client` | `OpencodeClient` | SDK client for AI interaction, session management |
| `$` | `BunShell` | Bun's shell API for executing commands |
| `serverUrl` | `URL` | OpenCode server URL (e.g., `http://localhost:4096`) |

### Using the SDK Client

```typescript
// Send a message to the session
await client.session.prompt({
  path: { id: sessionID },
  body: { parts: [{ type: "text", text: "Hello!" }] },
})

// Log to OpenCode's app logger
await client.app.log({
  body: { service: 'my-plugin', level: 'info', message: '...' }
})

// Show TUI toast notification
await client.tui.showToast({
  body: { title: "Done", message: "Task completed", variant: "success" }
})
```

---

## Plugin Load Order

OpenCode loads plugins in this order (all hooks run in sequence):

1. **Global config** (`~/.config/opencode/opencode.json`)
2. **Project config** (`opencode.json` in project root)
3. **Global plugin directory** (`~/.config/opencode/plugin/`)
4. **Project plugin directory** (`.opencode/plugin/`)

### Duplicate Handling

- Same npm package with same version → loaded once
- Local + npm plugin with same name → loaded separately
- Identical exports from same module → initialized once

---

## Available Hooks

### Session Events

| Event | When It Fires | Input Object |
|-------|----------------|-------------|
| `session.created` | New session starts | `{ type, session_id, ... }` |
| `session.updated` | Session metadata changes | `{ type, session_id, ... }` |
| `session.deleted` | Session removed | `{ type, session_id }` |
| `session.idle` | Session completed/session idle | `{ type, session_id }` |
| `session.compacted` | Context was compacted | `{ type, session_id }` |
| `session.error` | Session error occurred | `{ type, session_id, error }` |
| `session.status` | Status change | `{ type, session_id, status }` |
| `session.diff` | Diff available | `{ type, session_id, diff }` |

### Tool Events

```typescript
export const MyPlugin: Plugin = async (ctx) => {
  return {
    "tool.execute.before": async (input, output) => {
      // input: { tool, args, sessionID, callID }
      // output: mutable copy of args (modify to change tool behavior)
      // Throw error to block tool execution

      if (input.tool === "bash") {
        // Modify command before execution
        output.args.command = `echo "Running: ${output.args.command}" && ${output.args.command}`
      }
    },

    "tool.execute.after": async (input) => {
      // input: { tool, args, sessionID, callID }
      // Tool has already executed
      // Use this to react to tool results, inject messages, etc.

      if (input.tool === "task") {
        // Task completed, maybe inject follow-up
      }
    },
  }
}
```

### File Events

| Event | Description |
|-------|-------------|
| `file.edited` | File was modified |
| `file.watcher.updated` | File watcher detected changes |

### Message Events

Events related to chat messages and AI responses.

### Permission Events

| Event | Description |
|-------|-------------|
| `permission.replied` | User responded to permission prompt |
| `permission.updated` | Permission state changed |

### TUI Events

| Event | Description |
|-------|-------------|
| `tui.append` | Content appended to TUI |
| `tui.command.execute` | TUI command executed |

### Server Events

| Event | Description |
|-------|-------------|
| `server.connected` | Connected to OpenCode server |

### Todo Events

| Event | Description |
|-------|-------------|
| `todo.updated` | Todo list changed |

---

## Compaction Hook (Experimental)

Control how OpenCode compacts context when it gets too long:

```typescript
export const MyPlugin: Plugin = async (ctx) => {
  return {
    "experimental.session.compacting": async (input, output) => {
      // input: { messages, summary } (current state)
      // output: { context: string[], prompt: string }

      // Add domain-specific context before compaction
      output.context.push(`
## Project-Specific Notes
- Always use TypeScript strict mode
- All API calls go through the apiClient wrapper
      `.trim())

      // OR replace the entire compaction prompt:
      // output.prompt = "Custom compaction instructions..."
    },
  }
}
```

**Note:** When `output.prompt` is set, it replaces the default compaction prompt entirely.
The `output.context` array is ignored in that case.

---

## Custom Tools

Register tools that the AI agent can call. See `references/tools-guide.md` for full details.

Quick example:

```typescript
import { tool } from "@opencode-ai/plugin"

export const MyPlugin: Plugin = async (ctx) => {
  return {
    tool: {
      mytool: tool({
        description: "What this tool does",
        args: {
          param: tool.schema.string().describe("Parameter description"),
        },
        async execute(args, context) {
          // context has: agent, sessionID, messageID, directory, worktree
          return `Result: ${args.param}`
        },
      }),
    },
  }
}
```

---

## Plugin Return Interface

```typescript
interface PluginInterface {
  config?: ConfigHandler              // Control config loading/merging
  tool?: ToolsRecord                    // Custom tools
  "chat.message"?: ChatMessageHandler  // First-message setup
  "chat.params"?: ChatParamsHandler    // Adjust model parameters
  event?: EventHandler                 // Session lifecycle events
  "tool.execute.before"?: ToolExecuteBeforeHandler  // Pre-tool guard
  "tool.execute.after"?: ToolExecuteAfterHandler   // Post-tool hook
  "experimental.chat.messages.transform"?: TransformHandler  // Message transform
  "experimental.session.compacting"?: CompactionHandler  // Context compaction
}
```

---

## Self-Contained Requirement

**Critical:** Plugin files loaded from `plugin/` directories must be self-contained:

```typescript
// ❌ WRONG - local imports will fail
import { helper } from "./utils"
import { config } from "../config"

// ✅ CORRECT - use npm packages or bundle inline
import { z } from "zod"
import type { Plugin } from "@opencode-ai/plugin"

// Or bundle the code directly in the same file
function helper() { /* ... */ }
```

**Why?** OpenCode loads plugin files individually via symlinks. A file importing `./utils.ts` won't have access to that file.

**Solution:** Use npm packages (declare in `package.json`) or bundle code inline.

---

## Directory Locations

| Location | Scope | Purpose |
|----------|-------|---------|
| `~/.config/opencode/plugin/` | Global | Plugins available in all projects |
| `.opencode/plugin/` | Project | Project-specific plugins |
| `src/skills/*/SKILL.md` | Bundled | Skills shipped with your plugin |
| `src/agents/*.md` | Bundled | Agents shipped with your plugin |

Skills and agents in your npm package are auto-discovered. No configuration needed.

Commands (`.opencode/commands/*.md`) are NOT auto-discovered from npm packages.
They must be copied to `.opencode/commands/` manually or via setup script.
