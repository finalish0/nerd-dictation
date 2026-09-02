# Desktop glue (this fork, branch `local`)

Warm systemd daemon, mic toggle, Sway include. **Not for upstream `main`.**

Users: start at the repo [README.md](../../README.md) and run
`./contrib/desktop/install.sh`.

That script is the install. It does **not** assume `$HOME/git/nerd-dictation`.
AhaKey LED / pad-enter are optional (detected if `~/git/ahakey-x1` exists).

## Sway (once)

```
include ~/.config/sway/nerd-dictation.conf
bindsym $mod+n exec --no-startup-id ~/.local/bin/nerd-dictation-toggle master
```

`on`/`off` rewrites the include (`Ctrl+Space`, and pad Enter only while
dictation is on). Super+n stays in the main config.

## Optional hooks

`opencode-ahakey-led.js` and `grok-hooks-ahakey-led.json` freeze dictation
when that app sends a message. Copy only if you use those tools. Crush and
any other focused window need nothing extra: nerd-dictation types keys.

## Files

| File | Role |
|---|---|
| `install.sh` | venv, models, user unit, toggle |
| `nerd-dictation.service.in` | unit template (`install.sh` fills paths) |
| `nerd-dictation-toggle` | on / off / master / suspend |
| `sway-nerd-dictation.conf` | seed include; rewritten by the toggle |
| `whisper-rescore-worker.py` | persistent Whisper (spawned by the daemon) |
| `requirements.txt` | `vosk`, `pywhispercpp` |
