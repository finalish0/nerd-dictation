# Desktop glue (this fork, branch `local`)

Warm systemd daemon, mic toggle, Sway include. **Not for upstream `main`.**

Users: start at the repo [README.md](../../README.md) and run
`./contrib/desktop/install.sh`.

That script does **not** assume a clone path. It writes
`~/.config/nerd-dictation/env` (`ND`, `PYTHON`) and a user unit.

## Sway (once)

```
include ~/.config/sway/nerd-dictation.conf
bindsym $mod+n exec --no-startup-id ~/.local/bin/nerd-dictation-toggle master
```

`on`/`off` rewrites the include (`Ctrl+Space`). Super+n stays in the main
config. Dictation types into the focused window — no per-app plugin.

## Files

| File | Role |
|---|---|
| `install.sh` | venv, models, user unit, toggle |
| `nerd-dictation.service.in` | unit template (`install.sh` fills paths) |
| `nerd-dictation-toggle` | on / off / master / suspend |
| `sway-nerd-dictation.conf` | seed include; rewritten by the toggle |
| `whisper-rescore-worker.py` | persistent Whisper (spawned by the daemon) |
| `requirements.txt` | `vosk`, `pywhispercpp` |
