import type { Plugin } from "@opencode-ai/plugin"

/**
 * Plugin with Hooks
 *
 * Demonstrates tool interception hooks (before/after execution)
 * and event handling.
 */

export const MyPlugin: Plugin = async ({ client, $, directory }) => {
  console.log(`[my-plugin] Loaded with hooks in ${directory}`)

  // State tracking (survives across hook calls)
  const toolCallCount = new Map<string, number>()

  return {
    // -------------------------------------------
    // Tool Execution Hooks
    // -------------------------------------------

    // Fires BEFORE a tool executes
    "tool.execute.before": async (input, output) => {
      // input: { tool, args, sessionID, callID }
      // output: mutable copy of args (modify to change behavior)
      // Throw error to BLOCK execution

      console.log(`[my-plugin] Before: ${input.tool}`)

      // Track call counts
      const count = (toolCallCount.get(input.tool) || 0) + 1
      toolCallCount.set(input.tool, count)

      // Example: Block .env file reads
      if (input.tool === "read" && output.args?.filePath?.includes(".env")) {
        throw new Error("[my-plugin] Reading .env files is not allowed")
      }

      // Example: Modify bash commands
      if (input.tool === "bash") {
        const cmd = output.args?.command || ""
        // Log the command
        console.log(`[my-plugin] Executing: ${cmd}`)
        // Could modify: output.args.command = `echo "Running..." && ${cmd}`
      }

      // Example: Validate edit operations
      if (input.tool === "edit") {
        const filePath = output.args?.filePath || ""
        if (filePath.includes("node_modules") || filePath.includes(".git")) {
          throw new Error(`[my-plugin] Cannot edit ${filePath}`)
        }
      }
    },

    // Fires AFTER a tool executes
    "tool.execute.after": async (input) => {
      // input: { tool, args, sessionID, callID }
      // Tool has already executed

      console.log(`[my-plugin] After: ${input.tool} (call #${toolCallCount.get(input.tool)})`)

      // Example: React to bash results
      if (input.tool === "bash") {
        // Could analyze output, trigger follow-up actions, etc.
      }

      // Example: Track file modifications
      if (input.tool === "write" || input.tool === "edit") {
        const filePath = input.args?.filePath
        if (filePath) {
          console.log(`[my-plugin] File modified: ${filePath}`)
        }
      }
    },

    // -------------------------------------------
    // Session Events
    // -------------------------------------------
    event: async ({ event }) => {
      switch (event.type) {
        case "session.created":
          console.log(`[my-plugin] Session ${(event as any).sessionId || (event as any).session_id} started`)
          break

        case "session.idle":
          console.log(`[my-plugin] Session ${(event as any).sessionId || (event as any).session_id} completed`)
          // Could send notification, update external systems, etc.
          break

        case "session.deleted":
          console.log(`[my-plugin] Session ${(event as any).sessionId || (event as any).session_id} deleted`)
          toolCallCount.clear() // Cleanup
          break

        case "session.compacted":
          console.log(`[my-plugin] Session ${(event as any).sessionId || (event as any).session_id} compacted`)
          break
      }
    },

    // -------------------------------------------
    // Optional: Custom tools
    // -------------------------------------------
    // tool: {
    //   mytool: tool({
    //     description: "...",
    //     args: { ... },
    //     async execute(args) { ... }
    //   })
    // }
  }
}

export default MyPlugin
