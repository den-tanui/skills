# Git Integration Patterns

`fzf` is incredibly powerful for navigating git repositories. Here are standard patterns for AI agents to use when building git-related scripts.

## 1. Interactive `git log`

Browse commits and see the diff in the preview window. Pressing enter copies the commit hash.

```bash
git log --color=always --format="%C(auto)%h%d %s %C(black)%C(bold)%cr" "$@" |
  fzf --ansi --no-sort --reverse --tiebreak=index --bind=ctrl-s:toggle-sort \
      --bind "ctrl-m:execute:
                (grep -o '[a-f0-9]\{7\}' | head -1 |
                xargs -I % sh -c 'git show color=always % | less -R') << 'FZF-EOF'
                {}
FZF-EOF" \
      --preview 'grep -o "[a-f0-9]\{7,\}" <<< {} | head -1 | xargs git show --color=always' \
      --bind 'enter:become(grep -o "[a-f0-9]\{7,\}" <<< {} | head -1)'
```

## 2. Interactive `git checkout` (Branches)

Switch branches interactively, showing the git log of the branch in the preview.

```bash
git branch -a --color=always | grep -v '/HEAD\s' | sort |
  fzf --ansi --multi --tac --preview-window right:70% \
      --preview 'git log --oneline --graph --date=short --color=always --pretty="format:%C(auto)%cd %h%d %s" $(sed s/^..// <<< {} | cut -d" " -f1)' |
  sed 's/^..//' | cut -d' ' -f1 |
  sed 's#^remotes/##' |
  xargs git checkout
```

## 3. Interactive `git add` (Staging)

Stage files interactively. Shows the diff of the file in the preview window. Uses `TAB` to select multiple files.

```bash
git -c color.status=always status -s |
  fzf -m --ansi --nth 2..,.. \
      --preview '(git diff --color=always -- {-1} | sed 1,4d; cat {-1})' |
  cut -c4- | sed 's/.* -> //' |
  xargs -I {} git add "{}"
```

## 4. Interactive `git stash`

Browse stashes and apply/drop them.

```bash
git stash list | 
  fzf --reverse -d: --preview 'git show --color=always {1}' \
      --bind 'enter:become(git stash apply {1})' \
      --bind 'ctrl-d:execute(git stash drop {1})+reload(git stash list)'
```
