# Tools Guide

Complete reference for creating custom tools in OpenCode plugins using the `tool()` helper.

## The `tool()` Helper

Import from `@opencode-ai/plugin`:

```typescript
import { tool } from "@opencode-ai/plugin"
```

### Basic Structure

```typescript
export const MyPlugin: Plugin = async (ctx) => {
  return {
    tool: {
      toolname: tool({
        description: "What this tool does",
        args: {
          param1: tool.schema.string().describe("Description of param1"),
          param2: tool.schema.number().optional(),
        },
        async execute(args, context) {
          // args: validated and typed parameters
          // context: { agent, sessionID, messageID, directory, worktree }
          return "Result to return to the AI"
        },
      }),
    },
  }
}
```

**Important:** Filename determines tool name for standalone tools. For plugin tools, the key in `tool: {}` determines the name.

---

## Argument Validation with Zod

The `tool.schema` is Zod under the hood. You get full Zod validation:

### Common Types

```typescript
args: {
  // Strings
  name: tool.schema.string().describe("User name"),
  optionalStr: tool.schema.string().optional(),

  // Numbers
  count: tool.schema.number().describe("Item count"),
  port: tool.schema.number().int().min(1).max(65535),

  // Booleans
  force: tool.schema.boolean().default(false),

  // Enums
  mode: tool.schema.enum(["read", "write", "delete"]),

  // Arrays
  tags: tool.schema.array(tool.schema.string()),

  // Objects
  config: tool.schema.object({
    host: tool.schema.string(),
    port: tool.schema.number(),
  }),

  // Union types
  id: tool.schema.union([tool.schema.string(), tool.schema.number()]),
}
```

### Advanced Validation

```typescript
args: {
  email: tool.schema.string().email().describe("Must be valid email"),
  age: tool.schema.number().min(0).max(150).describe("Age in years"),
  url: tool.schema.string().url().describe("Must be valid URL"),
  tags: tool.schema.array(tool.schema.string()).min(1).describe("At least one tag"),
}
```

---

## Tool Context

The `execute` function receives a `context` object as the second argument:

```typescript
async execute(args, context) {
  const { agent, sessionID, messageID, directory, worktree } = context

  // Use directory for file operations
  const filePath = `${directory}/output.txt`

  // Use worktree for git operations
  await $`cd ${worktree} && git status`

  return `Running in ${directory}`
}
```

| Property | Type | Description |
|----------|------|-------------|
| `agent` | `string` | Current agent name |
| `sessionID` | `string` | Current session ID |
| `messageID` | `string` | Current message ID |
| `directory` | `string` | Session working directory |
| `worktree` | `string` | Git worktree root path |

---

## Return Values

Tools can return different types:

```typescript
// String (most common)
return "Operation completed successfully"

// Object (structured data)
return { success: true, data: [...] }

// Array
return [1, 2, 3]

// Null/undefined (no output)
return null
```

The return value is converted to a string representation that the AI sees.

---

## Multiple Tools in One Plugin

```typescript
export const MyPlugin: Plugin = async (ctx) => {
  return {
    tool: {
      add: tool({
        description: "Add two numbers",
        args: {
          a: tool.schema.number(),
          b: tool.schema.number(),
        },
        async execute(args) {
          return args.a + args.b
        },
      }),

      multiply: tool({
        description: "Multiply two numbers",
        args: {
          a: tool.schema.number(),
          b: tool.schema.number(),
        },
        async execute(args) {
          return args.a * args.b
        },
      }),

      // Tool that runs a shell command
      runCheck: tool({
        description: "Run a health check command",
        args: {
          command: tool.schema.string(),
        },
        async execute(args, ctx) {
          const result = await $(`${args.command}`).quiet()
          return result.text()
        },
      }),
    },
  }
}
```

---

## Tool Name Conflicts

**Rule:** If a custom tool uses the same name as a built-in tool, the **custom tool takes precedence**.

```typescript
// This replaces the built-in bash tool
export const MyPlugin: Plugin = async (ctx) => {
  return {
    tool: {
      bash: tool({
        description: "Restricted bash wrapper",
        args: { command: tool.schema.string() },
        async execute(args) {
          // Add logging, restrictions, etc.
          console.log(`Running: ${args.command}`)
          return `blocked: ${args.command}`
        },
      }),
    },
  }
}
```

**Best practice:** Use unique names unless intentionally replacing a built-in tool.

---

## Real-World Examples

### Example 1: Query Database (from plugin research)

```typescript
import { tool } from "@opencode-ai/plugin"
import path from "path"

export const MyPlugin: Plugin = async (ctx) => {
  return {
    tool: {
      db_query: tool({
        description: "Query the project database",
        args: {
          query: tool.schema.string().describe("SQL query to execute"),
        },
        async execute(args, context) {
          const script = path.join(context.worktree, "scripts/db-query.js")
          const result = await Bun.$`node ${script} ${args.query}`.text()
          return result.trim()
        },
      }),
    },
  }
}
```

### Example 2: Python Tool (from official docs)

```typescript
import { tool } from "@opencode-ai/plugin"
import path from "path"

export default tool({
  description: "Add two numbers using Python",
  args: {
    a: tool.schema.number().describe("First number"),
    b: tool.schema.number().describe("Second number"),
  },
  async execute(args, context) {
    const script = path.join(context.worktree, ".opencode/tools/add.py")
    const result = await Bun.$`python3 ${script} ${args.a} ${args.b}`.text()
    return result.trim()
  },
})
```

### Example 3: Using Shell Commands

```typescript
export const MyPlugin: Plugin = async ({ $ }) => {
  return {
    tool: {
      git_status: tool({
        description: "Get git status",
        args: {},
        async execute(_args, context) {
          const result = await $(`cd ${context.worktree} && git status --short`).text()
          return result || "Working tree clean"
        },
      }),
    },
  }
}
```

---

## Standalone Tools vs Plugin Tools

### Standalone Tool (in `.opencode/tools/` or `~/.config/opencode/tools/`)

```typescript
// File: .opencode/tools/my-tool.ts
import { tool } from "@opencode-ai/plugin"

export default tool({
  description: "...",
  args: { ... },
  async execute(args) { ... }
})
```

- Filename becomes tool name (`my-tool`)
- Auto-discovered by OpenCode
- Can use any language for the actual logic (via shell commands)

### Plugin Tool (inside a plugin's `tool:` block)

```typescript
// File: plugin/my-plugin.ts
export const MyPlugin: Plugin = async (ctx) => {
  return {
    tool: {
      toolName: tool({ ... }),  // Key determines name
    },
  }
}
```

- Key in `tool: {}` becomes tool name
- Only available when plugin is loaded
- Can access plugin state via closures

---

## Tool Errors

Throw errors to signal failure:

```typescript
async execute(args) {
  if (!isValid(args.input)) {
    throw new Error("Invalid input: must be non-empty string")
  }
  // ...
}
```

The error message is shown to the AI agent.

---

## Testing Your Tools

1. **Build the plugin:**
   ```bash
   bun build src/index.ts --outdir dist --target node --format esm
   ```

2. **Load in opencode.json:**
   ```json
   { "plugin": ["file:///path/to/your/plugin"] }
   ```

3. **Restart OpenCode completely**

4. **Test in conversation:**
   ```
   Can you use the mytool tool to...
   ```

5. **Check logs:**
   ```bash
   # OpenCode logs (depends on your setup)
   tail -f ~/.cache/opencode/logs/opencode.log
   ```
