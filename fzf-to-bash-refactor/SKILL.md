---
name: fzf-to-bash-refactor
description: Convert fzf workflows into portable Bash scripts using numbered menus and read input, removing TUI dependencies while maintaining functionality.
version: 1.0.0
author: AI Assistant
license: MIT
platforms: [linux, macos, unix]
metadata:
  hermes:
    tags: [bash, shell, scripting, fzf, cli, automation]
    related_skills: [bash, shell-scripting, git-workflow]
---

# 🔄 Skill: fzf-to-Bash Refactor (Semi-Interactive)

> **Skill Level:** Intermediate  
> **Target:** Shell scripters, CI/CD engineers, and users who need portable scripts without `fzf` dependencies.  
> **Goal:** Convert complex `fzf` workflows into pure Bash scripts using numbered menus and `read` input, maintaining logic flow while removing TUI dependencies.

---

## 🎯 Core Philosophy

`fzf` is powerful but requires a TTY, a binary dependency, and complex keybindings. This skill teaches you to **deconstruct** `fzf` logic into:

1. **Data Collection:** Gather the list into a Bash array.
2. **Rendering:** Display a numbered list.
3. **Input Parsing:** Handle numbers, ranges, and simple text search via `read`.
4. **Action Execution:** Map selection to commands (mimicking `fzf` bindings).

**Result:** A script that works in any terminal, is easier to debug, and requires zero external binaries.

---

## 🛠️ 1. The Refactor Pattern: `select_menu()`

This is the core engine. It replaces `fzf` with a reusable Bash function.

### The Function

```bash
#!/usr/bin/env bash

# --- Configuration ---
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# --- Core Function: select_menu ---
# Usage: select_menu "Prompt> " < input_stream
# Returns: Selected item via stdout, exit code 0 on success, 1 on cancel/invalid
select_menu() {
  local prompt="${1:-Select> }"
  local -a items=()
  local count=0
  
  # 1. Read all input into an array (Memory: O(N))
  while IFS= read -r line; do
    [[ -z "$line" ]] && continue
    items+=("$line")
    ((count++))
  done

  if [[ $count -eq 0 ]]; then
    echo -e "${RED}No items found.${NC}" >&2
    return 1
  fi

  # 2. Render the Menu
  clear || true # Optional: Clear screen for cleaner UI (use with caution in pipes)
  echo -e "${GREEN}=== Selection Menu (${count} items) ===${NC}"
  echo ""
  for i in "${!items[@]}"; do
    local idx=$((i + 1))
    local display="${items[$i]}"
    # Truncate long lines to prevent wrapping
    if [[ ${#display} -gt 70 ]]; then
      display="${display:0:67}..."
    fi
    printf "%3d. %s\n" "$idx" "$display"
  done
  echo ""

  # 3. Input Loop
  while true; do
    read -rp "$prompt" user_input
    
    # Handle Cancel (Empty or 'q')
    if [[ -z "$user_input" || "$user_input" == "q" ]]; then
      echo -e "${YELLOW}Cancelled.${NC}"
      return 1
    fi

    # --- Logic: Parse Input ---
    
    # A. Single Number (e.g., "1")
    if [[ "$user_input" =~ ^[0-9]+$ ]]; then
      local idx=$((user_input - 1))
      if (( idx >= 0 && idx < count )); then
        echo -e "${GREEN}>> Selected: ${items[$idx]}${NC}"
        echo "${items[$idx]}"
        return 0
      else
        echo -e "${RED}Invalid number (1-${count}). Try again.${NC}"
        continue
      fi
    fi
    
    # B. Range (e.g., "1-3") - Bulk Selection
    if [[ "$user_input" =~ ^([0-9]+)-([0-9]+)$ ]]; then
      local start="${BASH_REMATCH[1]}"
      local end="${BASH_REMATCH[2]}"
      if (( start >= 1 && end <= count && start <= end )); then
        echo -e "${GREEN}>> Range Selected: ${start}-${end}${NC}"
        # Output all items in range (one per line)
        for (( i=start-1; i<end; i++ )); do
          echo "${items[$i]}"
        done
        return 0
      else
        echo -e "${RED}Invalid range (1-${count}). Try again.${NC}"
        continue
      fi
    fi

    # C. Text Search (Fuzzy-lite)
    # Find first item containing the string
    local found_idx=-1
    for i in "${!items[@]}"; do
      if [[ "${items[$i]}" == *"$user_input"* ]]; then
        found_idx=$i
        break
      fi
    done

    if (( found_idx >= 0 )); then
      echo -e "${GREEN}>> Match Found (Index $((found_idx+1))): ${items[$found_idx]}${NC}"
      echo "${items[$found_idx]}"
      return 0
    else
      echo -e "${RED}No match for '${user_input}'. Try a number or substring.${NC}"
    fi
  done
}
```

---

## 🔄 2. Conversion Guide: From `fzf` to `select_menu`

### Scenario A: Simple Selection

**Original fzf:**
```bash
ps -ef | fzf | awk '{print $2}' | xargs kill -9
```

**Refactored Bash:**
```bash
selected=$(ps -ef | tail -n +2 | select_menu "Select Process to Kill> ")
if [[ -n "$selected" ]]; then
  pid=$(echo "$selected" | awk '{print $2}')
  kill -9 "$pid" && echo "Killed PID $pid" || echo "Failed to kill"
fi
```

