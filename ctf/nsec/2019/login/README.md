# NSEC 2019 : login (Neurosoft)

**Category:** Misc / Crypto (symbol-substitution cipher)
**Points:**
**Solves:**
**Description:**

A photo of a *Neurosoft* login form (the same NeuroPass / Neurosoft track as
[`../neuropass`](../neuropass/README.md)). The form is filled in:

- **Username:** `justin`
- **Password:** a sequence of ~8 hand-drawn **glyphs** in an unknown symbol script.

The task is to read the password back out of the glyph script (then, in the broader track,
log in as `justin`).

## Files

- `login.jpg` — the original photo: the page header reads "Neuro…", `username: justin`,
  `password:` followed by the glyph string.
- `login.png` — a tightly cropped, higher-contrast image of just the password glyphs.
- `ocr.py` — the author's attempt: Tesseract OCR plus ROT/Caesar helper functions.

## Write-up

### What the picture shows

After cropping/upscaling `login.png`, the password is a row of distinct symbols (an
`F`-like stroke, an hourglass/figure-eight, a dashed cross with dots, a cursive loop, a black
chess-knight silhouette, an `X`, a left-pointing triangle with a dot, and a spiral/`@`-like
glyph). This is a **constructed symbol alphabet** (a substitution cipher where each glyph maps
to one character), not normal text — exactly the kind of thing standard OCR cannot read.

### The author's approach (`ocr.py`)

`ocr.py` tries to (a) OCR the image and (b) undo a Caesar/ROT shift on the result:

```python
import pytesseract
from PIL import Image

img  = Image.open("login.png")
text = pytesseract.image_to_string(img)                 # plain OCR

def image_ocr(image_path, output_txt_file_name):
    image_text = pytesseract.image_to_string(image_path, lang='eng+ces', config='--psm 1')
    open(output_txt_file_name, 'w+', encoding='utf-8').write(image_text)
```

and a generic ROT helper used to test letter-shift hypotheses on the OCR output:

```python
def rot_encode(n):
    from string import ascii_lowercase as lc, ascii_uppercase as uc
    lookup = str.maketrans(lc + uc, lc[n:] + lc[:n] + uc[n:] + uc[:n])
    return lambda s: s.translate(lookup)

# print(rot_encode(7)(text))
# print(7, rot_encode(7)('vtxlt'))
```

Tesseract on a symbol font produces garbage (confirmed by running it in an isolated venv),
so the ROT step never had a clean input to work on. The intended solution is **manual**:
identify the symbol alphabet (these glyph sets are usually a themed/known font — e.g. a
sci-fi or game script tied to the "Neurosoft" theme) and substitute glyph-by-glyph, then
optionally apply the ROT the author was probing for.

### Connection to the broader track

The username `justin` and the "Neuro…" header tie this directly to the
[`neuropass`](../neuropass/README.md) NeuroPass challenge: the glyph password is the
credential NeuroPass would store/auto-fill for `justin`. Decoding the glyphs yields the
password that, fed through NeuroPass's `protect()` cipher / stored in its SQLite DB, gates the
target account.

### Commands used

```
# isolated venv to test the author's OCR (confirms Tesseract can't read the glyph font)
uv venv /tmp/login-venv && uv pip install --python /tmp/login-venv/bin/python pillow
# upscaled login.png 3x for manual glyph reading
```

## Other write-ups and resources

- [Substitution cipher](https://en.wikipedia.org/wiki/Substitution_cipher)
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) (used unsuccessfully on the glyph font)
- Companion challenge: [`../neuropass`](../neuropass/README.md)
