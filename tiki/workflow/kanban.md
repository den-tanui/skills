# Kanban Workflow — Project SDLC Tracking

This guide maps the bundled **kanban** workflow to a software development life cycle.
The kanban workflow ships with four statuses and four types that map naturally to SDLC phases.

## Statuses (lanes)

| Status | SDLC phase | Meaning |
|---|---|---|
| `inbox` | Triage / backlog | New work captured but not yet committed to a sprint |
| `ready` | Sprint backlog | Refined, estimated, and ready to be picked up |
| `inProgress` | Active development | Someone is actively working on it |
| `done` | Complete | Finished and meets the definition of done |

## Types

| Type | SDLC use |
|---|---|
| `story` | A feature or user-facing deliverable |
| `bug` | A defect to fix |
| `spike` | Research or investigation task |
| `project` | An umbrella that groups related stories, bugs, and spikes via `dependsOn` |

## Priority

Stock priority values (enum, most to least urgent):

`high` > `medium-high` > `medium` (default) > `medium-low` > `low`

Use `next_enum(priority)` / `prev_enum(priority)` to bump up or down.

## Points

Stock estimation values: `1`, `3` (default), `7`, `11`.

---

## SDLC workflow

### 1. Capture (inbox)

New ideas, bugs, and stories land in `inbox` by default.

```sh
tiki exec 'create title="Add OAuth login"'                          # story, defaults to inbox
tiki exec 'create title="Fix crash on export" type="bug" priority="high"'
tiki exec 'create title="Investate migration path" type="spike" tags=["research"]'
```

### 2. Refine and estimate (inbox → ready)

During refinement, set priority, points, and move to `ready`:

```sh
tiki exec 'update where id = "ABC123" set priority="medium-high" points="7" status="ready"'
```

Bulk-promote all high-priority inbox items:

```sh
tiki exec 'update where status = "inbox" and priority = "high" set status="ready"'
```

### 3. Plan with projects

Create a project to group related work, then link tikis to it:

```sh
tiki exec 'create title="Q4 Auth Overhaul" type="project" priority="high" points="11"'
```

Link stories and bugs to the project (run from the TUI with the `a` key on a selected tiki,
or via CLI — you need the project ID):

```sh
tiki exec 'update where id = "DEF456" set dependsOn = dependsOn + ["ABC123"]'
```

View all work linked to a project:

```sh
tiki exec 'select id, title, status, type where "ABC123" in dependsOn order by status, priority'
```

### 4. Sprint (ready → inProgress)

Pick up a task and start work. Assign yourself and move to `inProgress`:

```sh
tiki exec 'update where id = "ABC123" set assignee=user() status="inProgress"'
```

What am I working on right now:

```sh
tiki exec 'select id, title, type, priority where assignee = user() and status = "inProgress" order by priority'
```

### 5. Blocked tasks

Check for tasks blocked by unfinished dependencies:

```sh
tiki exec 'select id, title, status where exists(select where outer.id in dependsOn and status != "done")'
```

List a tiki's dependencies:

```sh
tiki exec 'select id, title, status where id in (select where id = "ABC123").dependsOn'
```

Or from the TUI detail view, press `L` to list dependencies.

### 6. Complete (inProgress → done)

Mark a task done. The kanban workflow enforces that tasks pass through `inProgress` first
(trigger will deny direct inbox→done transitions):

```sh
tiki exec 'update where id = "ABC123" set status="done"'
```

Projects auto-complete when all their child tasks are done (trigger in the stock workflow).

Check what's left on a project:

```sh
tiki exec 'select id, title, status where "ABC123" in dependsOn and status != "done" order by priority'
```

### 7. Review sprint progress

```sh
tiki exec 'select id, title, status, type, priority where status != "done" order by status, priority'

tiki exec 'count(select where status = "done")'                                   # completed count
tiki exec 'count(select where status = "inProgress")'                             # in-flight count
tiki exec 'count(select where status = "ready")'                                  # ready count
tiki exec 'count(select where status != "done")'                                  # remaining count
```

Burndown — remaining vs done grouped by type:

```sh
tiki exec 'select type, count(select where outer.type = type and status = "done"), count(select where outer.type = type and status != "done")'
```

### 8. Recurring tasks

For repeating work (e.g. weekly reviews, monthly dependency audits):

```sh
tiki exec 'create title="Weekly dependency review" recurrence=weekly("monday") status="ready"'
```

When a recurring task is marked `done`, the stock workflow trigger auto-creates the next
occurrence in `inbox` with the same title, priority, tags, and recurrence.

---

## Triggers (built into stock kanban)

| Trigger | Effect |
|---|---|
| Block completion with open dependencies | `deny` if `new.status = "done"` and any `dependsOn` is not `done` |
| Must pass through in-progress | `deny` if moving to `done` without having been `inProgress` |
| Remove deleted from dependency lists | `after delete`, removes the deleted id from all `dependsOn` lists |
| Clean up completed after 24h | `every 1day`, deletes tikis that have been `done` for over 24 hours |
| Must have assignee before starting | `deny` if moving to `inProgress` without an assignee (non-projects) |
| Auto-complete projects | `after update`, marks a project `done` when all its tasks are done |
| Cannot delete in-progress | `deny` if `old.status = "inProgress"` |
| Spawn next recurring occurrence | `after update`, creates next instance when a recurring task completes |

---

## TUI keybindings (kanban board view)

| Key | Action |
|---|---|
| `Enter` | Open selected tiki in detail view |
| `e` | Edit selected tiki |
| `n` | Create new tiki |
| `m` | Assign to me |
| `a` | Add to project (interactive picker) |
| `d` / `D` | Add / remove dependency |
| `+` / `-` | Priority up / down |
| `Delete` | Delete selected tiki |
| `F1` | Kanban board |
| `F2` | Docs/wiki view |
| `F4` | Roadmap (projects by Now/Next/Later) |
| `Ctrl-R` | Recent (changed in last 24h) |

---

## Tips

- **No `tiki init` needed** — just run `tiki` in any directory with `.md` files.
- **Git is read-only** — tiki reads history for timestamps/authorship but never commits.
- **Custom fields** — add project-specific fields (e.g. `severity`, `environment`) in `workflow.yaml`.
- **JSON output** — use `tiki exec --format json '...'` for scripting and CI.
- **Workflow install** — `tiki workflow install kanban --local` to set up in a project.
