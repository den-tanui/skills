---
name: opencode-pty
description: Interactive PTY management for OpenCode — spawn background processes, send interactive input, read output with regex filtering, and manage multiple terminal sessions simultaneously.
---

# OpenCode PTY Plugin - Comprehensive Skill Guide

**Purpose**: Provides interactive PTY (pseudo-terminal) management for OpenCode, enabling AI agents to run background processes, send interactive input, read output with regex filtering, and manage multiple terminal sessions simultaneously.

**Plugin Name**: `opencode-pty`

---

## Table of Contents

1. [Installation & Setup](#installation--setup)
2. [Core Concepts](#core-concepts)
3. [Available Tools](#available-tools)
4. [Usage Patterns](#usage-patterns)
5. [Long-Running Processes](#long-running-processes)
6. [Interactive Input & Control](#interactive-input--control)
7. [Output Reading & Filtering](#output-reading--filtering)
8. [Web UI & Monitoring](#web-ui--monitoring)
9. [Advanced Features](#advanced-features)
10. [Configuration](#configuration)
11. [Permissions & Security](#permissions--security)
12. [Troubleshooting](#troubleshooting)

---

## Installation & Setup

### Adding to OpenCode Config

Add the plugin to your OpenCode configuration file (`.opencode/config.json` or `opencode.json`):

```json
{
  "$schema": "https://opencode.ai/config.json",
  "plugin": ["opencode-pty"]
}
```

OpenCode will automatically install the plugin on the next run.

### Updating the Plugin

OpenCode checks for plugin updates automatically on startup. No manual action required.

**Force Reinstall (if needed)**:

```bash
rm -rf ~/.cache/opencode/node_modules/opencode-pty
opencode
```

### Loading Local Development Version

For local development, point to the local checkout:

```json
{
  "$schema": "https://opencode.ai/config.json",
  "plugin": ["file:///absolute/path/to/opencode-pty/index.ts"]
}
```

---

## Core Concepts

### What Problems Does This Solve?

OpenCode's built-in `bash` tool runs commands **synchronously**—the agent waits for completion. This plugin solves this limitation for:

- **Dev servers** (`npm run dev`, `cargo watch`, `python manage.py runserver`)
- **Watch modes** (`npm test -- --watch`, `jest --watch`)
- **Long-running processes** (database servers, tunnels, background jobs)
- **Interactive programs** (REPLs, prompts, interactive CLIs)
- **Multiple concurrent tasks** (run tests while dev server stays alive)

### Session Model

The plugin manages **PTY (Pseudo-Terminal) Sessions**—independent terminal-like environments that run in the background.

**Session Lifecycle**:

```
spawn → running → [exited | killed]
                       ↓
               (stays in list until cleanup=true in pty_kill)
```

**Key Properties**:

- **ID**: Unique session identifier (e.g., `pty_a1b2c3d4`)
- **Status**: `running`, `exited`, or `killed`
- **PID**: Process ID of the running command
- **Output Buffer**: Rolling line buffer (ring buffer) storing recent output
- **Exit Code**: Available after process finishes

### Session Persistence

Sessions **remain in the list after exit** so the agent can:

- Read final output
- Check exit code
- Compare logs between multiple runs
- Restart if needed

Use `pty_kill` with `cleanup=true` to fully remove a session.

---

## Available Tools

### 1. `pty_spawn` - Create a New Session

**Description**: Spawns a new background process in a PTY session.

**Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `command` | string | Yes | Command to execute (e.g., `npm`, `python`, `cargo`) |
| `args` | array | - | Arguments for the command (e.g., `["run", "dev"]`) |
| `workdir` | string | - | Working directory (defaults to current directory) |
| `env` | object | - | Environment variables to set |
| `title` | string | - | Descriptive name for the session (e.g., "Dev Server") |
| `notifyOnExit` | boolean | - | If `true`, send chat notification when process exits (default: `false`) |
| `timeoutSeconds` | number | - | Auto-kill session after N seconds (useful for tests) |

**Returns**:

```json
{
  "id": "pty_a1b2c3d4",
  "command": "npm",
  "args": ["run", "dev"],
  "title": "Dev Server",
  "status": "running",
  "pid": 12345
}
```

**Best Practices**:

- Use descriptive `title` values so the agent knows which session is which
- Set `notifyOnExit=true` for long-running processes (builds, tests, deployments)
- Use `timeoutSeconds` for tests to prevent infinite hangs
- Set relevant environment variables if needed (e.g., `PYTHONUNBUFFERED` for Python)

---

### 2. `pty_write` - Send Input to a Session

**Description**: Sends keyboard input (text, Ctrl+C, arrow keys, etc.) to a running PTY session.

**Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `id` | string | Yes | Session ID (e.g., `pty_a1b2c3d4`) |
| `data` | string | Yes | Input to send (text or escape sequences) |

**Escape Sequences**:

| Escape | Meaning | Use Case |
|--------|---------|----------|
| `\x03` | Ctrl+C | Stop running process |
| `\x04` | Ctrl+D | EOF / Exit |
| `\x1b[A` | Arrow Up | Navigate REPL history |
| `\x1b[B` | Arrow Down | Navigate REPL history |
| `\n` | Enter / Return | Submit input |

**Best Practices**:

- Always include `\n` at the end of text input to "submit" the command
- Use escape sequences for control signals (Ctrl+C, Ctrl+D)
- Send input only to sessions you know exist and are running

---

### 3. `pty_read` - Read Session Output

**Description**: Reads the output buffer from a PTY session with optional pagination and regex filtering.

**Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `id` | string | Yes | Session ID |
| `offset` | number | - | Starting line offset (0 = oldest, default: from current position) |
| `limit` | number | - | Max lines to return (default: all remaining) |
| `pattern` | string | - | Regex pattern to filter lines (e.g., `error\|ERROR\|warning`) |
| `ignoreCase` | boolean | - | Case-insensitive regex matching (default: `false`) |

**Returns**:

```json
{
  "lines": [
    "1 | > dev",
    "2 | Vite v5.0.0 building for production...",
    "3 | ✓ 1234 modules transformed.",
    "4 | built in 3.45s"
  ],
  "totalLines": 150,
  "offset": 0,
  "limit": 4,
  "byteLength": 340
}
```

**Best Practices**:

- Use `limit` to avoid huge responses for long-running processes
- Use `pattern` to extract relevant information (errors, warnings, success messages)
- Use `offset` + `limit` for pagination through large output
- Always set `ignoreCase=true` when searching for common keywords (Error, WARNING, Failed)

---

### 4. `pty_list` - List All Sessions

**Description**: Lists all PTY sessions with their status, PID, and line count.

**Parameters**: None (no parameters)

**Returns**:

```json
{
  "sessions": [
    {
      "id": "pty_dev_server",
      "title": "Dev Server",
      "command": "npm",
      "args": ["run", "dev"],
      "status": "running",
      "pid": 12345,
      "lineCount": 250,
      "exitCode": null,
      "startedAt": "2024-01-15T10:30:00Z"
    }
  ]
}
```

**Best Practices**:

- Use at the start of a task to understand the current state
- Check `status` before sending input to a session
- Monitor `lineCount` to detect if output buffer is growing unexpectedly

---

### 5. `pty_kill` - Terminate a Session

**Description**: Terminates a PTY session, optionally cleaning up the output buffer.

**Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `id` | string | Yes | Session ID |
| `cleanup` | boolean | - | If `true`, remove session from list entirely (default: `false`) |

**Returns**:

```json
{
  "id": "pty_dev_server",
  "status": "killed",
  "cleaned": true,
  "finalLineCount": 250
}
```

**Best Practices**:

- Use `cleanup=false` (default) to preserve output after killing
- Read output with `pty_read` **before** killing with `cleanup=true` if you need the logs
- For one-off tests, use `cleanup=true` to free memory
- For important builds, keep output for debugging failed runs

---

## Usage Patterns

### Pattern 1: Simple Background Task

**Scenario**: Start a dev server and let it run.

```
1. pty_spawn: command="npm", args=["run", "dev"], title="Dev Server"
   → Returns: pty_dev_123

2. ... do other work ...

3. pty_read: id="pty_dev_123", limit=20
   → Check last 20 lines to verify it's running

4. pty_kill: id="pty_dev_123"  (when done)
```

### Pattern 2: Long-Running Process with Exit Notification

**Scenario**: Run a build that takes 5+ minutes, get notified when it completes.

```
1. pty_spawn: command="npm", args=["run", "build"], title="Build", notifyOnExit=true
   → Returns: pty_build_001
   
2. Agent checks other things...

3. [Plugin sends notification when build exits]:
   <pty_exited>
   ID: pty_build_001
   Title: Build
   Exit Code: 0
   Output Lines: 123
   Last Line: Build completed successfully!
   </pty_exited>

4. pty_read: id="pty_build_001", limit=50
   → Review build output
```

### Pattern 3: Interactive Testing with Watch Mode

**Scenario**: Run tests in watch mode, interact with them.

```
1. pty_spawn: command="npm", args=["test", "--watch"], title="Test Watcher"
   → Returns: pty_watch_001

2. pty_read: id="pty_watch_001", limit=30
   → Verify tests are running

3. [Modify code]

4. pty_write: id="pty_watch_001", data="a\n"  (run all tests)

5. [Wait a moment]

6. pty_read: id="pty_watch_001", pattern="PASS|FAIL", ignoreCase=true
   → Check test results

7. [Repeat steps 3-6 as needed]

8. pty_write: id="pty_watch_001", data="\x03"  (Ctrl+C to exit)
```

### Pattern 4: Multiple Concurrent Processes

**Scenario**: Run dev server, tests, and database concurrently.

```
1. pty_spawn: command="npm", args=["run", "dev"], title="Dev Server"
   → pty_dev_001

2. pty_spawn: command="npm", args=["test"], title="Tests", notifyOnExit=true
   → pty_test_001

3. pty_spawn: command="docker", args=["run", "postgres:15"], title="Database"
   → pty_db_001

4. pty_list:
   → Confirm all three are running

5. [Do development work, check outputs as needed]

6. pty_read: id="pty_test_001"  (when notification comes)
   → Review test results

7. [Clean up in reverse order]
   pty_kill: id="pty_dev_001"
   pty_kill: id="pty_test_001"
   pty_kill: id="pty_db_001", cleanup=true
```

---

## Long-Running Processes

### Key Patterns for Long-Running Tasks

#### 1. Use `notifyOnExit=true` to Avoid Polling

**Without notification** (bad - requires polling):

```
# Agent has to repeatedly ask "is it done?"
pty_read: id="pty_build_001", pattern="error|success"
→ ... wait 10 seconds ...
→ ... ask again ...
```

**With notification** (good - event-driven):

```
pty_spawn: command="npm", args=["run", "build"], 
           title="Build", notifyOnExit=true
→ Plugin automatically sends message when done:
<pty_exited>
ID: pty_build_001
Title: Build
Exit Code: 0
...</pty_exited>
```

#### 2. Use `timeoutSeconds` for Tests

Prevents hung processes from blocking:

```
pty_spawn: command="npm", args=["test"], 
           title="Tests", 
           notifyOnExit=true,
           timeoutSeconds=600
→ Auto-kills after 10 minutes even if stuck
```

#### 3. Monitor Output Without Stopping Process

Periodically read output without interrupting:

```
# Start long build
pty_spawn: command="cargo", args=["build", "--release"], title="Cargo Build"
→ pty_cargo_001

# Check progress every minute (or whenever)
pty_read: id="pty_cargo_001", limit=5
→ "Compiling xyz v1.0.0 (62/100)"

pty_read: id="pty_cargo_001", limit=5
→ "Compiling abc v2.0.0 (75/100)"

pty_read: id="pty_cargo_001", limit=5
→ "Finished release ..."
```

#### 4. Stream-like Reading for Real-Time Updates

Read new output in chunks:

```
# Keep track of where we read last
current_offset = 0

Loop until done:
  pty_read: id="pty_stream", offset=current_offset, limit=20
  → Print new lines
  → Update current_offset
  → Sleep 1 second
  → Check if exited via pty_list
```

---

## Interactive Input & Control

### Sending Commands to Interactive Processes

#### Example 1: REPL / Python Shell

```
# Start Python REPL
pty_spawn: command="python3", title="Python REPL"
→ pty_python_001

# Send a command
pty_write: id="pty_python_001", data="print('hello world')\n"

# Read output
pty_read: id="pty_python_001", limit=5
→ hello world
```

#### Example 2: npm run dev (with hot reload restart)

```
# Start dev server
pty_spawn: command="npm", args=["run", "dev"], title="Dev Server"
→ pty_dev_001

# When you want to restart (some dev servers support "rs" + Enter)
pty_write: id="pty_dev_001", data="rs\n"

# Check it restarted
pty_read: id="pty_dev_001", limit=10, pattern="restarted|running"
```

#### Example 3: Interactive Git Command

```
# Some git commands are interactive (e.g., git rebase -i)
pty_spawn: command="git", args=["rebase", "-i", "HEAD~5"], title="Git Rebase"
→ pty_git_001

# Editor might open; send input to accept defaults
pty_write: id="pty_git_001", data="\x03"  # Ctrl+C if needed, or :q to close editor

# Better: use non-interactive flags
pty_spawn: command="git", args=["rebase", "--continue"], title="Git Rebase Continue"
```

### Stopping Processes Gracefully

#### Send Ctrl+C (SIGINT)

```
pty_write: id="pty_process", data="\x03"
```

**Use for**:
- Stopping dev servers
- Interrupting watch processes
- Canceling long operations

#### Send Ctrl+D (EOF)

```
pty_write: id="pty_process", data="\x04"
```

**Use for**:
- Exiting REPLs/shells
- Closing stdin

#### Graceful termination followed by kill

```
# Try Ctrl+C first
pty_write: id="pty_process", data="\x03"

# Wait a moment (simulated via other commands)

# Check if it exited
pty_list:
→ Check status of pty_process

# If still running, kill it
pty_kill: id="pty_process", cleanup=false
```

---

## Output Reading & Filtering

### Basic Output Reading

```
# Last N lines
pty_read: id="pty_001", limit=100

# Lines from offset to end
pty_read: id="pty_001", offset=50

# Window: lines 50-75
pty_read: id="pty_001", offset=50, limit=25
```

### Pattern Filtering (Regex)

```
# Find errors
pty_read: id="pty_build", pattern="^error|ERROR|✗"

# Find success
pty_read: id="pty_build", pattern="success|✓|completed"

# Find specific log level
pty_read: id="pty_app", pattern="\[ERROR\]|\[WARN\]"

# Find URLs
pty_read: id="pty_dev", pattern="http://.*:.*"
```

### Case-Insensitive Search

```
# Find "error", "Error", "ERROR", etc.
pty_read: id="pty_001", pattern="error", ignoreCase=true

# Find "warning", "WARNING", etc.
pty_read: id="pty_001", pattern="warning", ignoreCase=true
```

### Multi-Pattern Search

```
# Find lines with error OR warning (regex OR syntax)
pty_read: id="pty_001", pattern="error|warning", ignoreCase=true

# Find lines with "error" AND "database"
pty_read: id="pty_001", pattern="error.*database|database.*error", ignoreCase=true
```

### Pagination for Large Outputs

```
# Session has 10,000 lines total
# Read in chunks:

# First 100
pty_read: id="pty_001", offset=0, limit=100

# Next 100
pty_read: id="pty_001", offset=100, limit=100

# Next 100
pty_read: id="pty_001", offset=200, limit=100

# Continue until done
```

---

## Web UI & Monitoring

### Opening the Web UI

**Via Slash Command** (in OpenCode chat):

```
/pty-open-background-spy
```

This will:
1. Start the WebSocket server (if not running)
2. Open browser at the server URL
3. Display all active PTY sessions with live output

### Web UI Features

- **Session List**: View all active sessions with status indicators
- **Real-time Output**: Live streaming of process output
- **Interactive Input**: Send commands directly from the UI
- **Session Management**: Kill sessions from the UI
- **Connection Status**: Visual indicator of WebSocket connection

### Getting the Server URL

**Via Slash Command**:

```
/pty-show-server-url
```

**Example Output**:
```
PTY Web Server: http://localhost:5174
```

Use this to connect external tools or multiple browser windows.

### WebSocket Streaming (for custom clients)

Connect to `/ws` for real-time updates:

```javascript
const PORT = 5174;  // Or whatever port is shown
const ws = new WebSocket(`ws://localhost:${PORT}/ws`);

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  if (data.type === 'raw_data') {
    console.log('New output:', data.rawData);
  } else if (data.type === 'session_list') {
    console.log('Sessions:', data.sessions);
  } else if (data.type === 'session_update') {
    console.log('Session update:', data.session);
  }
};

ws.onerror = (error) => console.error('WebSocket error:', error);
```

### REST API for Session Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/sessions` | List all PTY sessions |
| `POST` | `/api/sessions` | Create a new PTY session |
| `GET` | `/api/sessions/:id` | Get session details |
| `POST` | `/api/sessions/:id/input` | Send input to a session |
| `DELETE` | `/api/sessions/:id` | Kill a session (no cleanup) |
| `DELETE` | `/api/sessions/:id/cleanup` | Kill and cleanup |
| `GET` | `/api/sessions/:id/buffer/plain` | Get output (plain text) |
| `GET` | `/api/sessions/:id/buffer/raw` | Get output (raw) |
| `DELETE` | `/api/sessions` | Clear all sessions |
| `GET` | `/health` | Server health check |

**Example: Create a session via API**:

```bash
curl -X POST http://localhost:5174/api/sessions \
  -H "Content-Type: application/json" \
  -d '{
    "command": "bash",
    "args": ["-c", "echo hello && sleep 10"],
    "description": "Test session",
    "timeoutSeconds": 15
  }'
```

---

## Advanced Features

### Environment Variables in Sessions

```
pty_spawn: 
  command="python", 
  args=["-m", "http.server", "8000"],
  env={"PYTHONUNBUFFERED": "1", "DEBUG": "true"}
```

**Useful env vars**:

- `PYTHONUNBUFFERED=1` - Python: flush output immediately
- `NODE_ENV=development` - Node: dev mode
- `RUST_LOG=debug` - Rust: debug logging
- `DEBUG=*` - Node/JS: enable debug output
- `NO_COLOR=1` - Disable colored output

### Working Directory

```
pty_spawn:
  command="npm",
  args=["run", "build"],
  workdir="/path/to/project"
```

Useful when:
- Project isn't in current working directory
- Running multiple projects concurrently
- Need to ensure correct context

### Custom Session Titles

```
pty_spawn: 
  command="npm", 
  args=["run", "dev"],
  title="Frontend Dev Server (port 3000)"
```

**Best Practices**:

- Include port number in title (`Dev Server (port 5173)`)
- Include project name (`MyApp API Server`)
- Include version if managing multiple (`API v1 Dev`, `API v2 Dev`)

### Output Buffer Management

The plugin maintains a **rolling line buffer** for each session:

- **Default max**: 50,000 lines per session
- **Configurable**: Set `PTY_MAX_BUFFER_LINES` environment variable
- **Behavior**: Oldest lines are dropped when buffer fills up

**Set custom buffer size**:

```bash
export PTY_MAX_BUFFER_LINES=100000
opencode
```

---

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PTY_MAX_BUFFER_LINES` | `50000` | Max lines to keep per session |
| `PTY_WEB_HOSTNAME` | `::1` | Web server hostname (IPv6 loopback) |
| `PTY_WEB_PORT` | `0` (random) | Web server port (0 = auto-assign) |

**Example: Set custom buffer size**:

```bash
export PTY_MAX_BUFFER_LINES=100000
export PTY_WEB_PORT=5555
opencode
```

### Permission Configuration

Add to `opencode.json`:

```json
{
  "permission": {
    "bash": {
      "npm run dev": "allow",
      "npm run build": "allow",
      "npm test *": "allow",
      "cargo build": "allow",
      "python *": "allow",
      "git push": "deny",
      "rm -rf": "deny"
    }
  }
}
```

The plugin respects OpenCode's permission system. Commands matching your permissions will be allowed or denied accordingly.

---

## Permissions & Security

### How Permissions Work

Commands spawned via `pty_spawn` are checked against your `permission.bash` configuration in `opencode.json`.

### Permission Levels

- **`allow`**: Command always allowed
- **`deny`**: Command never allowed
- **`ask`**: (Treated as `deny` by this plugin - cannot trigger UI)
- **`external_directory` with `ask`**: (Treated as `allow` - working directory outside project)

### Example: Safe Development Configuration

```json
{
  "$schema": "https://opencode.ai/config.json",
  "permission": {
    "bash": {
      "npm *": "allow",
      "yarn *": "allow",
      "cargo *": "allow",
      "python *": "allow",
      "git clone": "allow",
      "git pull": "allow",
      "git push": "deny",
      "git reset --hard": "deny",
      "rm -rf": "deny",
      "sudo *": "deny"
    }
  }
}
```

### Important Security Notes

**"ask" permissions are treated as "deny"**: Since plugins cannot trigger OpenCode's permission prompt UI, commands matching an "ask" pattern will be denied. You'll see a toast notification explaining this.

**"external_directory" with "ask" is treated as "allow"**: When the working directory is outside the project and `permission.external_directory` is set to "ask", this plugin allows it (with a notification).

---

## Troubleshooting

### Session Not Responding / Hung Process

**Symptom**: Process started but `pty_read` returns old output.

**Solutions**:

1. Check if process is actually running:
   ```
   pty_list:
   → Check status is "running"
   ```

2. Try sending Ctrl+C:
   ```
   pty_write: id="pty_process", data="\x03"
   ```

3. Force kill if needed:
   ```
   pty_kill: id="pty_process", cleanup=true
   ```

### No Output Appearing

**Symptom**: Process started but `pty_read` returns no lines.

**Possible causes**:

1. Process hasn't output anything yet (normal for startup)
   - Wait a moment and try again
   
2. Output is buffered (common in compiled languages)
   - Set `PYTHONUNBUFFERED=1` for Python
   - Use `--verbose` or `--debug` flags
   
3. Output is going to stderr (not captured by default in some shells)
   - Redirect: `args=["run", "dev", "2>&1"]`

4. Session exited immediately
   - Check exit code: `pty_list: → exitCode: 1`
   - Read output for errors: `pty_read: id="pty_process", limit=50`

### Permission Denied Errors

**Symptom**: `pty_spawn` fails with permission error.

**Solution**:

1. Check your `permission.bash` configuration
2. Ensure the command pattern matches and is set to `"allow"`
3. Look for "ask" patterns that default to deny
4. Review the toast notification for details

### Web UI Not Connecting

**Symptom**: Browser shows "Disconnected" or can't load UI.

**Solutions**:

1. Verify server is running:
   ```
   /pty-show-server-url
   → Should show URL like http://localhost:5174
   ```

2. Check firewall/network:
   - Open `http://localhost:5174` directly in browser
   - On remote systems, use SSH tunnel: `ssh -L 5174:localhost:5174 user@host`

3. Restart the plugin:
   - Kill OpenCode
   - Clear cache: `rm -rf ~/.cache/opencode/node_modules/opencode-pty`
   - Restart OpenCode

### Session Cleanup Not Working

**Symptom**: Old sessions still in list after `pty_kill`.

**Solution**:

```
# Make sure you use cleanup=true to fully remove
pty_kill: id="pty_old_session", cleanup=true
```

Sessions without `cleanup=true` persist for output inspection. This is intentional.

### Out of Memory / Buffer Growing

**Symptom**: Multiple sessions using excessive memory.

**Solution**:

1. Reduce buffer size:
   ```bash
   export PTY_MAX_BUFFER_LINES=10000
   opencode
   ```

2. Clean up old sessions:
   ```
   pty_list:
   → Find exited sessions
   
   pty_kill: id="pty_old_1", cleanup=true
   pty_kill: id="pty_old_2", cleanup=true
   ```

3. Monitor sessions:
   ```
   pty_list:
   → Check lineCount for each session
   ```

---

## Session Name Best Practices

When instructing the coding agent to run background processes, **use the word "session"** in your command:

**Good**:
```
"Run the dev server as a background SESSION"
"Start the test watcher in a SESSION"
```

**Avoid**:
```
"Run the dev server as a background task"  (might use & instead)
"Start the test watcher as a process"       (might use & instead)
```

The agent will consistently use PTY sessions when you use the word "session".

---

## Quick Reference

### Spawn a long-running process

```
pty_spawn: command="CMD", args=[...], title="Title", notifyOnExit=true
```

### Check process output

```
pty_read: id="PTY_ID", limit=50, pattern="error", ignoreCase=true
```

### Send keyboard input

```
pty_write: id="PTY_ID", data="input\n"
```

### Stop a process

```
pty_write: id="PTY_ID", data="\x03"
```

### List all sessions

```
pty_list:
```

### Kill a session

```
pty_kill: id="PTY_ID", cleanup=true
```

### Open web monitor

```
/pty-open-background-spy
```

---

## Additional Resources

- **GitHub Repository**: https://github.com/shekohex/opencode-pty
- **OpenCode Documentation**: https://opencode.ai/docs
- **OpenCode Plugin Guide**: https://opencode.ai/docs/plugins
- **Bun PTY Library**: https://github.com/nicksrandall/bun-pty

---

## License

MIT - Same as opencode-pty repository

---

**Last Updated**: 2024 | **Plugin Version**: 0.3.6+
