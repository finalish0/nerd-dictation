#!/usr/bin/env bash
# Install this fork’s warm daemon (venv, models, user systemd, toggle).
# Safe to re-run. Does not edit Sway config.
set -euo pipefail

DESKTOP=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
ROOT=$(CDPATH= cd -- "$DESKTOP/../.." && pwd)
CONF="${XDG_CONFIG_HOME:-$HOME/.config}/nerd-dictation"
DATA="${XDG_DATA_HOME:-$HOME/.local/share}/nerd-dictation"
VOSK_ROOT="${XDG_DATA_HOME:-$HOME/.local/share}/vosk-models"
BIN="${NERD_DICTATION_BIN:-$HOME/.local/bin}"
WHISPER_LANG=de
WITH_EN=1
WITH_MODELS=1

usage() {
  cat <<EOF
Usage: $0 [options]

  --no-models     skip VOSK/Whisper downloads (paths must already exist)
  --no-en         do not wire the small English VOSK model
  --whisper-lang CODE   default: de
  --help
EOF
}

while [ $# -gt 0 ]; do
  case "$1" in
    --no-models) WITH_MODELS=0 ;;
    --no-en) WITH_EN=0 ;;
    --whisper-lang)
      shift
      WHISPER_LANG="${1:-de}"
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
  shift
done

need() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "missing command: $1" >&2
    exit 1
  }
}

need python3
need curl
need unzip
need install

if ! command -v parec >/dev/null 2>&1; then
  echo "warning: parec not on PATH (PipeWire/Pulse). Dictation will not record." >&2
fi
if ! command -v wtype >/dev/null 2>&1; then
  echo "warning: wtype not on PATH. Wayland typing will not work." >&2
fi

mkdir -p "$CONF" "$DATA/models" "$VOSK_ROOT" "$BIN" "$HOME/.config/systemd/user"

VENV="$ROOT/.venv"
if [ ! -x "$VENV/bin/python" ]; then
  python3 -m venv "$VENV"
fi
"$VENV/bin/pip" install -q --upgrade pip
"$VENV/bin/pip" install -q -r "$DESKTOP/requirements.txt"

fetch_zip() {
  local url=$1 dest=$2
  if [ -d "$dest" ]; then
    return 0
  fi
  local tmp
  tmp=$(mktemp -d)
  echo "downloading $(basename "$dest") …"
  curl -fL --progress-bar "$url" -o "$tmp/model.zip"
  unzip -q "$tmp/model.zip" -d "$VOSK_ROOT"
  rm -rf "$tmp"
}

fetch_file() {
  local url=$1 dest=$2
  if [ -e "$dest" ]; then
    return 0
  fi
  echo "downloading $(basename "$dest") …"
  mkdir -p "$(dirname "$dest")"
  curl -fL --progress-bar "$url" -o "$dest.partial"
  mv "$dest.partial" "$dest"
}

VOSK_DE="$VOSK_ROOT/vosk-model-small-de-0.15"
VOSK_EN="$VOSK_ROOT/vosk-model-small-en-us-0.15"
WHISPER="$DATA/models/ggml-small.bin"
OPENCODE_WHISPER="$HOME/.cache/opencode-voice/models/ggml-small.bin"

if [ ! -e "$WHISPER" ] && [ -f "$OPENCODE_WHISPER" ]; then
  mkdir -p "$(dirname "$WHISPER")"
  ln -s "$OPENCODE_WHISPER" "$WHISPER"
  echo "whisper model: symlink to existing $OPENCODE_WHISPER"
fi

if [ "$WITH_MODELS" = 1 ]; then
  fetch_zip "https://alphacephei.com/vosk/models/vosk-model-small-de-0.15.zip" "$VOSK_DE"
  if [ "$WITH_EN" = 1 ]; then
    fetch_zip "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip" "$VOSK_EN"
  fi
  fetch_file "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-small.bin" "$WHISPER"
fi

for p in "$VOSK_DE" "$WHISPER"; do
  if [ ! -e "$p" ]; then
    echo "missing $p (run without --no-models, or place the file)" >&2
    exit 1
  fi
done
if [ "$WITH_EN" = 1 ] && [ ! -d "$VOSK_EN" ]; then
  echo "missing $VOSK_EN (omit --no-en, or run without --no-models)" >&2
  exit 1
fi

ND="$ROOT/nerd-dictation"
PYTHON="$VENV/bin/python"
VOSK_ARGS="--vosk-model-dir=$VOSK_DE"
if [ "$WITH_EN" = 1 ]; then
  VOSK_ARGS="$VOSK_ARGS --vosk-en-model-dir=$VOSK_EN"
fi

umask 077
{
  echo "# Written by contrib/desktop/install.sh — sourced by nerd-dictation-toggle."
  printf 'ND=%q\n' "$ND"
  printf 'PYTHON=%q\n' "$PYTHON"
  if [ -x "$HOME/git/ahakey-x1/ahakey.sh" ]; then
    printf 'AHAKEY=%q\n' "$HOME/git/ahakey-x1/ahakey.sh"
  fi
  if [ -x "$HOME/git/ahakey-x1/contrib/pad-enter.sh" ]; then
    printf 'PAD_ENTER=%q\n' "$HOME/git/ahakey-x1/contrib/pad-enter.sh"
    printf 'AHAKEY_ENV=%q\n' "$HOME/git/ahakey-x1/.env"
  fi
} > "$CONF/env"

sed \
  -e "s|@PYTHON@|$PYTHON|g" \
  -e "s|@ND@|$ND|g" \
  -e "s|@VOSK_ARGS@|$VOSK_ARGS|g" \
  -e "s|@WHISPER@|$WHISPER|g" \
  -e "s|@WHISPER_LANG@|$WHISPER_LANG|g" \
  "$DESKTOP/nerd-dictation.service.in" \
  > "$HOME/.config/systemd/user/nerd-dictation.service"

install -Dm755 "$DESKTOP/nerd-dictation-toggle" "$BIN/nerd-dictation-toggle"
SWAY_INC="${XDG_CONFIG_HOME:-$HOME/.config}/sway/nerd-dictation.conf"
if [ ! -f "$SWAY_INC" ]; then
  install -Dm644 "$DESKTOP/sway-nerd-dictation.conf" "$SWAY_INC"
fi

systemctl --user daemon-reload
if systemctl --user --quiet is-enabled nerd-dictation.service 2>/dev/null; then
  echo "unit already enabled. Restart when idle:  systemctl --user restart nerd-dictation"
else
  systemctl --user enable nerd-dictation.service
  echo "enabled nerd-dictation.service (not started). Super+n / toggle on will start it."
fi

cat <<EOF

Installed.

Add once to ~/.config/sway/config, then: swaymsg reload

  include ~/.config/sway/nerd-dictation.conf
  bindsym \$mod+n exec --no-startup-id $BIN/nerd-dictation-toggle master

Then:

  nerd-dictation-toggle on
  nerd-dictation-toggle status   # wait for state T/Ts before the first mic press

EOF
