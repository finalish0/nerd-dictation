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

The script `nerd-dictation` is patched (Wayland/wtype, dual VOSK, Whisper
rescore). Machine-specific glue (systemd user unit, AhaKey toggle,
OpenCode/Grok send-to-suspend, Whisper worker) lives under
`contrib/desktop/` on **`local` only**.

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

### 3. Two recognizers for mixed German/English

`--vosk-en-model-dir` loads a second (usually small English) model on the
same audio. German stays the default; English wins a word only with high
confidence so `commit` is not heard as `komme mit`.

### 4. Whisper as phrase post-correction (not live)

`--whisper-model` starts a persistent Whisper worker. Live typing stays
VOSK (word-for-word). Whisper only rewrites a *finished* phrase, and only
while the next one has not started (`text_prev` empty, same
`capture_epoch`). This is how mixed English in a German session can be
fixed without losing the live visualization.

### 5. wtype robustness on Sway

- Run wtype via `Popen` so suspend can kill an in-flight type.
- Ignore a killed wtype’s non-zero exit during freeze.
- Guard `text_prev` if `SIGUSR1` arrives mid-emit (`in_emit` /
  `abort_assign`).

## Desktop glue (this branch only)

systemd unit, mic toggle, Sway `Ctrl+Space`, OpenCode plugin and Grok
`UserPromptSubmit` freeze live under [`contrib/desktop/`](contrib/desktop/).
They are **not** on `main` and are not meant for an upstream PR. See
[`contrib/desktop/README.md`](contrib/desktop/README.md).

No vendored VOSK models.

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
