# Process Management Patterns

`fzf` is excellent for managing system processes, allowing you to search, preview, and send signals to processes interactively.

## 1. Interactive `kill`

Search through running processes and kill the selected ones. Supports multi-selection (`TAB`).

```bash
# List processes, fuzzy find, and kill selected
# Uses `ps -ef`, extracts the PID (awk '{print $2}'), and kills it.
(date; ps -ef) |
  fzf --bind='ctrl-r:reload(date; ps -ef)' \
      --header=$'Press CTRL-R to reload\n\n' --header-lines=2 \
      --preview='echo {}' --preview-window=down,3,wrap \
      --layout=reverse --multi \
      --height=80% | awk '{print $2}' | xargs -r kill -9
```

## 2. Systemd Service Management

Manage systemd services interactively.

```bash
# Select a service to restart
systemctl list-units --type=service --all --no-pager --no-legend | 
  awk '{print $1}' | 
  fzf --preview 'systemctl status {}' \
      --bind 'enter:become(sudo systemctl restart {})' \
      --header "Select a service to restart"
```

## 3. Docker Container Management

Manage Docker containers interactively.

```bash
# Stop/Remove Docker containers
docker ps -a --format "table {{.ID}}\t{{.Names}}\t{{.Status}}\t{{.Image}}" |
  fzf --header-lines=1 \
      --multi \
      --preview 'docker logs {1} | tail -n 50' \
      --bind 'ctrl-s:execute(docker stop {1})+reload(docker ps -a --format "table {{.ID}}\t{{.Names}}\t{{.Status}}\t{{.Image}}")' \
      --bind 'ctrl-r:execute(docker rm {1})+reload(docker ps -a --format "table {{.ID}}\t{{.Names}}\t{{.Status}}\t{{.Image}}")' \
      --bind 'enter:become(docker exec -it {1} sh)'
```

## 4. Log Tailing (Kubernetes Pods)

Use the `follow` flag in `--preview-window` to tail logs in real-time.

```bash
# Browse Kubernetes pods and tail their logs
kubectl get pods --all-namespaces |
  fzf --info=inline --layout=reverse --header-lines=1 \
      --prompt "Pods> " \
      --header $'╱ Enter (kubectl exec) ╱ CTRL-O (open log in editor) ╱ CTRL-R (reload) ╱\n\n' \
      --bind 'start,ctrl-r:reload:kubectl get pods --all-namespaces' \
      --bind 'ctrl-/:change-preview-window(80%,border-bottom|hidden|)' \
      --bind 'enter:execute:kubectl exec -it --namespace {1} {2} -- bash' \
      --bind 'ctrl-o:execute:${EDITOR:-vim} <(kubectl logs --all-containers --namespace {1} {2})' \
      --preview-window up:follow \
      --preview 'kubectl logs --follow --all-containers --tail=10000 --namespace {1} {2}'
```
