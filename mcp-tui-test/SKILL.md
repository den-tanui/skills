---
name: mcp-tui-test
description: Test Terminal User Interface (TUI) applications programmatically using MCP. Like Playwright but for TUIs, supporting both stream mode for CLI tools and buffer mode for full TUI applications.
version: 1.0.0
author: AI Assistant
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [tui, testing, automation, terminal, cli, playwright]
    related_skills: [bash, shell-scripting, debugging]
---

# MCP TUI Testing Skill

**Like Playwright, but for Terminal User Interfaces**

This skill enables AI assistants to test Terminal User Interface (TUI) applications programmatically using the MCP TUI Test server. It provides tools to launch, interact with, and verify TUI applications in both stream and buffer modes.

## When to Use This Skill

Activate this skill when you need to:

- Test command-line tools and interactive CLIs
- Automate testing of full TUI applications (htop, vim, dialog boxes)
- Verify TUI application behavior and output
- Create automated test scenarios for terminal applications
- Debug and inspect TUI application state
- Test applications that require keyboard input and screen verification

## Key Features

- **Dual Testing Modes**: Stream mode for CLI tools, buffer mode for full TUIs
- **Session Management**: Run multiple TUI applications simultaneously
- **Keyboard Input**: Send keys, control combinations, and special characters
- **Screen Capture**: Read and analyze terminal output
- **Position-Based Testing**: Verify text at specific screen coordinates (buffer mode)
- **Cursor Tracking**: Monitor cursor position in real-time (buffer mode)
- **Asynchronous Waiting**: Wait for specific content to appear
- **Assertions**: Verify expected content is present

## Testing Modes

### Stream Mode
- **Best for**: CLI tools, command-line applications, simple interactive programs
- **Uses**: pexpect for stream-based testing
- **Features**: Text matching, pattern waiting, output capture
- **Example use cases**: git, npm, grep, interactive shell scripts

### Buffer Mode
- **Best for**: Full TUI applications, ncurses apps, dialog boxes, menus
- **Uses**: pexpect + pyte for screen buffer emulation
- **Features**: All stream features PLUS position-based assertions, cursor tracking, region extraction
- **Example use cases**: htop, vim, dialog, interactive menus

**When to use which mode:**
- Use **stream mode** for applications that output text sequentially
- Use **buffer mode** for applications that draw complex UIs with cursor movement

## Available Tools

### Session Management

#### `launch_tui`
Launch a TUI application for testing.

**Parameters:**
- `command` (required): The command to launch the TUI application
- `session_id` (optional): Unique identifier for this session (default: "default")
- `timeout` (optional): Command timeout in seconds (default: 30)
- `dimensions` (optional): Terminal dimensions as WIDTHxHEIGHT (default: "80x24")
- `mode` (optional): Testing mode - "stream" or "buffer" (default: "stream")

**Examples:**
```python
# Stream mode for CLI tools
launch_tui(command="python example_tui_app.py", session_id="test1")

# Buffer mode for full TUI applications
launch_tui(command="htop", session_id="test2", mode="buffer", dimensions="120x40")
```

#### `close_session`
Close a TUI testing session.

**Parameters:**
- `session_id` (optional): Session identifier (default: "default")

**Example:**
```python
close_session(session_id="test1")
```

#### `list_sessions`
List all active TUI testing sessions.

**Example:**
```python
list_sessions()
```

### Input Tools

#### `send_keys`
Send keyboard input to a TUI application.

**Parameters:**
- `keys` (required): Keys to send. Use `\n` for Enter, `\t` for Tab, `\x1b` for Escape
- `session_id` (optional): Session identifier (default: "default")
- `delay` (optional): Delay in seconds after sending keys (default: 0.1)

**Example:**
```python
send_keys(keys="1\n", session_id="test1")
```

#### `send_ctrl`
Send a Ctrl+Key combination to the TUI application.

