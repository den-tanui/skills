import type { Plugin } from "@opencode-ai/plugin"

/**
 * Minimal OpenCode Plugin
 *
 * Copy this file to start a new plugin.
 * Place in: ~/.config/opencode/plugin/my-plugin.ts (global)
 *   or: .opencode/plugin/my-plugin.ts (project)
 *
 * Then add to opencode.json:
 *   { "plugin": ["file:///path/to/plugin"] }
 *
 * Restart OpenCode completely (kill + restart, not just new session)
 */

export const MyPlugin: Plugin = async ({ project, client, $, directory, worktree }) => {
  console.log(`[my-plugin] Initialized in ${directory}`)

  return {
    // -------------------------------------------
    // Event hooks - react to session lifecycle
    // -------------------------------------------
    event: async ({ event }) => {
      // Uncomment to see all events:
      // console.log(`[my-plugin] Event: ${event.type}`)

      if (event.type === "session.created") {
        console.log(`[my-plugin] Session ${(event as any).sessionId || (event as any).session_id} started`)
      }

      if (event.type === "session.idle") {
        console.log(`[my-plugin] Session ${(event as any).sessionId || (event as any).session_id} completed`)
      }
    },

    // -------------------------------------------
    // Tool execution hooks (optional)
    // -------------------------------------------
    // "tool.execute.before": async (input, output) => {
    //   // Runs BEFORE a tool executes
    //   // input: { tool, args, sessionID, callID }
    //   // output: mutable copy of args (modify to change behavior)
    //   // Throw error to BLOCK tool execution
    // },

    // "tool.execute.after": async (input) => {
    //   // Runs AFTER a tool executes
    //   // input: { tool, args, sessionID, callID }
    // },
  }
}

export default MyPlugin
