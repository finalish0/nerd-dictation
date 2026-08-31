# Desktop glue (not upstream)

Machine-side wiring used with this fork’s `local` branch: warm systemd
daemon, mic toggle, Sway key, and “send message → freeze dictation”
hooks. **None of this belongs on `main` or in an upstream PR.**

Paths assume the clone lives at `$HOME/git/nerd-dictation` and the
German VOSK model at `$HOME/.local/share/vosk-models/vosk-model-de-0.21`.
Edit if yours differ. AhaKey LED pulses are optional (`ahakey.sh`).

## Install (user systemd + toggle)

```sh
install -Dm755 contrib/desktop/nerd-dictation-toggle ~/.local/bin/nerd-dictation-toggle
install -Dm644 contrib/desktop/nerd-dictation.service ~/.config/systemd/user/nerd-dictation.service
systemctl --user daemon-reload
systemctl --user enable --now nerd-dictation
```

Wait until the process is stopped (`nerd-dictation-toggle status` → state `T`/`Ts`) before the first mic press. SIGUSR1 during model load kills the daemon.

Master switch (no Sway edits; Ctrl+Space stays bound but does nothing while off):

```sh
nerd-dictation-toggle off     # disable --now, mic is a no-op
nerd-dictation-toggle on      # enable --now, wait for the model, then mic works
nerd-dictation-toggle status
```

The AhaKey **checkmark** (Enter) is wired in ahakey-x1 `contrib/pad-enter.sh`:
it calls `nerd-dictation-toggle suspend` first, then send/focus.

## Sway

```sh
install -Dm644 contrib/desktop/sway-nerd-dictation.conf ~/.config/sway/nerd-dictation.conf
```

Then in `~/.config/sway/config`:

```
include ~/.config/sway/nerd-dictation.conf
```

Reload: `swaymsg reload`. AhaKey mic is bound to `Ctrl+Space`.

## OpenCode

Copy `opencode-ahakey-led.js` to `~/.config/opencode/plugins/ahakey-led.js` and restart OpenCode. `chat.message` freezes dictation (SIGSTOP → SIGUSR1 → SIGCONT, 50 ms gaps) and pulses the pad LED.

## Grok Build TUI

Copy `grok-hooks-ahakey-led.json` to `~/.grok/hooks/ahakey-led.json`. New sessions pick it up. `UserPromptSubmit` pulses send and runs `nerd-dictation-toggle suspend`.

## Files

| File | Role |
|---|---|
| `nerd-dictation.service` | Warm daemon: model preloaded, `--suspend-on-start`, mic closed |
| `nerd-dictation-toggle` | Toggle / `suspend` / `stop`; writes `$XDG_RUNTIME_DIR/nerd-dictation.pid` |
| `sway-nerd-dictation.conf` | `Ctrl+Space` → toggle |
| `opencode-ahakey-led.js` | OpenCode plugin: LED + freeze on send |
| `grok-hooks-ahakey-led.json` | Grok hooks: LED + freeze on submit |
