# Skills Index System

This directory contains an automated system for maintaining an index of all skills.

## How It Works

1. **Generator Script** (`generate-index.js`)
   - Scans all subdirectories for `SKILL.md` files
   - Parses YAML frontmatter (name, description)
   - Generates `README.md` and `SKILL_INDEX.md` with formatted index

2. **Git Hook** (`.git/hooks/pre-commit`)
   - Automatically runs generator when SKILL.md files are modified
   - Stages the updated index files
   - Ensures index is always up-to-date

## Usage

### Automatic (Recommended)
Just commit your changes normally. The pre-commit hook will:
- Detect any SKILL.md modifications
- Regenerate the index
- Stage the updated README.md and SKILL_INDEX.md

### Manual
If you need to regenerate the index manually:
```bash
node generate-index.js
git add README.md SKILL_INDEX.md
```

## Requirements
- Node.js (for the generator script)
- `js-yaml` package (installed automatically by the hook)

## SKILL.md Format

Each skill must have a `SKILL.md` file with YAML frontmatter:

```yaml
---
name: skill-name
description: Short description of what this skill does
---

# Skill Title

Full skill documentation...
```

## Troubleshooting

**Hook not running?**
- Ensure the hook is executable: `chmod +x .git/hooks/pre-commit`
- Check for errors in the hook output during commit

**Index not updating?**
- Verify the SKILL.md file has proper YAML frontmatter
- Check that the file was staged before commit

**Missing dependencies?**
- Run `npm install js-yaml` to install required package

## Files Generated

- `README.md` - Main index (human-readable)
- `SKILL_INDEX.md` - Alternative index file

Both files contain the same content and are kept in sync.

## Disabling the Hook

To temporarily disable the hook:
```bash
mv .git/hooks/pre-commit .git/hooks/pre-commit.disabled
```

To re-enable:
```bash
mv .git/hooks/pre-commit.disabled .git/hooks/pre-commit
```