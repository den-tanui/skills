# Publishing & Distribution Guide

How to package, test locally, and publish OpenCode plugins.

---

## Local Development (No Publishing Required)

### Method 1: Local File Path

Point OpenCode directly to your plugin directory:

```json
// ~/.config/opencode/opencode.json or .opencode/opencode.json
{
  "plugin": ["file:///path/to/your/plugin"]
}
```

**Pros:** Instant changes, no rebuild needed if using TypeScript (Bun transpiles on the fly)
**Cons:** Must restart OpenCode to pick up changes

### Method 2: Symlink to Plugin Directory

```bash
# Global plugin
ln -s /path/to/your/plugin ~/.config/opencode/plugin/my-plugin

# Project plugin
ln -s /path/to/your/plugin .opencode/plugin/my-plugin
```

### Method 3: Build and Reference dist/

```bash
# Build the plugin
bun build src/index.ts --outdir dist --target node --format esm

# Reference in config
{
  "plugin": ["file:///path/to/your/plugin/dist/index.js"]
}
```

---

## Building for npm

### Build Script

Add to `package.json`:

```json
{
  "scripts": {
    "build": "bun build src/index.ts --outdir dist --target node --format esm --external @opencode-ai/plugin --external @opencode-ai/sdk",
    "prepare": "bun run build"
  }
}
```

### Important: External Dependencies

Always mark OpenCode packages as external:

```bash
bun build src/index.ts --outdir dist --target node --format esm \
  --external @opencode-ai/plugin \
  --external @opencode-ai/sdk
```

This prevents bundling and lets OpenCode provide the packages at runtime.

---

## npm Publish

### 1. Prepare package.json

```json
{
  "name": "opencode-your-plugin",
  "version": "1.0.0",
  "description": "Short description of what your plugin does",
  "main": "dist/index.js",
  "types": "dist/index.d.ts",
  "files": ["dist", "src/skills", "src/agents", "README.md"],
  "keywords": ["opencode", "opencode-plugin", "ai", "..."],
  "dependencies": {
    "@opencode-ai/plugin": "^1.3.17"
  },
  "peerDependencies": {
    "zod": "^4.0.0"
  }
}
```

### 2. Login to npm

```bash
npm login
```

### 3. Publish

```bash
# First publish
npm publish

# Subsequent updates
npm version patch  # or minor, major
npm publish
```

### Scoped Packages

For organization packages:

```bash
npm publish --access public
```

---

## Plugin Installation Methods

### From npm (Recommended for Users)

```json
{
  "plugin": ["opencode-your-plugin@latest"]
}
```

OpenCode auto-installs using Bun at startup.

### From GitHub

```json
{
  "plugin": ["github:yourname/your-plugin"]
}
```

### Local Development

```json
{
  "plugin": ["file:///path/to/plugin"]
}
```

---

## Including Bundled Assets

### Skills (Auto-Discovered)

```
my-plugin/
├── src/
│   ├── index.ts
│   └── skills/           # <-- Bundled skills
│       ├── my-skill/SKILL.md
│       └── another-skill/SKILL.md
```

No config needed — OpenCode finds these automatically.

### Agents (Auto-Discovered)

```
my-plugin/
├── src/
│   └── agents/           # <-- Bundled agents
│       ├── my-agent.md
│       └── helper-agent.md
```

### Commands (Manual Install)

Commands are NOT auto-discovered from npm packages. You need a setup script:

```typescript
// In your plugin or setup script
import { cpSync } from "fs"
import { homedir } from "os"
import { join } from "path"

const commandsSrc = join(import.meta.dir, "src/commands")
const commandsDest = join(homedir(), ".config/opencode/commands")

cpSync(commandsSrc, commandsDest, { recursive: true })
```

Or document for users to copy manually.

---

## Version Management

### In package.json

```json
{
  "version": "1.2.3",
  "scripts": {
    "release:patch": "npm version patch && git push --follow-tags && npm publish",
    "release:minor": "npm version minor && git push --follow-tags && npm publish",
    "release:major": "npm version major && git push --follow-tags && npm publish"
  }
}
```

### Semantic Versioning

- **Patch** (1.0.1): Bug fixes, docs updates
- **Minor** (1.1.0): New features, backward-compatible
- **Major** (2.0.0): Breaking changes

---

## Testing Before Publishing

### 1. Local Smoke Test

```bash
# Build
bun run build

# Check the output
ls -la dist/

# Test with a simple script
node -e "import('$PWD/dist/index.js').then(m => console.log('OK:', Object.keys(m)))"
```

### 2. Install Globally for Testing

```bash
# Link globally
npm link

# Or install from local path
cd ~/.config/opencode
npm install /path/to/your/plugin
```

### 3. Test in OpenCode

```json
{
  "plugin": ["opencode-your-plugin"]
}
```

Restart OpenCode and verify:
- Plugin loads without errors
- Tools appear in agent's toolkit
- Skills/agents are discoverable

---

## Common Issues

### "Cannot find module @opencode-ai/plugin"

**Cause:** Forgot to mark as external in build, or didn't declare in `package.json`

**Fix:**
```json
// package.json
{
  "dependencies": {
    "@opencode-ai/plugin": "^1.3.17"
  }
}
```

And in build:
```bash
--external @opencode-ai/plugin
```

### Plugin Not Loading

**Check:**
1. File is in `~/.config/opencode/plugin/` or `.opencode/plugin/`
2. File has `.ts` or `.js` extension
3. OpenCode was restarted (not just new session)
4. No syntax errors in plugin code

### "Module not found" for Local Imports

**Cause:** Plugin files must be self-contained

**Fix:** Bundle code inline or use npm packages

---

## Publishing Checklist

- [ ] `package.json` has correct `name`, `version`, `description`
- [ ] `main` field points to built file (e.g., `dist/index.js`)
- [ ] `files` field includes all necessary files
- [ ] `@opencode-ai/plugin` in `dependencies`
- [ ] Build succeeds (`bun run build`)
- [ ] No local imports in plugin files
- [ ] `README.md` documents installation and usage
- [ ] Tested locally with `file://` protocol
- [ ] Logged into npm (`npm whoami`)
- [ ] Ready to publish (`npm publish`)

---

## Resources

- [npm publish docs](https://docs.npmjs.com/cli/v8/commands/npm-publish)
- [OpenCode Plugin Docs](https://opencode.ai/docs/plugins/)
- [Creating a plugin from OpenCode School](https://opencode.school/lessons/plugins)
