# Nerd Dictation (fork)

Offline dictation for Linux that **types while you talk**, then quietly
fixes the sentence.

This is a fork of [ideasman42/nerd-dictation](https://github.com/ideasman42/nerd-dictation)
on branch **`local`**. Upstream stays on `main`. Engineering notes:
[FORK.md](FORK.md). Upstream options: [readme.rst](readme.rst).

## Why this fork

Upstream nerd-dictation is a begin/end script: hold a key, talk, release,
wait for VOSK, dump the whole phrase. Fine, but it feels like a dictation
box.

Here the mic is a **warm daemon**. Press once (default `Ctrl+Space`):

1. **VOSK types live**, word by word, into whatever is focused — Crush, a
   terminal, a browser, a chat composer.
2. After a short pause, **Whisper re-reads that fragment** and replaces it
   in place (punctuation, capitals, `commit` instead of `komme mit`).
3. Press the mic again (or the pad checkmark) to freeze. The process stays
   in RAM; the next press is instant. No model reload.

German is the live model; a second small English VOSK can steal
high-confidence words so code tokens survive. Whisper runs as a
persistent worker (`pywhispercpp`), not a fresh process per phrase.

A master switch (`Super+n` on Sway) turns the whole thing **off**. Then
`Ctrl+Space` is just `Ctrl+Space` again — Grok Voice / Croc Dictator / the
app. Dictation does not steal keys while it is off.

## Install (Sway / Wayland)

Needs: `python3`, `parec` (PipeWire/Pulse), `wtype`, `curl`, `unzip`, a
user systemd session.

```sh
git clone -b local https://github.com/finalish0/nerd-dictation.git
cd nerd-dictation
./contrib/desktop/install.sh
```

That creates a venv, installs `vosk` + `pywhispercpp`, fetches the small
German + English VOSK models and Whisper `ggml-small`, writes a **user**
systemd unit, and puts `nerd-dictation-toggle` on your `PATH`.

Once, in `~/.config/sway/config`:

```
include ~/.config/sway/nerd-dictation.conf
bindsym $mod+n exec --no-startup-id ~/.local/bin/nerd-dictation-toggle master
```

Then `swaymsg reload`. First mic press: wait until
`nerd-dictation-toggle status` shows `T`/`Ts` (model loaded, sleeping).

```sh
nerd-dictation-toggle on      # daemon + Ctrl+Space is the mic
nerd-dictation-toggle off     # keys go back to the app
nerd-dictation-toggle master  # Super+n
nerd-dictation-toggle status
```

Optional: `--no-models` if the models are already on disk,
`--no-en` to skip the English VOSK, `--whisper-lang de` (default).

## Optional: AhaKey pad

If [ahakey-x1](https://github.com/finalish0/ahakey-x1) is installed, the
toggle pulses the LED (breathing = recording) and, **only while dictation
is on**, the pad checkmark means “freeze mic, then Enter” in the focused
window. While dictation is off, the checkmark is plain Enter. Laptop Enter
is never stolen. No pad? Ignore this; the keyboard bindings are enough.

## What it is not

- Not a cloud STT API. Audio stays on the machine.
- Not a drop-in for macOS/Windows.
- Not the upstream CLI workflow (`begin` / `end` still work; the desktop
  path is the warm daemon).
- Desktop glue lives in `contrib/desktop/` on `local` only — not an
  upstream PR.

## Models

| Piece | Default | Role |
|---|---|---|
| VOSK `small-de-0.15` | live typing | fast, messy |
| VOSK `small-en-us-0.15` | mixed DE/EN | `commit` vs `komme mit` |
| Whisper `ggml-small` | phrase rescore | punctuation, cleanup |

Whisper is post-correction, not the live engine. Empty / `[Pause]` /
“thanks for watching” output is dropped. Long takes size the encoder
window to the clip so the same sentence is not typed twice.

## License

Same as upstream: GPL (`GPL-2.0-or-later` on the script).