**Parameters:**
- `key` (required): The key to combine with Ctrl (e.g., 'c', 'd', 'z')
- `session_id` (optional): Session identifier (default: "default")

**Example:**
```python
send_ctrl(key="c", session_id="test1")
```

### Output Capture Tools

#### `capture_screen`
Capture the current screen output of a TUI application.

**Parameters:**
- `session_id` (optional): Session identifier (default: "default")
- `include_ansi` (optional): Whether to include ANSI escape codes in stream mode (default: False)
- `use_buffer` (optional): Force buffer/stream mode. Auto-detects if None (default: None)

**Examples:**
```python
# Auto-detect mode based on session
capture_screen(session_id="test1")

# Force buffer mode capture
capture_screen(session_id="test1", use_buffer=True)
```

#### `expect_text`
Wait for specific text to appear in the TUI output.

**Parameters:**
- `pattern` (required): Text or regex pattern to wait for
- `session_id` (optional): Session identifier (default: "default")
- `timeout` (optional): Maximum time to wait in seconds (default: 10)

**Example:**
```python
expect_text(pattern="Welcome", session_id="test1", timeout=5)
```

#### `assert_contains`
Assert that the current screen contains specific text.

**Parameters:**
- `text` (required): Text to search for in the current screen
- `session_id` (optional): Session identifier (default: "default")
- `use_buffer` (optional): Check buffer/stream mode. Auto-detects if None (default: None)

**Example:**
```python
assert_contains(text="Counter value: 1", session_id="test1")
```

### Buffer Mode Tools (Position-Based)

#### `assert_at_position`
Assert that specific text appears at a screen position.

**Parameters:**
- `text` (required): Text to verify at the position
- `row` (required): Row number (0-indexed)
- `col` (required): Column number (0-indexed)
- `session_id` (optional): Session identifier (default: "default")

**Example:**
```python
# Verify "Error" appears at row 5, column 10
assert_at_position(text="Error", row=5, col=10, session_id="test1")
```

#### `get_cursor_position`
Get the current cursor position.

**Parameters:**
- `session_id` (optional): Session identifier (default: "default")

**Example:**
```python
get_cursor_position(session_id="test1")
# Returns: "Cursor position (session: test1): row 10, column 25"
```

#### `get_screen_region`
Extract a rectangular region of the screen.

**Parameters:**
- `row_start` (required): Starting row (0-indexed, inclusive)
- `row_end` (required): Ending row (0-indexed, exclusive)
- `col_start` (optional): Starting column (0-indexed, inclusive, default: 0)
- `col_end` (optional): Ending column (0-indexed, exclusive, default: end of line)
- `session_id` (optional): Session identifier (default: "default")

**Example:**
```python
# Extract rows 5-10, full width
get_screen_region(row_start=5, row_end=10, session_id="test1")

# Extract rows 5-10, columns 20-60
get_screen_region(row_start=5, row_end=10, col_start=20, col_end=60, session_id="test1")
```

#### `get_line`
Get a specific line from the screen buffer.

**Parameters:**
- `row` (required): Row number (0-indexed)
- `session_id` (optional): Session identifier (default: "default")

**Example:**
```python
get_line(row=3, session_id="test1")
# Returns: "Line 3 (session: test1): [line content]"
```

## Common Testing Patterns

### Basic CLI Testing (Stream Mode)
```python
# Launch in stream mode (default)
launch_tui(command="python example_tui_app.py")

# Wait for the welcome message
expect_text(pattern="Welcome to the Example TUI Application")

# Select option 1 (Say Hello)
send_keys(keys="1\n")

# Verify the greeting appears
assert_contains(text="Hello, TUI Tester!")

# Select option 3 (Counter)
send_keys(keys="3\n")

# Verify counter incremented
assert_contains(text="Counter value: 1")

# Quit the application
send_keys(keys="q\n")

# Close the session
close_session()
```

