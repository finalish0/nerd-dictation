# Changelog (fork branch `local`)

Base: upstream `ideasman42/nerd-dictation` @ `41f3727` (2025-10-10).
Script diff: see `git diff main --stat -- nerd-dictation`.

## 2026-08-31

### Optional Whisper `audio_ctx` from clip length

`NERD_DICTATION_WHISPER_AUDIO_CTX=auto` sets the encoder window from
the WAV duration (~50 frames/s + pad). Short phrases can infer in
~0.5 s instead of ~3 s; quality can drift. Off unless the env is set.
The worker logs `whisper-rescore: 0.51s audio=4.25s ctx=244`.

## 2026-08-31

### Do not kill wtype on send

Freezing the mic used to SIGKILL the current `wtype`. If that was a
Whisper replace, the line had already been backspaced and the first
letters of the new text never arrived. The pad checkmark now waits
~180 ms after suspend before Enter.

## 2026-08-31

### Live VOSK uses the small German model

`--vosk-model-dir` is `vosk-model-small-de-0.15` (~90 MB). The large
`de-0.21` stays on disk. Whisper still rescored finished fragments, so
live quality can be worse and the daemon lighter.

## 2026-08-31

### Faster Backspace burst on Whisper replace

Live word updates keep the slow wtype delays. A whole-phrase rescore
(≥8 deletes) uses a shorter key delay so the old VOSK line is not
visible for so long.

## 2026-08-31

### Freeze VOSK on silence, then Whisper

After ~250 ms quiet, live text stops rewriting. After ~550 ms the
phrase is finalized and Whisper runs. Room noise no longer starts a
new VOSK pass in that gap.

## 2026-08-31

### Whisper replace dropped the first letter in a terminal

A full-phrase rescore is many Backspaces, then the new text (often a
capital). Alacritty drops that first printable. Warm Shift again *after*
the deletes, and do not use the Chrome letter-overlap on this path.

## 2026-08-31

### Whisper rescored per fragment, not the whole take

Each VOSK final is one span. Whisper only rewrites that span and keeps
whatever was typed after it, so a late correction is not dropped when
you already started the next sentence. Room noise (`nein`/`nun` at
low RMS) is not typed and not sent to Whisper. Bracket tags such as
`[Pause]` / `[MUSIK]` / `[Pfiff]` are junk. Worker uses 8 threads and
a higher no-speech threshold.

## 2026-08-31

### Super+n master toggle

Sway `Mod4+n` flips dictation on/off (`nerd-dictation-toggle master`), same
idea as Super+m for the laptop panel. The bind stays in the main Sway
config so it still works when the daemon is off. Ctrl+Space remains the
mic and is unbound while off.

## 2026-08-31

### Whisper phrase post-correction (live VOSK stays)

VOSK still types word-by-word. After a phrase is finalized, a persistent
`whisper-rescore-worker.py` (pywhispercpp, `ggml-small.bin`) re-decodes
that audio and, if the user has not started the next phrase, replaces
the last committed text. Empty/hallucinated Whisper output is dropped.
Suspend/resume bumps `capture_epoch` so a late result cannot type into
the next prompt. The worker stays loaded across freeze (SIGSTOP is only
the main PID). Disable with `--no-whisper` or
`NERD_DICTATION_WHISPER_MODEL` pointing at a missing path.

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
