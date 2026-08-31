# Änderungsprotokoll (Fork `local`)

Basis: upstream `ideasman42/nerd-dictation` @ `41f3727` (2025-10-10).
Diff am Script: **+241 / −36** Zeilen in `nerd-dictation`.

## 2026-08-31

### Satz-Rest in der nächsten Aufnahme

Nach Stopp/Senden stimmte der abgeschickte Text. Beim nächsten Mic-Start
landete oft ein Fragment des letzten Satzes (USB-DMA / PipeWire-Puffer am
Samson Meteor, plus in-flight `AcceptWaveform` nach `SIGCONT`).

- Suspend flusht **kein** `FinalResult()` mehr.
- `capture_epoch`: Emits aus der vorigen Session werden verworfen.
- Neues `KaldiRecognizer`-Objekt beim Resume.
- ~500 ms Capture-Preroll verwerfen (`NERD_DICTATION_PREROLL_SEC`).
- `parec --latency-msec=20` statt `--latency=10` (10 Byte).
- Altes `parec` wird auf Resume reaped, nicht im Signal-Handler `wait()`.

Repro: eSpeak → virtuelle Pulse-Senke → nerd-dictation STDOUT.

### Chrome schluckt Leerzeichen

In normalen Chrome-Tabs (z. B. Poolsound-Composer) wurde

`ich erzähle eine kleine geschichte über eine ente`

zu

`icherzähleeinekleinegeschichteübereineente`.

Ursache: jeder `wtype`-Prozess lädt eine neue Virtual-Keyboard-Keymap.
Progressive Emits sind `" erzähle"` — führendes Space ist erstes Zeichen
und fällt weg. Im Terminal und in Chrome-`--app`-Fenstern nicht.

- Trailing-Space auf dem Screen, `text_prev` kennt den Space.
- Overlap des letzten Buchstabens: `"e über "` statt `" über "`.
- `build_wtype_args`: Shift-Warmup, Leading-Blanks als `-k space`, Rest
  hinter `--`.

Repro: React-`<textarea>` in einem echten Chrome-Tab, Satz Wort für Wort
wie nerd-dictation. Alt: zusammengeklebt. Overlap: mit Spaces und Umlauten.

### wtype unter Sway

- `Popen` statt `check_output`, damit Suspend ein laufendes wtype killen
  kann (`wtype_fail_ignored`).
- `in_emit` / `abort_assign`: kein Replay von Backspaces + altem Text,
  wenn `SIGUSR1` mitten im Emit kommt.

### Debug

`[nd-debug]` auf stderr (emit / suspend_pause / suspend_resume / preroll).
Unter systemd: `journalctl --user -u nerd-dictation`.

## 2026-08-30

Erstes Warm-Daemon-Setup (nicht in diesem Repo): systemd-User-Unit mit
`--suspend-on-start`, Toggle-Skript, Sway `Ctrl+Space`, wtype als
Input-Tool, deutsches VOSK-Modell. Viele der Signal- und wtype-Härten
stammen aus dem Tag.

## Nicht in diesem Fork

- `~/.local/bin/nerd-dictation-toggle`
- `~/.config/systemd/user/nerd-dictation.service`
- Sway-Binding, AhaKey-LED
- OpenCode-Plugin / Grok-Hook `UserPromptSubmit` → Suspend