### TUI Menu Testing (Buffer Mode)
```python
# Launch in buffer mode for position-aware testing
launch_tui(command="python menu_app.py", mode="buffer", session_id="menu")

# Wait for menu to render
expect_text(pattern="Main Menu", session_id="menu")

# Verify title is at the top
assert_at_position(text="Main Menu", row=0, col=0, session_id="menu")

# Navigate menu with arrow keys
send_keys(keys="\x1b[B", session_id="menu")  # Down arrow
send_keys(keys="\x1b[B", session_id="menu")  # Down arrow

# Check cursor moved
cursor_pos = get_cursor_position(session_id="menu")

# Select menu item
send_keys(keys="\n", session_id="menu")

close_session(session_id="menu")
```

### Multi-Session Testing
```python
# Launch first app in stream mode
launch_tui(command="python cli_tool.py", session_id="app1")

# Launch second app in buffer mode
launch_tui(
    command="htop",
    session_id="app2",
    mode="buffer",
    dimensions="120x40"
)

# List active sessions
list_sessions()
# Should show: app1 (stream), app2 (buffer)

# Interact with first app
send_keys(keys="status\n", session_id="app1")
assert_contains(text="Running", session_id="app1")

# Interact with second app
send_keys(keys="t", session_id="app2")
assert_at_position(text="CPU", row=0, col=0, session_id="app2")

# Close both sessions
close_session(session_id="app1")
close_session(session_id="app2")
```

## Best Practices

1. **Choose the right mode**: Use stream mode for CLI tools and buffer mode for full TUIs
2. **Add appropriate delays**: Some TUI apps need time to render
3. **Use expect_text for async operations**: When waiting for slow operations
4. **Test with appropriate terminal sizes**: Match your target environment
5. **Use sessions for isolation**: Each test can have its own session
6. **Clean up sessions**: Always close when done
7. **Capture screen on failure**: For debugging purposes
8. **Use position-based assertions**: For buffer mode when layout matters

## Technical Details

This skill uses:
- **FastMCP**: For the MCP server implementation
- **pexpect**: For spawning and controlling terminal applications
- **pyte**: For terminal emulation and screen buffer management (buffer mode)
- **ScreenSession wrapper**: Combines pexpect and pyte for hybrid testing

### Architecture
- **Stream Mode**: pexpect directly captures output stream
- **Buffer Mode**: pexpect output → pyte terminal emulator → screen buffer
- **Auto-detection**: Tools automatically use appropriate mode based on session

## Limitations

- Currently designed for Unix-like systems (Linux, macOS)
- Windows support may require modifications (consider using `winpty` or similar)
- Mouse support in TUIs is not currently available
- Buffer mode requires slightly more memory for screen emulation
- Position-based assertions only work in buffer mode

## Use Cases

- **Automated Testing**: Verify TUI applications behave correctly
- **Integration Testing**: Test command-line tools and interactive CLIs
- **Documentation**: Generate screenshots and examples from TUI apps
- **Debugging**: Inspect the state of TUI applications during development
- **CI/CD**: Add TUI testing to your continuous integration pipeline

## Example Test Scenario

Here's how you might use this skill to test a TUI application:

1. **Launch the application**:
   ```python
   launch_tui(command="python example_tui_app.py")
   ```

2. **Wait for it to load**:
   ```python
   expect_text(pattern="Welcome to the Example TUI Application")
   ```

3. **Interact with it**:
   ```python
   send_keys(keys="1\n")
   ```

4. **Verify output**:
   ```python
   assert_contains(text="Hello, TUI Tester!")
   ```

5. **Clean up**:
   ```python
   close_session()
   ```

## Related Projects

- [Playwright](https://playwright.dev/) - Browser automation (inspiration for this project)
- [pexpect](https://pexpect.readthedocs.io/) - Python module for spawning child applications
- [pyte](https://pyte.readthedocs.io/) - Python terminal emulator
- [MCP](https://modelcontextprotocol.io/) - Model Context Protocol specification

## License

MIT License - see LICENSE file for details

## Author

Created for testing TUI applications with AI assistance.
