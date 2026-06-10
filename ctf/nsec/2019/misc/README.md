# NSEC 2019 : misc

**Category:** Misc / Reverse Engineering
**Points:**
**Solves:**
**Description:** A grab-bag of small "misc" artifacts. This directory holds four
independent items:

- `re_challenge1.exe` / `re_challenge2.exe` — two NSIS-installer reverse-engineering puzzles.
- `pitman_shothand.png` — a line of Pitman shorthand to transcribe.
- `primitive_beat-140BPM-space.mp3` — an audio file (likely a steganography / signal puzzle).

## Write-up

### re_challenge1.exe and re_challenge2.exe (SOLVED)

Both files are **Nullsoft Install System (NSIS) v3.03** self-extracting installers:

```
$ file re_challenge1.exe re_challenge2.exe
re_challenge1.exe: PE32 executable (GUI) Intel 80386, ... Nullsoft Installer self-extracting archive
re_challenge2.exe: PE32 executable (GUI) Intel 80386, ... Nullsoft Installer self-extracting archive
```

NSIS stores its install script as a **deflate-compressed header** that begins right
after the firstheader (offset `0x8E40` = 36384 in these files). Inflating it
(`zlib.decompressobj(-15)`) exposes the script's strings table and bytecode
(`ENTRIES`/`STRINGS`/`SECTIONS` blocks). The full recovery script is `solve_nsis.py`:

```
$ python3 solve_nsis.py
re_challenge1.exe: FLAG-437699f45dc2b3d2370b9889f814fdd9f9e9e4e4
re_challenge2.exe: FLAG-ab1c1972c41c31b1bd7bda35d85eee39694c9d97
```

#### Challenge 1 — flag is a plain string

The script downloads the EICAR antivirus test file
(`http://2016.eicar.org/download/eicar.com`) and, on success, prints `Good boy!`.
The flag is sitting **in plaintext** in the strings block, so inflating the header
and grepping is enough:

```python
out = zlib.decompressobj(-15).decompress(open(path,'rb').read()[36384:])
re.search(rb"FLAG-[0-9a-fA-F]{40}", out)   # -> FLAG-437699f45dc2b3d2370b9889f814fdd9f9e9e4e4
```

#### Challenge 2 — flag assembled at install time

The author hid the flag from naive `strings`: the strings table only contains
`Good boy!` plus dozens of single-character fragments like `b{VAR}`, `7{VAR}`,
`{VAR}d`, ... Those are operands of `EW_ASSIGNVAR` (StrCpy, opcode `25`) entries
that build the flag one character at a time into a variable: `X{VAR}` prepends `X`,
`{VAR}X` appends `X`. Replaying the entries in order reconstructs it:

```python
for cmd, *p in entries:
    if cmd != 25:                       # EW_ASSIGNVAR / StrCpy
        continue
    s = getstr(p[1])                    # one literal char + one {VAR} reference
    lit = ''.join(c for c in s if c != ('VAR',))
    if [j for j,c in enumerate(s) if c==('VAR',)][0] == 0:
        flag += lit                     # "{VAR}X" -> append
    else:
        flag = lit + flag               # "X{VAR}" -> prepend
# -> FLAG-ab1c1972c41c31b1bd7bda35d85eee39694c9d97
```

Both flags are 40-hex-char NSEC-style flags and are reproduced by `solve_nsis.py`.

#### Commands used (extraction was done in an isolated Docker container)

```
docker run --rm -v "$PWD":/work -w /work ubuntu:22.04 bash -c \
  'apt-get update && apt-get install -y p7zip-full python3 && python3 solve_nsis.py'
# 7z confirmed the type:  Type = Nsis, SubType = NSIS-3, Method = Deflate
```

### pitman_shothand.png (UNSOLVED — manual transcription)

A 346x139 image of a single line of [Pitman shorthand](https://en.wikipedia.org/wiki/Pitman_shorthand)
(stenography). Solving it requires transcribing the strokes/positions into letters
by hand using Pitman rules; it cannot be brute-forced or OCR'd reliably. Documented
here as the intended approach; the decoded phrase is not recovered in this write-up.

### primitive_beat-140BPM-space.mp3 (UNSOLVED — audio/signal puzzle)

```
$ file primitive_beat-140BPM-space.mp3
MPEG ADTS, layer III, v1, 128 kbps, 44.1 kHz, JntStereo
```

A valid 685 KB MP3 (the trailing `0x55` run is ordinary frame padding; there is no
appended ZIP/PNG/RAR — checked). The name ("140 BPM", "space") plus the misc/audio
category strongly suggests a **signal-in-audio** puzzle (SSTV image, DTMF, or Morse
on a rhythmic carrier). Decoding needs an SSTV/Morse decoder and a spectrogram view;
it was not decoded in this headless environment. Approach: open in Audacity/`sox` and
inspect the spectrogram, then run an SSTV decoder if an image is present.

## Other write-ups and resources

- [NSIS (Nullsoft Scriptable Install System)](https://nsis.sourceforge.io/Main_Page)
- [NSIS file format / header layout](https://nsis.sourceforge.io/Docs/AppendixB.html)
- [7-Zip NSIS handler](https://www.7-zip.org/)
- [Pitman shorthand](https://en.wikipedia.org/wiki/Pitman_shorthand)
- [SSTV (slow-scan television)](https://en.wikipedia.org/wiki/Slow-scan_television)
