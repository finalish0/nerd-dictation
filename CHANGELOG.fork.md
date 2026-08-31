# Changelog (fork branch `local`)

Base: upstream `ideasman42/nerd-dictation` @ `41f3727` (2025-10-10).
Script diff: **+241 / −36** lines in `nerd-dictation`.

## 2026-08-31

### Dual models (German + English)

Optional second VOSK model (`--vosk-en-model-dir`, small `en-us` by default).
The same audio is decoded twice. High-confidence English words can replace
weak German guesses (`commit` instead of `komme mit`). Short German
function words stay German. Extra RAM is modest (small EN ~40 MB on disk).

## 2026-08-31

### Leftover fragment of the previous sentence on the next recording

After stop/send, the submitted text was correct. Starting the mic again
often typed a scrap of the last sentence (USB DMA / PipeWire buffer on a
Samson Meteor, plus in-flight `AcceptWaveform` after `SIGCONT`).

- Suspend no longer flushes `FinalResult()`.
- `capture_epoch` drops emits from the previous session.
- New `KaldiRecognizer` on resume.
- Discard ~500 ms of capture preroll (`NERD_DICTATION_PREROLL_SEC`).
- `parec --latency-msec=20` instead of `--latency=10` (that was 10 bytes).
- Reap the old `parec` on resume; do not `wait()` in the signal handler.

Repro: eSpeak → virtual Pulse sink → nerd-dictation STDOUT.

### Chrome swallows spaces

In a normal Chrome tab (e.g. the Poolsound composer),

`ich erzähle eine kleine geschichte über eine ente`

became

`icherzähleeinekleinegeschichteübereineente`.

Each `wtype` process uploads a new virtual-keyboard keymap. Progressive
emits are `" erzähle"` — the leading space is the first key and is
dropped. Terminals and Chrome `--app` windows do not do this.

- Trailing space on screen; `text_prev` accounts for it.
- Overlap the last letter: `"e über "` instead of `" über "`.
- `build_wtype_args`: Shift warmup, leading blanks as `-k space`, remainder
  after `--`.

Repro: React `<textarea>` in a real Chrome tab, word-by-word like
nerd-dictation. Old path: concatenated. Overlap path: spaces and umlauts
intact.

### wtype on Sway

- `Popen` instead of `check_output` so suspend can kill an in-flight wtype
  (`wtype_fail_ignored`).
- `in_emit` / `abort_assign`: no replay of backspaces + old text if
  `SIGUSR1` lands mid-emit.

### Debug

`[nd-debug]` on stderr (emit / suspend_pause / suspend_resume / preroll).
Under systemd: `journalctl --user -u nerd-dictation`.

## 2026-08-30

First warm-daemon setup (not in this repo): systemd user unit with
`--suspend-on-start`, toggle script, Sway `Ctrl+Space`, wtype as the input
tool, German VOSK model. A lot of the signal and wtype hardening comes
from that day.

## Not on `main` (desktop glue on `local`)

Shipped under `contrib/desktop/` on this branch only:

- `nerd-dictation-toggle`
- systemd user unit (`nerd-dictation.service`)
- Sway `Ctrl+Space` snippet
- OpenCode plugin + Grok `UserPromptSubmit` freeze
