# Desktop glue (not upstream)

Machine-side wiring used with this fork’s `local` branch: warm systemd
daemon, mic toggle, Sway key, and “send message → freeze dictation”
hooks. **None of this belongs on `main` or in an upstream PR.**

Paths assume the clone lives at `$HOME/git/nerd-dictation` and the
German VOSK model at `$HOME/.local/share/vosk-models/vosk-model-small-de-0.15`
(large `de-0.21` is still on disk if you want it back).
Edit if yours differ. AhaKey LED pulses are optional (`ahakey.sh`).

## Install (user systemd + toggle)

```sh
install -Dm755 contrib/desktop/nerd-dictation-toggle ~/.local/bin/nerd-dictation-toggle
install -Dm644 contrib/desktop/nerd-dictation.service ~/.config/systemd/user/nerd-dictation.service
systemctl --user daemon-reload
systemctl --user enable --now nerd-dictation
```

Wait until the process is stopped (`nerd-dictation-toggle status` → state `T`/`Ts`) before the first mic press. SIGUSR1 during model load kills the daemon.

Master switch (one command; do not edit Sway by hand after the include is in place):

```sh
nerd-dictation-toggle off     # stop daemon, unbind Ctrl+Space (Grok voice can use it)
nerd-dictation-toggle on      # start daemon, bind Ctrl+Space as the mic
nerd-dictation-toggle master  # flip on/off (Sway Super+n)
nerd-dictation-toggle status
```

`off` writes an empty `~/.config/sway/nerd-dictation.conf` and `unbindsym Ctrl+Space`,
so the combo is not swallowed. `on` puts the bind back. Super+n lives in the main
Sway config so it still works when dictation is off.

The AhaKey **checkmark** is HID Enter. While Super+n dictation is **on**,
`nerd-dictation-toggle` binds *the pad device only* to ahakey-x1
`contrib/pad-enter.sh` (wait for `wtype`, freeze mic, inject Enter) — any
focused app. While dictation is **off**, pad Enter is native again (Croc
Dictator / Grok Voice). Laptop Enter is never stolen.

## Sway

```sh
install -Dm644 contrib/desktop/sway-nerd-dictation.conf ~/.config/sway/nerd-dictation.conf
```

Then in `~/.config/sway/config` (once):

```
include ~/.config/sway/nerd-dictation.conf
bindsym $mod+n exec --no-startup-id ~/.local/bin/nerd-dictation-toggle master
```

The include file is rewritten by `on`/`off` (Ctrl+Space only). Super+n stays in
the main config. Reload once after adding the include.

## OpenCode

Copy `opencode-ahakey-led.js` to `~/.config/opencode/plugins/ahakey-led.js` and restart OpenCode. `chat.message` freezes dictation (SIGSTOP → SIGUSR1 → SIGCONT, 50 ms gaps) and pulses the pad LED.

## Grok Build TUI

Copy `grok-hooks-ahakey-led.json` to `~/.grok/hooks/ahakey-led.json`. New sessions pick it up. `UserPromptSubmit` pulses send and runs `nerd-dictation-toggle suspend`.

## Files

The venv at `$HOME/git/nerd-dictation/.venv` needs `vosk` and
`pywhispercpp`. Whisper post-correction uses
`~/.cache/opencode-voice/models/ggml-small.bin` (or
`NERD_DICTATION_WHISPER_MODEL`). `--no-whisper` turns it off. VOSK remains
the live word-by-word engine; Whisper only rewrites a finished phrase if
you have not started the next one. The unit sets
`NERD_DICTATION_WHISPER_LANG=de` so German stays German; mixed English
still gets a second look.

## Files

| File | Role |
|---|---|
| `nerd-dictation.service` | Warm daemon: VOSK models + Whisper worker, `--suspend-on-start` |
| `nerd-dictation-toggle` | Toggle / `suspend` / `stop`; writes `$XDG_RUNTIME_DIR/nerd-dictation.pid` |
| `sway-nerd-dictation.conf` | `Ctrl+Space` → toggle |
| `opencode-ahakey-led.js` | OpenCode plugin: LED + freeze on send |
| `grok-hooks-ahakey-led.json` | Grok hooks: LED + freeze on submit |
| `whisper-rescore-worker.py` | Persistent Whisper process (READY, then one line per WAV) |