### Scenario B: Multi-Selection (Ranges)

**Original fzf:**
```bash
# fzf doesn't natively support range selection easily without plugins
# Users usually select one by one or use multi-select mode
```

**Refactored Bash:**
```bash
# Supports "1-5" or "1,3,5" (if logic added)
files=$(find . -name "*.log" | select_menu "Select Logs to Delete> ")
if [[ -n "$files" ]]; then
  echo "$files" | xargs rm -f
fi
```

### Scenario C: "Keybindings" (Action Menu)

**Original fzf:**
```bash
# Press Enter to View, Ctrl-E to Edit, Ctrl-D to Delete
fzf --bind 'enter:execute(vim {}), ctrl-e:execute(code {}), ctrl-d:execute(rm {})'
```

**Refactored Bash:**
```bash
select_action_menu() {
  local -a items=("config.yaml" "script.sh" "data.csv")
  local -a actions=("View" "Edit" "Delete" "Quit")
  
  # 1. Select Item
  local item=$(printf "%s\n" "${items[@]}" | select_menu "Select File> ")
  [[ -z "$item" ]] && return 1
  
  # 2. Select Action
  local action_num=$(printf "%s\n" "${actions[@]}" | select_menu "Action for '$item' (1-4)> ")
  [[ -z "$action_num" ]] && return 1
  
  # 3. Execute
  case "$action_num" in
    1) echo "Viewing: $item"; cat "$item";;
    2) echo "Editing: $item"; $EDITOR "$item";;
    3) echo "Deleting: $item"; rm -f "$item";;
    4) echo "Exiting"; exit 0;;
  esac
}
```

---

## 🐞 3. Debugging & Robustness

### A. Handling Large Lists

`fzf` streams data. `select_menu` loads everything into an array.

- **Limit:** If the list > 5,000 items, the script may slow down.
- **Fix:** Add a `head` limit or pagination.

```bash
# Only show first 500 items
head -n 500 | select_menu "..."
```

### B. Non-Interactive Testing

You can pipe the selection directly for CI/CD testing.

```bash
# Simulate user typing "2"
echo "2" | ./script.sh
```

### C. Color Safety

If the script runs in a non-TTY (e.g., SSH without `-t`), colors might break.

- **Fix:** Check for TTY before printing colors.

```bash
if [[ -t 1 ]]; then
  RED='\033[0;31m'
else
  RED=''
fi
```

---

## 🎨 4. Advanced: Pagination (If List is Huge)

If you must handle > 500 items without loading all into RAM, implement a simple pager.

```bash
# Simplified pager logic
paginate_menu() {
  local page_size=20
  local page=1
  local -a all_items=() # Still needs to read all or stream? 
  # For true streaming, use `less` or `more` logic, but complex in Bash.
  # Recommendation: Limit input size or use `fzf` for huge lists.
}
```

*Note: For very large lists, `fzf` is still superior. This skill is for **moderate** lists (< 2000 items).*

---

## 🧪 5. Complete Example: The "Universal Selector"

A script that can handle processes, files, or git branches with a unified interface.

```bash
#!/usr/bin/env bash
source ./select_menu.sh # Assume the function is in a separate file

show_usage() {
  echo "Usage: $0 [type]"
  echo "  type: proc | file | branch"
  exit 1
}

type="${1:-proc}"

case "$type" in
  proc)
    echo "Loading processes..."
    selected=$(ps -ef | tail -n +2 | select_menu "Kill Process> ")
    if [[ -n "$selected" ]]; then
      pid=$(echo "$selected" | awk '{print $2}')
      read -p "Kill PID $pid? (y/n) " confirm
      [[ "$confirm" == "y" ]] && kill -9 "$pid"
    fi
    ;;
  file)
    echo "Loading files..."
    selected=$(find . -maxdepth 2 -type f | select_menu "Delete File> ")
    if [[ -n "$selected" ]]; then
      rm -i "$selected"
    fi
    ;;
  branch)
    echo "Loading branches..."
    selected=$(git branch --format='%(refname:short)' | select_menu "Checkout Branch> ")
    if [[ -n "$selected" ]]; then
      git checkout "$selected"
    fi
    ;;
  *)
    show_usage
    ;;
esac
```

---

## 📚 6. Quick Reference: fzf vs. Bash Refactor

| fzf Feature | Bash Refactor Equivalent |
| :--- | :--- |
| `fzf` | `select_menu` function |
| `--bind 'enter:...'` | `case` statement after `read` |
| `--bind 'ctrl-r:reload'` | Loop to re-run `select_menu` |
| `--multi` | Input range `1-5` or comma list |
| `--height` | `clear` + `printf` |
| `--preview` | `cat` or `echo` after selection |
| `--query` | Text search in `select_menu` loop |

---

## 💡 Pro Tip: The "Hybrid" Approach

If you want the best of both worlds:

1. **Check for `fzf`**: If present, use it (fast, TUI).
2. **Fallback**: If not, use `select_menu` (portable, text-based).

```bash
if command -v fzf &> /dev/null; then
  # Use fzf
  ps -ef | fzf | awk '{print $2}' | xargs kill -9
else
  # Fallback to Bash
  ps -ef | tail -n +2 | select_menu "Select Process> " | awk '{print $2}' | xargs kill -9
fi
```
