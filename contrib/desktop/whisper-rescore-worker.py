#!/usr/bin/env python3
"""Persistent Whisper rescorer for nerd-dictation.

stdin: one WAV path per line
stdout: READY once, then one transcription line per path

Keeps the ggml model loaded so each phrase is only inference, not a reload.
"""

from __future__ import annotations

import logging
import os
import sys
import time
import wave


def wav_duration_sec(path: str) -> float:
    with wave.open(path, "rb") as fh:
        rate = float(fh.getframerate() or 16000)
        return fh.getnframes() / rate


def audio_ctx_for(duration_sec: float) -> int:
    """Map clip length to whisper.cpp encoder frames (50 / s) plus pad.

    Return 0 to keep the model default (1500 / ~30 s). Tight windows are
    fast on short phrases and invent text on longer ones.
    """
    try:
        max_sec = float(os.environ.get("NERD_DICTATION_WHISPER_CTX_MAX_SEC", "4.5"))
    except ValueError:
        max_sec = 4.5
    if duration_sec >= max_sec:
        return 0
    try:
        pad = int(os.environ.get("NERD_DICTATION_WHISPER_CTX_PAD", "32"))
    except ValueError:
        pad = 32
    ctx = int(duration_sec * 50.0 + max(0, pad))
    return max(32, min(1500, ctx))


def want_audio_ctx() -> bool:
    raw = os.environ.get("NERD_DICTATION_WHISPER_AUDIO_CTX", "").strip().lower()
    return raw in ("1", "auto", "on", "yes", "true")


def main() -> int:
    if len(sys.argv) < 2:
        sys.stderr.write("usage: whisper-rescore-worker.py MODEL [THREADS]\n")
        return 2
    model_path = sys.argv[1]
    n_threads = int(sys.argv[2]) if len(sys.argv) > 2 else 4
    lang = os.environ.get("NERD_DICTATION_WHISPER_LANG", "").strip()
    use_ctx = want_audio_ctx()

    logging.getLogger("pywhispercpp").setLevel(logging.ERROR)

    from pywhispercpp.model import Model

    model = Model(
        model_path,
        n_threads=n_threads,
        print_realtime=False,
        print_progress=False,
        redirect_whispercpp_logs_to=os.devnull,
    )
    sys.stdout.write("READY\n")
    sys.stdout.flush()
    for line in sys.stdin:
        path = line.strip()
        if not path:
            continue
        if path == "QUIT":
            break
        text = ""
        dur = 0.0
        ctx = 0
        try:
            kwargs = {
                "suppress_nst": True,
                "no_speech_thold": 0.85,
                "no_context": True,
            }
            if lang and lang not in ("auto", "-"):
                kwargs["language"] = lang
            if use_ctx:
                try:
                    dur = wav_duration_sec(path)
                    ctx = audio_ctx_for(dur)
                    if ctx:
                        kwargs["audio_ctx"] = ctx
                except Exception as ex:
                    sys.stderr.write("whisper-rescore: wav meta %r\n" % (ex,))
            t0 = time.perf_counter()
            try:
                segs = model.transcribe(path, **kwargs)
            except Exception as ex:
                if "audio_ctx" in kwargs:
                    sys.stderr.write("whisper-rescore: audio_ctx failed %r, retry default\n" % (ex,))
                    kwargs.pop("audio_ctx", None)
                    ctx = 0
                    t0 = time.perf_counter()
                    segs = model.transcribe(path, **kwargs)
                else:
                    raise
            dt = time.perf_counter() - t0
            text = " ".join((getattr(s, "text", "") or "").strip() for s in segs)
            text = " ".join(text.split())
            sys.stderr.write(
                "whisper-rescore: %.2fs audio=%.2fs ctx=%d %r\n" % (dt, dur, ctx, text[:80])
            )
        except Exception as ex:
            sys.stderr.write("whisper-rescore: %r\n" % (ex,))
        sys.stdout.write(text.replace("\n", " ") + "\n")
        sys.stdout.flush()
        try:
            os.remove(path)
        except OSError:
            pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
