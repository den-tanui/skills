---
name: tiki
description: view, create, update, delete tikis and manage dependencies
allowed-tools: Read, Grep, Glob, Write, Bash(tiki exec:*), Bash(tiki log:*), Bash(tiki blame:*)
license: MIT
---

# tiki

A tiki is a task stored as a plain Markdown file with YAML frontmatter.
`tiki` scans every `.md` under the current directory recursively — no `.doc/` directory, no `tiki init`.
A file becomes a tracked tiki only if its frontmatter carries an `id:`; id-less Markdown is ordinary wiki content.

```
---
id: ABC123
title: Implement search
status: inbox
priority: medium
---
Markdown body here.
```

**Identity**: The `id:` frontmatter field is the sole identity — a bare 6-character uppercase alphanumeric string matching `^[A-Z0-9]{6}$` (e.g. `ABC123`). No `TIKI-` prefix.
Files are saved under human-readable slugs (e.g. `fix-login-bug.md`), so you can rename or move files freely; the `id` is stable.
`tiki` reads git history for authorship and timestamps but never stages or commits on your behalf.

All CRUD operations go through `tiki exec '<ruki-statement>'`.
This handles validation, triggers, file persistence automatically.
Never manually edit tiki files — `tiki exec` does it all.

**Reference docs** (in the tiki repo under `docs/`):
- [Tiki format](https://github.com/boolean-maybe/tiki/blob/main/docs/tiki-format.md) — frontmatter schema, workspace layout, wikilinks
- [Ruki syntax](https://github.com/boolean-maybe/tiki/blob/main/docs/ruki/syntax.md) — full grammar
- [Ruki operators and builtins](https://github.com/boolean-maybe/tiki/blob/main/docs/ruki/operators-and-builtins.md) — all operators and functions
- [Ruki semantics](https://github.com/boolean-maybe/tiki/blob/main/docs/ruki/semantics.md) — evaluation model
- [Ruki triggers](https://github.com/boolean-maybe/tiki/blob/main/docs/ruki/triggers.md) — automation rules
- [Ruki examples](https://github.com/boolean-maybe/tiki/blob/main/docs/ruki/examples.md) — cookbook
- [Workflow format](https://github.com/boolean-maybe/tiki/blob/main/docs/workflow-format.md) — `workflow.yaml` schema and versioning
- [Custom fields](https://github.com/boolean-maybe/tiki/blob/main/docs/customization/custom-fields.md) — defining project-specific fields
- [Customization guide](https://github.com/boolean-maybe/tiki/blob/main/docs/customization/customization.md) — tutorials, action requirements, choose/input actions
- [Configuration](https://github.com/boolean-maybe/tiki/blob/main/docs/config.md) — `config.yaml`, identity resolution, env vars
- [Command line](https://github.com/boolean-maybe/tiki/blob/main/docs/command-line.md) — CLI reference
- [Tips and FAQ](https://github.com/boolean-maybe/tiki/blob/main/docs/tips-tricks-faq.md) — tips and tricks

## Field reference

Fields are **workflow-declared** in `workflow.yaml fields:`. The runtime hardcodes only system fields (`id`, `title`, `description`/`body`, `createdAt`, `updatedAt`, `createdBy`, `filepath`). Everything else is loaded from the `fields:` list and gets type coercion and validation.

| Field | Type | Notes |
|---|---|---|
| `id` | `id` | immutable, auto-generated 6-char uppercase (e.g. `ABC123`) |
| `title` | `string` | required on create (max 200 chars), optional on disk |
| `description` | `string` | markdown body content; not a frontmatter field |
| `status` | `enum` | values from `workflow.yaml`; default on create is the value with `default: true` |
| `type` | `enum` | values from `workflow.yaml`; stock: `story`, `bug`, `spike`, `project` |
| `priority` | `enum` | **string** enum, not int. Stock: `high`, `medium-high`, `medium`, `medium-low`, `low`. Default: `medium` |
| `points` | `enum` | **string** enum, not int. Stock: `1`, `3`, `7`, `11`. Default: `3` |
| `assignee` | `user` | stored as string; `user` type uses suggestion-enabled picker in TUI (0.6.1+) |
| `tags` | `stringList` | set semantics — trimmed, deduped; `+`/`-` are union/difference. Default: `["idea"]` |
| `dependsOn` | `tikiIdList` | list of bare 6-char tiki IDs (e.g. `["ABC123", "DEF456"]`); uppercased, deduped |
| `due` | `date` | `YYYY-MM-DD` format (date only, no time) |
| `recurrence` | `recurrence` | on-disk cron string; author with `daily()`, `weekly("monday")`, `monthly(1)` builtins in ruki |
| `filepath` | `string` | synthetic, read-only — on-disk path of the tiki file |

**Derived fields** (not stored in frontmatter; from git history with mtime fallback):
- `createdAt` / `updatedAt` — commit times, or file mtime when uncommitted/non-repo
- `createdBy` — git author, or tiki identity fallback

Unknown frontmatter keys are preserved untouched. Absence is meaningful: a tiki with no `status` key has no status, not a defaulted one. Use `has(status)` to filter by presence.

Cross-tiki links: reference another tiki by bare id in double brackets — `[[ABC123]]`. Links survive file moves and renames.

## Query

```sh
tiki exec 'select'                                                    # all tasks
tiki exec 'select title, status'                                      # field projection
tiki exec 'select id, title where status = "done"'                    # filter
tiki exec 'select where "bug" in tags order by priority'              # tag filter + sort
tiki exec 'select where due < now()'                                  # overdue
tiki exec 'select where due - now() < 7day'                           # due within 7 days
tiki exec 'select where exists(select where outer.id in dependsOn and status != "done")'  # blocked
tiki exec 'select where assignee = user()'                            # my tasks
tiki exec 'select where status = "ready" order by priority limit 5'   # limit results
tiki exec 'select where has(status) and not has(assignee)'            # has-field checks
```

Output is an ASCII table by default. Use `--format json` for scripting:
```sh
tiki exec --format json 'select id, title where status = "ready"'
```

Use `--` to allow statements starting with `--` (ruki line comments):
```sh
tiki exec -- '-- backlog count
count(select where status != "done")'
```

To read a tiki's full markdown body, find its filepath first, then use `Read`:
```sh
tiki exec 'select filepath where id = "ABC123"'   # get the file path
```

### Condition syntax

Conditions support `and`, `or`, `not`, parentheses, comparisons (`=`, `!=`, `<`, `>`, `<=`, `>=`), `is empty`, `is not empty`, `in`, `not in`, `any`, `all`, and bare boolean expressions.

```sql
select where not (status = "done" or priority = "high")
select where status not in ["done", "inProgress"]
select where dependsOn any status != "done"
select where assignee is empty
select where status = "done"                  -- any boolean expression
```

### Order by and limit

```sql
select order by priority
select where status = "done" order by updatedAt desc
select where "bug" in tags order by priority asc, createdAt desc
select where status != "done" order by priority limit 5
```

## Create

```sh
tiki exec 'create title="Fix login"'                                             # minimal
tiki exec 'create title="Fix login" priority="medium-high" status="ready" tags=["bug"]'  # full
tiki exec 'create title="Review" due=2026-04-01 + 2day'                           # date arithmetic
tiki exec 'create title="Sprint review" recurrence=weekly("monday")'              # recurrence
```

Output: `created ABC123`. Defaults: status from `workflow.yaml` (value with `default: true`), priority `medium`, points `3`, tags `["idea"]`.

### Create from file

When asked to create a tiki from a file:
1. Read the source file
2. Summarize its content into a short title
3. Use the file content as the description:
   ```sh
   tiki exec 'create title="Summary of file" description="<escaped content>"'
   ```
Escape double quotes in the content with backslash.

## Update

```sh
tiki exec 'update where id = "ABC123" set status="done"'                   # status change
tiki exec 'update where id = "ABC123" set priority="high"'                   # priority (string enum)
tiki exec 'update where status = "ready" set status="inbox"'             # bulk update
tiki exec 'update where id = "ABC123" set tags=tags + ["urgent"]'           # add tag (set union)
tiki exec 'update where id = "ABC123" set tags=tags - ["urgent"]'           # remove tag (set difference)
tiki exec 'update where id = "ABC123" set due=2026-04-01'                   # set due date
tiki exec 'update where id = "ABC123" set due=empty'                        # clear due date
tiki exec 'update where id = "ABC123" set recurrence=daily()'               # set recurrence
tiki exec 'update where id = "ABC123" set recurrence=empty'                 # clear recurrence
tiki exec 'update where id in ids() set status="done"'                      # multi-selection
```

Output: `updated N tasks`.

## Delete

```sh
tiki exec 'delete where id = "ABC123"'
```

## Ruki builtins reference

| Builtin | Returns | Notes |
|---|---|---|
| `count(select ...)` | `int` | subquery count; valid as top-level expression |
| `exists(select ...)` | `bool` | true if any match; valid as top-level expression |
| `has(field)` | `bool` | true if field has an explicit value (distinguishes absent from zero) |
| `now()` | `timestamp` | current time |
| `next_date(recurrence)` | `date` | next occurrence from a recurrence value |
| `daily()` | `recurrence` | daily cron pattern |
| `weekly("monday")` | `recurrence` | weekly on a weekday (case-insensitive) |
| `monthly(1)` | `recurrence` | monthly on a day-of-month (1..31) |
| `next_enum(priority)` | same enum | next value in declared order, clamping at last |
| `prev_enum(priority)` | same enum | previous value, clamping at first |
| `id()` | `id` | plugin runtime only; requires exactly one selected tiki |
| `ids()` | `list<ref>` | plugin runtime only; all selected tiki IDs |
| `selected_count()` | `int` | plugin runtime only; number of selected tikis |
| `filepath()` | `string` | plugin runtime only; absolute path of the one selected tiki |
| `filepaths()` | `list<string>` | plugin runtime only; absolute paths of all selected tikis |
| `input()` | declared type | plugin actions with `input:` declaration only |
| `choose(select ...)` | `ref` | plugin runtime only; opens interactive task picker |
| `user()` | `string` | current identity (config → git → OS) |
| `call("cmd")` | `string` | shell command (currently rejected by validation) |

`id()`, `ids()`, `filepath()`, `filepaths()`, `selected_count()`, `choose()`, `input()` are plugin-runtime only — rejected in CLI and triggers.

## Advanced ruki

### Top-level expressions

Ruki statements can be bare expressions returning scalars or lists:
```sh
tiki exec 'count(select where status != "done")'
tiki exec 'exists(select where priority = "high")'
tiki exec 'count(select where status = "done") + count(select where status = "ready")'
```

### Pipe syntax

Pipe select results to external handlers:
```sh
tiki exec 'select id, title where status = "done" | run("myscript $1 $2")'
tiki exec 'select id where id = "ABC123" | clipboard()'
tiki exec 'select filepath | run("some-app $1")'
```

### Qualifiers

- `old.` / `new.` — previous/proposed field values in trigger conditions and actions
- `outer.` — parent-query row inside `count()`/`choose()`/`exists()` subqueries
- `target.` / `targets.` — selected task(s) in plugin runtime

```sql
select where count(select where assignee = outer.assignee and status = "inProgress") >= 3
select where not exists(select where outer.id in dependsOn)
```

### Triggers

Automation rules in `workflow.yaml`:
```yaml
triggers:
  - before update where new.type = "project" and exists(select where id in new.dependsOn and status != "done") deny "project has unfinished dependencies"
  - after update where new.status = "inProgress" run("echo hello")
```

See [Triggers docs](https://github.com/boolean-maybe/tiki/blob/main/docs/ruki/triggers.md).

### `user()` identity resolution

`user()` resolves through: `identity.name`/`identity.email` in `config.yaml` → `git config user.name` → OS username.
Set `TIKI_IDENTITY_NAME` / `TIKI_IDENTITY_EMAIL` env vars to override. Errors if none resolves.

### Environment variable overrides

Every `config.yaml` setting can be overridden with a `TIKI_*` variable:
`store.git` → `TIKI_STORE_GIT`, `appearance.theme` → `TIKI_APPEARANCE_THEME`, etc.

## Workflow management

```sh
tiki workflow install kanban --local       # install a bundled workflow
tiki workflow install ./custom.yaml --local  # install from local file
tiki workflow install https://example.com/wf.yaml --global  # from URL
tiki workflow describe bug-tracker         # describe a workflow
tiki workflow reset --global               # reset to defaults
```

Custom fields and types are defined in `workflow.yaml`. Supported field types: `text`, `user`, `integer`, `boolean`, `date`, `datetime`, `enum`, `stringList`, `tikiIdList`, `recurrence`.

Bundled workflows: `todo` (minimal 2-lane), `kanban` (5-status board), `bug-tracker` (triage with severity/SLA).

See [Workflow format](https://github.com/boolean-maybe/tiki/blob/main/docs/workflow-format.md) for the full schema.

### Implement

When asked to implement a tiki and the user approves implementation, set its status to `inProgress`:
```sh
tiki exec 'update where id = "ABC123" set status="inProgress"'
```
