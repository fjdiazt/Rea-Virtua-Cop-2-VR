"""Extract audio from a single-BIN, 2352-byte/sector Virtua Cop 2 CUE image."""

import argparse
import re
import wave
from pathlib import Path


def extract(cue: Path, output: Path) -> None:
    text = cue.read_text(encoding="utf-8-sig")
    files = re.findall(r'^FILE\s+"([^"]+)"\s+BINARY\s*$', text, re.M | re.I)
    if len(files) != 1 or len(re.findall(r"^FILE\s+", text, re.M | re.I)) != 1:
        raise ValueError("CUE must name one quoted BINARY file")
    bin_path = cue.parent / files[0]
    tracks = []
    for line in text.splitlines():
        track = re.fullmatch(r"\s*TRACK\s+(\d+)\s+(\S+)\s*", line, re.I)
        index = re.fullmatch(r"\s*INDEX\s+01\s+(\d+):(\d+):(\d+)\s*", line, re.I)
        if track:
            tracks.append([int(track[1]), track[2].upper(), None])
        elif index:
            minute, second, frame = map(int, index.groups())
            if not tracks or tracks[-1][2] is not None or second >= 60 or frame >= 75:
                raise ValueError("Invalid INDEX 01")
            tracks[-1][2] = (minute * 60 + second) * 75 + frame
    size = bin_path.stat().st_size
    if size % 2352 or size == 0:
        raise ValueError("BIN size must be a nonzero multiple of 2352 bytes")
    sectors = size // 2352
    if (len(tracks) < 2 or tracks[0] != [1, "MODE1/2352", 0] or
            any(track[0] != number or track[1] != "AUDIO" or track[2] is None
                for number, track in enumerate(tracks[1:], 2)) or
            any(a[2] >= b[2] for a, b in zip(tracks, tracks[1:])) or
            tracks[-1][2] >= sectors or tracks[-1][0] > 99):
        raise ValueError("Expected data track 01 followed by numbered audio tracks")
    if output.exists():
        raise FileExistsError(output)
    output.mkdir(parents=True)
    with bin_path.open("rb") as source:
        for i, (number, _, start) in enumerate(tracks[1:], 1):
            end = tracks[i + 1][2] if i + 1 < len(tracks) else sectors
            remaining = (end - start) * 2352
            source.seek(start * 2352)
            path = output / f"Track{number:02d}.wav"
            with wave.open(str(path), "wb") as audio:
                audio.setnchannels(2)
                audio.setsampwidth(2)
                audio.setframerate(44100)
                while remaining:
                    block = source.read(min(remaining, 2352 * 300))
                    if not block:
                        raise EOFError(bin_path)
                    audio.writeframesraw(block)
                    remaining -= len(block)
            print(path.name)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("cue", type=Path)
    parser.add_argument("output", type=Path, help="new MUSIC directory beside PROJECT")
    args = parser.parse_args()
    extract(args.cue, args.output)
