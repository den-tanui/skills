import type { Plugin } from "@opencode-ai/plugin"
import { tool } from "@opencode-ai/plugin"

/**
 * Full-Featured OpenCode Plugin
 *
 * Demonstrates all major plugin capabilities:
 * - Custom tools with Zod validation
 * - Event hooks for session lifecycle
 * - Tool interception (before/after)
 * - Bundled skills and agents
 * - State management across sessions
 * - Compaction hook (experimental)
 */

// ---------------------------------------------------------------------------
// Session State Management
// ---------------------------------------------------------------------------

interface SessionState {
  filesModified: string[]
  toolsCalled: number
  customState: Record<string, unknown>
}

const sessionStore = new Map<string, SessionState>()

// ---------------------------------------------------------------------------
// Plugin Export
// ---------------------------------------------------------------------------

export const MyPlugin: Plugin = async (ctx) => {
  const { project, client, $, directory, worktree } = ctx

  console.log(`[my-plugin] Initialized in ${directory}`)
  console.log(`[my-plugin] Worktree: ${worktree}`)

  return {
    // -------------------------------------------
    // Custom Tools
    // -------------------------------------------
    tool: {
      // Tool 1: Analyze project
      analyze_project: tool({
        description: "Analyze the project structure and return a summary",
        args: {
          depth: tool.schema.number().int().min(1).max(5).default(2).describe("How deep to scan"),
        },
        async execute(args, context) {
          const { directory } = context
          try {
            const { readdirSync, statSync } = await import("fs")
            const { join } = await import("path")

            function scan(dir: string, currentDepth: number): string[] {
              if (currentDepth > args.depth) return []
              const entries: string[] = []
              try {
                for (const entry of readdirSync(dir)) {
                  const fullPath = join(dir, entry)
                  if (entry.startsWith(".") || entry === "node_modules") continue
                  const isDir = statSync(fullPath).isDirectory()
                  entries.push(isDir ? `${entry}/` : entry)
                  if (isDir) {
                    entries.push(...scan(fullPath, currentDepth + 1).map(e => `  ${e}`))
                  }
                }
              } catch {}
              return entries
            }

            const structure = scan(directory, 1)
            return `Project Structure (depth ${args.depth}):\n${structure.slice(0, 50).join("\n")}`
          } catch (err) {
            return `Error analyzing project: ${String(err)}`
          }
        },
      }),

      // Tool 2: Store custom state
      store_state: tool({
        description: "Store custom state for the current session",
        args: {
          key: tool.schema.string().describe("State key"),
          value: tool.schema.string().describe("State value"),
        },
        async execute(args, context) {
          const sessionId = (context as any).sessionID || (context as any).sessionId
          if (!sessionId) return "No session ID available"

          let state = sessionStore.get(sessionId)
          if (!state) {
            state = { filesModified: [], toolsCalled: 0, customState: {} }
            sessionStore.set(sessionId, state)
          }

          state.customState[args.key] = args.value
          return `Stored ${args.key} = ${args.value}`
        },
      }),

      // Tool 3: Retrieve state
      get_state: tool({
        description: "Retrieve stored state for the current session",
        args: {
          key: tool.schema.string().optional().describe("State key (omit to get all)"),
        },
        async execute(args, context) {
          const sessionId = (context as any).sessionID || (context as any).sessionId
          if (!sessionId) return "No session ID available"

          const state = sessionStore.get(sessionId)
          if (!state) return "No state stored for this session"

          if (args.key) {
            const val = state.customState[args.key]
            return val ? String(val) : `Key "${args.key}" not found`
          }

          return JSON.stringify(state.customState, null, 2) as any
        },
      }),
    },

    // -------------------------------------------
    // Session Events
    // -------------------------------------------
    event: async ({ event }) => {
      const sessionId = (event as any).sessionId || (event as any).session_id

      switch (event.type) {
        case "session.created":
          if (sessionId) {
            sessionStore.set(sessionId, {
              filesModified: [],
              toolsCalled: 0,
              customState: {},
            })
            console.log(`[my-plugin] Session ${sessionId} initialized`)
          }
          break

        case "session.idle":
          if (sessionId) {
            const state = sessionStore.get(sessionId)
            console.log(`[my-plugin] Session ${sessionId} idle. Tools called: ${state?.toolsCalled || 0}`)
          }
          break

        case "session.deleted":
          if (sessionId) {
            sessionStore.delete(sessionId)
            console.log(`[my-plugin] Session ${sessionId} cleaned up`)
          }
          break

        case "session.compacted":
          console.log(`[my-plugin] Session compacted, preserving state`)
          break
      }
    },

    // -------------------------------------------
    // Tool Execution Hooks
    // -------------------------------------------
    "tool.execute.before": async (input, output) => {
      const sessionId = input.sessionID || (input as any).sessionId

      // Track tool usage
      if (sessionId) {
        const state = sessionStore.get(sessionId)
        if (state) {
          state.toolsCalled++
        }
      }

      // Example: Log all bash commands
      if (input.tool === "bash") {
        console.log(`[my-plugin] Bash: ${output.args?.command?.slice(0, 100)}`)
      }

      // Example: Block dangerous operations
      if (input.tool === "write" || input.tool === "edit") {
        const filePath = output.args?.filePath || ""
        if (filePath.includes(".env") || filePath.includes("secrets")) {
          throw new Error("[my-plugin] Cannot modify sensitive files")
        }
      }
    },

    "tool.execute.after": async (input) => {
      // React to tool completion
      if (input.tool === "write" || input.tool === "edit") {
        const sessionId = input.sessionID || (input as any).sessionId
        if (sessionId) {
          const state = sessionStore.get(sessionId)
          if (state && input.args?.filePath) {
            state.filesModified.push(input.args.filePath as string)
          }
        }
      }
    },

    // -------------------------------------------
    // Compaction Hook (Experimental)
    // -------------------------------------------
    "experimental.session.compacting": async (input, output) => {
      // Inject custom context before compaction
      const sessionId = (input as any).sessionID || (input as any).sessionId
      if (!sessionId) return

      const state = sessionStore.get(sessionId)
      if (!state) return

      output.context.push(`
## Plugin State (${sessionId})
- Tools called: ${state.toolsCalled}
- Files modified: ${state.filesModified.length}
- Custom state keys: ${Object.keys(state.customState).join(", ") || "none"}
      `.trim())
    },
  }
}

export default MyPlugin
