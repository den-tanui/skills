# Debugging and Testing OpenCode Plugins

## Debugging Plugins

### Native OpenCode Debugging Tools
- **Log level**: Launch OpenCode with `opencode --log-level DEBUG` for detailed debug output (source: [Troubleshooting Docs](https://opencode.ai/docs/troubleshooting/))
- **Structured logging**: Use `client.app.log()` instead of `console.log` for plugin logging. Supports levels: `debug`, `info`, `warn`, `error`:
  ```typescript
  await client.app.log({
    body: {
      service: "my-plugin",
      level: "info",
      message: "Plugin initialized",
      extra: { key: "value" }
    }
  })
  ```
  (source: [Plugin Docs](https://opencode.ai/docs/plugins/))
- **Isolate plugin issues**: Temporarily disable plugins by:
  1. Removing the `plugin` key from `opencode.json` (set to empty array `[]`)
  2. Renaming plugin directories (`~/.config/opencode/plugins/` or `.opencode/plugins/`)
  (source: [Troubleshooting Docs](https://opencode.ai/docs/troubleshooting/))
- **Clear cache**: Fix corrupted cache/provider issues with `rm -rf ~/.cache/opencode` (source: [Troubleshooting Docs](https://opencode.ai/docs/troubleshooting/))

### Common Debugging Tips
1. **Plugin not loading?** Check for TypeScript syntax errors (prevents loading)
2. **Hooks not firing?** Verify hook names match exactly (case-sensitive)
3. **State not persisting?** Use session-keyed `Map` objects, not global variables
4. **`client.session.prompt` failing?** Check destructuring: use `async ({ client })` not `async (client)`
(source: [OpenCode Plugins Guide Gist](https://gist.github.com/johnlindquist/0adf1032b4e84942f3e1050aba3c5e4a))

### Advanced Debugging Tools
- **opencode-debug-helper**: Plugin for automated debugging with `/debug` command. Provides tools for project detection, instrumentation, log analysis, and process management (source: [shamashel/opencode-debug-helper](https://github.com/shamashel/opencode-debug-helper))
- **opencode-pty**: Manage interactive PTY sessions to debug OpenCode itself by running inner instances, sending inputs, and capturing terminal output (source: [JosXa/opencode-pty](https://github.com/JosXa/opencode-pty))

---

## Testing Plugins

### Testing Framework
OpenCode plugins use **Bun's built-in test runner**. Bun auto-discovers all `*.test.ts` files under `src/` with no separate config needed.
(source: [opencode-hooks-plugin](https://registry.npmjs.org/opencode-hooks-plugin))

### Test Commands
```bash
bun test                      # Run all tests
bun test src/config.test.ts   # Run specific test file
bun test --test-name-pattern "command"  # Filter by test name
bun test --verbose            # Verbose output
bun run build && bun test     # Test compiled output (optional)
```

### Mocking OpenCode APIs
- Mock `globalThis.fetch` for HTTP handler tests
- Pass fake SDK client for prompt/agent handler tests
- Create isolated temporary directories for config tests to avoid leaking real user settings
(source: [opencode-hooks-plugin test isolation notes](https://registry.npmjs.org/opencode-hooks-plugin))

### Mock Plugin Context Example
```typescript
const mockContext = {
  project: { root: '/test/project' },
  client: {
    app: { log: async (body) => console.log(body) }
  },
  $: async (cmd) => ({ stdout: '', stderr: '' }),
  directory: '/test/project',
  worktree: null
};

const plugin = await MyPlugin(mockContext);
// Simulate event
await plugin.event({
  event: { type: 'file.edited', data: { path: 'test.txt' } }
});
```
(source: [creating-opencode-plugins skill](https://claude-plugins.dev/skills/@pr-pm/prpm/creating-opencode-plugins))

### Test Coverage Structure
| Test File | Coverage |
|-----------|----------|
| `config.test.ts` | Settings loading/merging, `disableAllHooks` precedence, malformed JSON handling |
| `events.test.ts` | Event mapping, input builders (`buildToolHookInput`, `buildSessionHookInput`) |
| `executor.test.ts` | All handler types (`command`, `http`, `prompt`, `agent`), timeouts, env var interpolation |
| `matcher.test.ts` | Wildcard, exact, regex matching, case-sensitivity |
(source: [opencode-hooks-plugin](https://registry.npmjs.org/opencode-hooks-plugin))

---

## Local Development Workflow

### Loading Local Plugins
- **Project-level**: Place `.ts`/`.js` files in `.opencode/plugins/` (auto-loaded, no `opencode.json` entry needed)
- **Global-level**: Place files in `~/.config/opencode/plugins/` (available in all projects)
- **npm plugins**: Add package name to `opencode.json` `plugin` array
(source: [Plugin Docs](https://opencode.ai/docs/plugins/))

### Rebuilding After Changes
```bash
bun run build   # Compile src/ → dist/
bun run dev     # Watch mode for auto-rebuild
```
(source: [shamashel/opencode-debug-helper](https://github.com/shamashel/opencode-debug-helper))

### Verifying Plugin Load
1. Quit and restart OpenCode Desktop
2. Check logs for plugin initialization messages
3. Trigger test events (e.g., edit a file to fire `file.edited`, call a custom tool)
