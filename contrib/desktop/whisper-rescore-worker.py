#!/usr/bin/env python3
"""Persistent Whisper rescorer for nerd-dictation.

stdin: one WAV path per line
stdout: READY once, then one transcription line per path

Keeps the ggml model loaded so each phrase is only inference, not a reload.
"""

from __future__ import annotations

import logging
import os
import re
import sys
import time
import wave


def wav_duration_sec(path: str) -> float:
    with wave.open(path, "rb") as fh:
        rate = float(fh.getframerate() or 16000)
        return fh.getnframes() / rate


def audio_ctx_for(duration_sec: float) -> int:
    """Map clip length to whisper.cpp encoder frames (50 / s) plus pad.

    Always size the window to the clip. The old path returned 0 (model
    default ~30 s) once duration hit NERD_DICTATION_WHISPER_CTX_MAX_SEC;
    that padded ~7 s phrases with silence and Whisper echoed the sentence.
    """
    try:
        pad = int(os.environ.get("NERD_DICTATION_WHISPER_CTX_PAD", "32"))
    except ValueError:
        pad = 32
    ctx = int(max(0.0, duration_sec) * 50.0 + max(0, pad))
    return max(32, min(1500, ctx))


def _norm_seg(text: str) -> str:
    return " ".join((text or "").casefold().strip(" .!?,;:").split())


def collapse_repeated_segments(texts: list[str]) -> str:
    """Join segments, dropping a trailing echo of the same sentence."""
    parts = [" ".join((t or "").split()).strip() for t in texts]
    parts = [p for p in parts if p]
    if not parts:
        return ""
    out: list[str] = []
    for p in parts:
        if out:
            a, b = _norm_seg(out[-1]), _norm_seg(p)
            if a and b and (a == b or (len(b) >= 24 and (b in a or a in b))):
                if len(b) > len(a):
                    out[-1] = p
                continue
        out.append(p)
    text = " ".join(out)
    sents = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
    if len(sents) >= 2 and len(sents) % 2 == 0:
        mid = len(sents) // 2
        left, right = " ".join(sents[:mid]), " ".join(sents[mid:])
        a, b = _norm_seg(left), _norm_seg(right)
        if a and b and (a == b or (len(a) >= 24 and len(b) >= 24 and (a in b or b in a))):
            return left if len(a) >= len(b) else right
    return text


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
            segs_text = [(getattr(s, "text", "") or "").strip() for s in segs]
            text = collapse_repeated_segments(segs_text)
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
