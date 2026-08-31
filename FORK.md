# This fork (`finalish0/nerd-dictation`)

Fork of [ideasman42/nerd-dictation](https://github.com/ideasman42/nerd-dictation)
(offline speech-to-text via VOSK). The working patches live on branch
**`local`**. Branch **`main`** tracks upstream and stays clean for rebases.

| Branch | Contents |
|---|---|
| `main` | Unmodified upstream |
| `local` | This fork’s runtime fixes (Wayland/wtype, Chrome spaces, suspend/resume) |

Checkout:

```sh
git clone -b local https://github.com/finalish0/nerd-dictation.git
```

Sync with upstream later:

```sh
git fetch upstream
git checkout main
git merge --ff-only upstream/main
git checkout local
git merge main   # then resolve if needed
```

## What we actually changed

Only the script `nerd-dictation` is patched (+241 / −36 vs upstream
`41f3727`). Machine-specific glue (systemd user unit, AhaKey toggle,
OpenCode/Grok send-to-suspend) is **not** in this repository.

Details and dates: [CHANGELOG.fork.md](CHANGELOG.fork.md).

### 1. Suspend/resume must not leak the previous sentence

Stopping dictation and starting a new utterance often replayed a scrap of
the last sentence (USB capture ring buffer on a Samson Meteor, plus
in-flight `AcceptWaveform` after `SIGCONT`).

- Do **not** flush `FinalResult()` on suspend (that used to type leftover
  words after the message was already sent).
- Bump a `capture_epoch` so a resume cannot emit audio that was read
  before the pause.
- Open a **new** `KaldiRecognizer` on resume.
- Discard ~500 ms of capture preroll (`NERD_DICTATION_PREROLL_SEC`).
- Use `parec --latency-msec=20` instead of `--latency=10` (that was 10
  **bytes**).

### 2. Chromium on Wayland drops spaces

In a normal Chrome tab, progressive emits look like `" erzähle"` (leading
space). Chrome swallows that first key after each virtual-keyboard keymap
upload, so you get `icherzähleeinekleinegeschichte`.

- Keep the separator as a **trailing** space on screen.
- Overlap the last already-typed letter so the space sits *inside* the
  wtype text (`"e über "` not `" über "`).
- `build_wtype_args`: Shift warmup, leading blanks as `-k space`, rest
  after `--`.

Reproduced with eSpeak → virtual Pulse sink (audio leak) and with a
React textarea in a real Chrome tab (spaces).

### 3. wtype robustness on Sway

- Run wtype via `Popen` so suspend can kill an in-flight type.
- Ignore a killed wtype’s non-zero exit during freeze.
- Guard `text_prev` if `SIGUSR1` arrives mid-emit (`in_emit` /
  `abort_assign`).

## What we did *not* put here

- systemd `nerd-dictation.service`, `nerd-dictation-toggle`, Sway
  `Ctrl+Space`, AhaKey LED, OpenCode plugin, Grok `UserPromptSubmit`
  hook — those stay on the machine (see ahakey-x1 docs).
- No vendored VOSK models.

## Upstream PRs

Not dumped as one mega-PR. Candidates worth splitting later:

- capture preroll / epoch on resume
- skip `FinalResult` on suspend
- `parec --latency-msec`
- wtype `--` before text (related: upstream PR #158)

Chrome letter-overlap and `[nd-debug]` lines stay fork-only unless cleaned
up.

## License

Same as upstream: GPL. The original script is
`GPL-2.0-or-later` (SPDX in the file); the GitHub license metadata says
GPL-3.0. We do not relicense.
