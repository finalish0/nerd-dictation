#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later

"""Tests for Whisper post-correction helpers (no ggml load)."""

import os
import sys
import tempfile
import unittest
import wave
from types import ModuleType


def execfile_as_module(mod_name: str, filepath: str) -> ModuleType:
    import importlib.machinery

    loader = importlib.machinery.SourceFileLoader(mod_name, filepath)
    return loader.load_module()


HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(os.path.dirname(HERE), "nerd-dictation")
nd = execfile_as_module("nerd_dictation_whisper_test", SCRIPT)


class TestWhisperJunk(unittest.TestCase):
    def test_empty(self) -> None:
        self.assertTrue(nd.whisper_text_is_junk(""))
        self.assertTrue(nd.whisper_text_is_junk("   "))
        self.assertTrue(nd.whisper_text_is_junk("..."))

    def test_hallucinations(self) -> None:
        self.assertTrue(nd.whisper_text_is_junk("Thanks for watching."))
        self.assertTrue(nd.whisper_text_is_junk("Untertitel der Amara.org-Community"))
        self.assertTrue(nd.whisper_text_is_junk("[music]"))

    def test_real_phrases_are_kept(self) -> None:
        self.assertFalse(nd.whisper_text_is_junk("ich commit das"))
        self.assertFalse(nd.whisper_text_is_junk("thank you"))
        self.assertFalse(nd.whisper_text_is_junk("ich erzähle eine kleine geschichte"))


class TestWhisperShouldApply(unittest.TestCase):
    def test_identical_skipped(self) -> None:
        self.assertFalse(nd.whisper_should_apply("ich commit das", "ich commit das"))
        self.assertFalse(nd.whisper_should_apply("Ich Commit Das", "ich commit das"))

    def test_english_fix_applied(self) -> None:
        self.assertTrue(nd.whisper_should_apply("ich komme mit das", "ich commit das"))

    def test_junk_skipped(self) -> None:
        self.assertFalse(
            nd.whisper_should_apply("ich erzähle eine geschichte", "Thanks for watching.")
        )

    def test_length_mismatch_skipped(self) -> None:
        self.assertFalse(nd.whisper_should_apply("ich erzähle eine kleine geschichte über eine ente", "Hi"))


class TestWriteWav(unittest.TestCase):
    def test_header(self) -> None:
        pcm = b"\x00\x00" * 160
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as fh:
            path = fh.name
        try:
            nd.write_s16le_wav(path, pcm, 16000)
            with wave.open(path, "rb") as wav:
                self.assertEqual(wav.getnchannels(), 1)
                self.assertEqual(wav.getsampwidth(), 2)
                self.assertEqual(wav.getframerate(), 16000)
                self.assertEqual(wav.getnframes(), 160)
        finally:
            os.remove(path)


if __name__ == "__main__":
    unittest.main()
