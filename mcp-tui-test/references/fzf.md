# Testing fzf with MCP TUI Test

This guide shows how to use the MCP TUI Test server to test [fzf](https://github.com/junegunn/fzf), a popular command-line fuzzy finder.

## Prerequisites

1. Install fzf on your system:
   ```bash
   # macOS
   brew install fzf
   
   # Linux (Debian/Ubuntu)
   sudo apt-get install fzf
   
   # Or from source
   git clone --depth 1 https://github.com/junegunn/fzf.git ~/.fzf
   ~/.fzf/install
   ```

2. Ensure the MCP TUI Test server is running

## Basic fzf Testing

### Example 1: Simple fzf Search

```python
# Launch fzf with some input
launch_tui(command="echo -e 'apple\nbanana\ncherry\ndate' | fzf", 
           session_id="fzf_test",
           mode="buffer",
           dimensions="80x24")

# Wait for fzf to start
expect_text(pattern=">", session_id="fzf_test", timeout=2)

# Type search query
send_keys(keys="app", session_id="fzf_test")

# Wait for results to filter
expect_text(pattern="apple", session_id="fzf_test", timeout=1)

# Verify apple is highlighted (should be at the top)
assert_at_position(text="apple", row=1, col=0, session_id="fzf_test")

# Select the item (Enter)
send_keys(keys="\n", session_id="fzf_test")

# Wait for selection to complete
expect_text(pattern="apple", session_id="fzf_test", timeout=1)

# Close session
close_session(session_id="fzf_test")
```

### Example 2: Testing fzf Navigation

```python
# Launch fzf with multiple items
launch_tui(command="seq 1 20 | fzf", 
           session_id="fzf_nav",
           mode="buffer",
           dimensions="80x24")

# Wait for fzf to start
expect_text(pattern=">", session_id="fzf_nav", timeout=2)

# Navigate down with arrow keys
send_keys(keys="\x1b[B", session_id="fzf_nav")  # Down arrow
send_keys(keys="\x1b[B", session_id="fzf_nav")  # Down arrow

# Check cursor position
cursor_pos = get_cursor_position(session_id="fzf_nav")
# Should show cursor at row 2 (0-indexed)

# Navigate up
send_keys(keys="\x1b[A", session_id="fzf_nav")  # Up arrow

# Verify cursor moved back
cursor_pos = get_cursor_position(session_id="fzf_nav")

# Exit without selection (Ctrl+C)
send_ctrl(key="c", session_id="fzf_nav")

close_session(session_id="fzf_nav")
```

### Example 3: Testing fzf Preview

```python
# Launch fzf with preview (shows file content)
launch_tui(command="find . -type f | fzf --preview 'cat {}'", 
           session_id="fzf_preview",
           mode="buffer",
           dimensions="120x40")

# Wait for fzf to start
expect_text(pattern=">", session_id="fzf_preview", timeout=3)

# Type to filter files
send_keys(keys="test", session_id="fzf_preview")

# Wait for preview to appear
expect_text(pattern="Preview:", session_id="fzf_preview", timeout=2)

# Verify preview region contains file content
preview_region = get_screen_region(
    row_start=10, 
    row_end=30, 
    col_start=0, 
    col_end=120,
    session_id="fzf_preview"
)

# Should contain file content
assert "#" in preview_region or "def" in preview_region

# Exit
send_ctrl(key="c", session_id="fzf_preview")

close_session(session_id="fzf_preview")
```

### Example 4: Testing fzf Multi-Selection

```python
# Launch fzf with multi-selection enabled
launch_tui(command="seq 1 10 | fzf --multi", 
           session_id="fzf_multi",
           mode="buffer",
           dimensions="80x24")

# Wait for fzf to start
expect_text(pattern=">", session_id="fzf_multi", timeout=2)

# Select first item with Tab
send_keys(keys="\t", session_id="fzf_multi")

# Navigate down
send_keys(keys="\x1b[B", session_id="fzf_multi")

# Select second item with Tab
send_keys(keys="\t", session_id="fzf_multi")

# Verify both items are marked (should show > at the beginning)
region = get_screen_region(row_start=1, row_end=3, session_id="fzf_multi")
assert ">" in region

# Confirm selection (Enter)
send_keys(keys="\n", session_id="fzf_multi")

# Verify multiple items were selected
output = capture_screen(session_id="fzf_multi")
assert "1" in output and "2" in output

close_session(session_id="fzf_multi")
```

### Example 5: Testing fzf with Custom Options

```python
# Launch fzf with custom options
launch_tui(command="history | fzf --height 40% --reverse --border", 
           session_id="fzf_custom",
           mode="buffer",
           dimensions="80x24")

# Wait for fzf to start
expect_text(pattern=">", session_id="fzf_custom", timeout=2)

# Verify border is present
assert_at_position(text="┌", row=0, col=0, session_id="fzf_custom")
assert_at_position(text="└", row=9, col=0, session_id="fzf_custom")  # 40% of 24 = ~10 rows

# Type to search history
send_keys(keys="git", session_id="fzf_custom")

# Exit
send_ctrl(key="c", session_id="fzf_custom")

close_session(session_id="fzf_custom")
```

## Advanced fzf Testing

### Example 6: Testing fzf with External Command

```python
# Create a test file
write_file("test_items.txt", "apple\nbanana\ncherry\ndate\nelderberry\nfig")

# Launch fzf reading from file
launch_tui(command="cat test_items.txt | fzf", 
           session_id="fzf_file",
           mode="buffer",
           dimensions="80x24")

# Wait for fzf to start
expect_text(pattern=">", session_id="fzf_file", timeout=2)

# Search for items starting with 'e'
send_keys(keys="^e", session_id="fzf_file")

# Verify only 'elderberry' appears (exact match)
region = get_screen_region(row_start=1, row_end=5, session_id="fzf_file")
assert "elderberry" in region
assert "apple" not in region

# Exit
send_ctrl(key="c", session_id="fzf_file")

close_session(session_id="fzf_file")

# Clean up
bash("rm test_items.txt")
```

### Example 7: Testing fzf Key Bindings

```python
# Launch fzf
launch_tui(command="seq 1 10 | fzf", 
           session_id="fzf_keys",
           mode="buffer",
           dimensions="80x24")

# Wait for fzf to start
expect_text(pattern=">", session_id="fzf_keys", timeout=2)

# Test toggle selection (Tab)
send_keys(keys="\t", session_id="fzf_keys")

# Test toggle all (Ctrl+A)
send_ctrl(key="a", session_id="fzf_keys")

# Verify all items are selected
region = get_screen_region(row_start=1, row_end=10, session_id="fzf_keys")
# Count occurrences of ">" which indicates selection
selection_count = region.count(">")
assert selection_count >= 5  # Should have multiple selections

# Test clear selection (Ctrl+D)
send_ctrl(key="d", session_id="fzf_keys")

# Verify selections are cleared
region = get_screen_region(row_start=1, row_end=10, session_id="fzf_keys")
selection_count = region.count(">")
assert selection_count == 0

# Exit
send_ctrl(key="c", session_id="fzf_keys")

close_session(session_id="fzf_keys")
```

### Example 8: Testing fzf with Different Input Sources

```python
# Test fzf with process substitution
launch_tui(command="fzf < <(echo -e 'item1\nitem2\nitem3')", 
           session_id="fzf_proc",
           mode="buffer",
           dimensions="80x24")

# Wait for fzf to start
expect_text(pattern=">", session_id="fzf_proc", timeout=2)

# Verify items are loaded
assert_contains(text="item1", session_id="fzf_proc")
assert_contains(text="item2", session_id="fzf_proc")

# Exit
send_ctrl(key="c", session_id="fzf_proc")

close_session(session_id="fzf_proc")
```

## Tips for fzf Testing

1. **Use buffer mode**: fzf is a full TUI application, so buffer mode works best
2. **Add delays**: fzf may need time to process input and update the display
3. **Test with realistic data**: Use actual file lists or command output for realistic testing
4. **Verify cursor position**: Important for navigation testing
5. **Test key bindings**: fzf has many keyboard shortcuts to test
6. **Test preview functionality**: If your fzf setup uses preview
7. **Test multi-selection**: Important for file selection scenarios
8. **Test different options**: fzf has many command-line options to configure behavior

## Common fzf Key Bindings to Test

| Key | Description | Escape Sequence |
|-----|-------------|------------------|
| Enter | Select item | `\n` |
| Tab | Toggle selection | `\t` |
| Shift+Tab | Toggle selection backward | `\x1b[Z` |
| Ctrl+A | Select all | `send_ctrl('a')` |
| Ctrl+D | Deselect all | `send_ctrl('d')` |
| Ctrl+K | Delete forward | `send_ctrl('k')` |
| Ctrl+U | Delete backward | `send_ctrl('u')` |
| Ctrl+C | Exit | `send_ctrl('c')` |
| Ctrl+R | Reload | `send_ctrl('r')` |
| Up Arrow | Move up | `\x1b[A` |
| Down Arrow | Move down | `\x1b[B` |
| Right Arrow | Move right | `\x1b[C` |
| Left Arrow | Move left | `\x1b[D` |

## Testing fzf in Different Scenarios

### File Selection
```python
# Test file selection with fzf
launch_tui(command="find . -name '*.py' | fzf", 
           session_id="fzf_files",
           mode="buffer",
           dimensions="80x24")

# Wait for fzf to start
expect_text(pattern=">", session_id="fzf_files", timeout=3)

# Search for specific file
send_keys(keys="server", session_id="fzf_files")

# Verify file appears in results
assert_contains(text="server.py", session_id="fzf_files")

# Select file
send_keys(keys="\n", session_id="fzf_files")

# Verify selection
output = capture_screen(session_id="fzf_files")
assert "server.py" in output

close_session(session_id="fzf_files")
```

### Command History
```python
# Test command history with fzf
launch_tui(command="history | fzf", 
           session_id="fzf_history",
           mode="buffer",
           dimensions="80x24")

# Wait for fzf to start
expect_text(pattern=">", session_id="fzf_history", timeout=2)

# Search for git commands
send_keys(keys="git", session_id="fzf_history")

# Verify git commands appear
assert_contains(text="git", session_id="fzf_history")

# Exit
send_ctrl(key="c", session_id="fzf_history")

close_session(session_id="fzf_history")
```

### Process Selection
```python
# Test process selection with fzf
launch_tui(command="ps aux | fzf", 
           session_id="fzf_ps",
           mode="buffer",
           dimensions="120x40")

# Wait for fzf to start
expect_text(pattern=">", session_id="fzf_ps", timeout=3)

# Search for python processes
send_keys(keys="python", session_id="fzf_ps")

# Verify python processes appear
assert_contains(text="python", session_id="fzf_ps")

# Exit
send_ctrl(key="c", session_id="fzf_ps")

close_session(session_id="fzf_ps")
```

## Debugging fzf Tests

If your fzf tests aren't working as expected:

1. **Capture screen output**: Use `capture_screen()` to see what fzf is displaying
2. **Check cursor position**: Use `get_cursor_position()` to verify navigation
3. **Extract regions**: Use `get_screen_region()` to examine specific parts of the display
4. **Verify input**: Make sure your key sequences are correct
5. **Add delays**: fzf may need time to process input
6. **Check dimensions**: Ensure your terminal size is appropriate for the test

## Performance Considerations

- fzf can be slow with large input sets (thousands of items)
- Consider using smaller test datasets for faster testing
- Add appropriate timeouts for operations that may take longer
- Use `expect_text()` with reasonable timeouts to avoid test failures

## Best Practices for fzf Testing

1. **Use realistic but small datasets**: 10-20 items is usually enough for testing
2. **Test common use cases**: Search, navigation, selection, multi-selection
3. **Test edge cases**: Empty input, single item, exact matches
4. **Test different fzf options**: `--multi`, `--reverse`, `--border`, etc.
5. **Test key bindings**: Both default and custom bindings
6. **Clean up after tests**: Close sessions and remove temporary files
7. **Use descriptive session IDs**: Helps with debugging multiple fzf instances
8. **Add appropriate delays**: Especially after sending input

## Related Resources

- [fzf GitHub Repository](https://github.com/junegunn/fzf)
- [fzf Wiki](https://github.com/junegunn/fzf/wiki)
- [fzf Key Bindings](https://github.com/junegunn/fzf#key-bindings)
- [fzf Options](https://github.com/junegunn/fzf#usage)

This guide provides a comprehensive approach to testing fzf using the MCP TUI Test server. The examples cover basic functionality, navigation, selection, and advanced features like preview and multi-selection.