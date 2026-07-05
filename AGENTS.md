# Agent Instructions — Skills Repository

## When modifying skills

After any **major edit, addition, or deletion** of a skill (SKILL.md, references, or scripts):

1. **Commit with a descriptive message** — the index regeneration runs automatically in CI/CD.

   ```
   feat(skill-name): what changed and why
   ```

2. **Only run `generate-index.js` manually** if the CI/CD pipeline fails:

   ```bash
   node /home/opt/my-skills/generate-index.js
   ```

   Then commit the index update separately with `chore(skill-name): regenerate index`.

## Commit message format

Use imperative mood, describe the *what* and *why*:

```
feat(<scope>): <short description>

- <detail bullet, optional>
- <detail bullet, optional>
```

Examples:

```
feat(herdr-plugin-dev): add manifest reference tables
feat(tmux-herdr-plugin): create new porting skill

- tmux→herdr command mapping for 40+ tmux commands
- spec template and analysis workflow
- ast-grep CLI patterns for complex plugin parsing
```

## Why

The index (`README.md` / `SKILL_INDEX.md`) is the repo's API surface — agents and users
scan it to discover what skills exist. A stale index means skills are invisible. Descriptive
commits make `git log` useful for understanding what evolved, when, and why.
