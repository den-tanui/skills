import type { Plugin } from "@opencode-ai/plugin"
import { tool } from "@opencode-ai/plugin"

/**
 * Plugin with Custom Tools
 *
 * Demonstrates how to add custom tools that the AI can call.
 * Each tool gets a description, Zod-validated args, and an execute function.
 */

export const MyPlugin: Plugin = async (ctx) => {
  console.log("[my-plugin] Loaded with custom tools")

  return {
    // -------------------------------------------
    // Custom Tools
    // -------------------------------------------
    tool: {
      // Tool 1: Simple greeting tool
      greet: tool({
        description: "Greet a user by name",
        args: {
          name: tool.schema.string().describe("The name to greet"),
          loud: tool.schema.boolean().optional().describe("Whether to SHOUT the greeting"),
        },
        async execute(args, context) {
          const { directory } = context
          const greeting = `Hello, ${args.name}!`
          const result = args.loud ? greeting.toUpperCase() : greeting
          console.log(`[my-plugin] Greeted ${args.name} in ${directory}`)
          return result
        },
      }),

      // Tool 2: Run a shell command
      run_check: tool({
        description: "Run a health check command",
        args: {
          command: tool.schema.string().describe("The command to run"),
        },
        async execute(args, context) {
          const { directory } = context
          try {
            // Use Bun's shell API (available via plugin context, not tool context)
            // For tools, use the bash tool or pass to plugin hook
            const { execSync } = await import("child_process")
            const result = execSync(args.command, { cwd: directory, encoding: "utf-8" })
            return result
          } catch (err: any) {
            return `Error: ${String(err)}`
          }
        },
      }),

      // Tool 3: Calculator tool
      calculate: tool({
        description: "Perform a simple calculation",
        args: {
          a: tool.schema.number().describe("First number"),
          b: tool.schema.number().describe("Second number"),
          operation: tool.schema
            .enum(["add", "subtract", "multiply", "divide"] as const)
            .describe("Operation to perform"),
        },
        async execute(args) {
          switch (args.operation) {
            case "add":
              return `${args.a + args.b}`
            case "subtract":
              return `${args.a - args.b}`
            case "multiply":
              return `${args.a * args.b}`
            case "divide":
              if (args.b === 0) throw new Error("Division by zero")
              return `${args.a / args.b}`
          }
        },
      }),

      // Tool 4: Read file with validation
      read_config: tool({
        description: "Read a config file and return its contents",
        args: {
          path: tool.schema.string().describe("Path to config file"),
        },
        async execute(args, context) {
          const { readFileSync } = await import("fs")
          const { join } = await import("path")
          const filePath = join(context.directory, args.path)

          try {
            const content = readFileSync(filePath, "utf-8")
            return content
          } catch (err) {
            throw new Error(`Failed to read ${filePath}: ${String(err)}`)
          }
        },
      }),
    },

    // -------------------------------------------
    // Optional: Event hooks
    // -------------------------------------------
    event: async ({ event }) => {
      if (event.type === "session.created") {
        console.log(`[my-plugin] Session ${(event as any).sessionId || (event as any).session_id} started`)
      }
    },
  }
}

export default MyPlugin
