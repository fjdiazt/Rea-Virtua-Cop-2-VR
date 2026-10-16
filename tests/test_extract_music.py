import tempfile
import unittest
import wave
from pathlib import Path

from audio.extract_music import extract


class ExtractMusicTest(unittest.TestCase):
    def test_single_bin_mixed_mode(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "disc.bin").write_bytes(b"D" * 2352 + b"A" * 2352 + b"B" * 2352)
            cue = root / "disc.cue"
            cue.write_text('FILE "disc.bin" BINARY\n'
                           'TRACK 01 MODE1/2352\nINDEX 01 00:00:00\n'
                           'TRACK 02 AUDIO\nINDEX 01 00:00:01\n'
                           'TRACK 03 AUDIO\nINDEX 01 00:00:02\n')
            output = root / "MUSIC"
            extract(cue, output)
            self.assertEqual([p.name for p in sorted(output.iterdir())],
                             ["Track02.wav", "Track03.wav"])
            with wave.open(str(output / "Track03.wav"), "rb") as audio:
                self.assertEqual((audio.getnchannels(), audio.getframerate(),
                                  audio.getsampwidth(), audio.readframes(1)),
                                 (2, 44100, 2, b"BBBB"))

    def test_rejects_multiple_files_before_writing(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            cue = root / "disc.cue"
            cue.write_text('FILE "a.bin" BINARY\nFILE "b.bin" BINARY\n')
            with self.assertRaises(ValueError):
                extract(cue, root / "MUSIC")
            self.assertFalse((root / "MUSIC").exists())


if __name__ == "__main__":
    unittest.main()
