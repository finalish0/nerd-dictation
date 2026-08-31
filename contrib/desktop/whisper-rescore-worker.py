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


def main() -> int:
    if len(sys.argv) < 2:
        sys.stderr.write("usage: whisper-rescore-worker.py MODEL [THREADS]\n")
        return 2
    model_path = sys.argv[1]
    n_threads = int(sys.argv[2]) if len(sys.argv) > 2 else 4
    lang = os.environ.get("NERD_DICTATION_WHISPER_LANG", "").strip()

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
        try:
            kwargs = {
                "suppress_nst": True,
                "no_speech_thold": 0.85,
                "no_context": True,
            }
            if lang and lang not in ("auto", "-"):
                kwargs["language"] = lang
            segs = model.transcribe(path, **kwargs)
            text = " ".join((getattr(s, "text", "") or "").strip() for s in segs)
            text = " ".join(text.split())
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
