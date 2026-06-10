# Google CTF 2018 — Beginners Quest

Write-ups for the Google CTF 2018 *Beginners Quest* challenges collected in this folder.

| Challenge | Category | Flag | Status |
|-----------|----------|------|--------|
| OCR is cool | Crypto / Misc | `CTF{caesarcipherisasubstitutioncipher}` | Solved |
| Foobarnizer 9000 (`fobanizer9000`) | Forensics / Misc | `CTF{ICanReadDis}` | Solved |
| Security through obscurity (`securityObscurity`) | Misc | inside `password.txt` (ZipCrypto-locked) | Structure fully recovered, final password not cracked |

---

## OCR is cool

**Category:** Crypto / Misc
**Files:** `flag.png`, `OCR_is_cool.png`, `image-to-string.py`
**Description:** Recover the flag from the image.

### Write-up

The image `flag.png` contains a string in a slightly rotated font:

```
VMY{vtxltkvbiaxkbltlnulmbmnmbhgvbiaxk}
```

The text is a **ROT (Caesar) cipher**. `VMY` → `CTF` is a shift of **+7**, so the whole
string is decoded by applying ROT+7. The helper [`image-to-string.py`](image-to-string.py)
automates this: it OCRs the image with `pytesseract` and then applies a ROT‑7 substitution
over the alphabet.

The key component is the rotation function:

```python
def rot_encode(n):
    from string import ascii_lowercase as lc, ascii_uppercase as uc
    lookup = str.maketrans(lc + uc, lc[n:] + lc[:n] + uc[n:] + uc[:n])
    return lambda s: s.translate(lookup)

text = pytesseract.image_to_string(Image.open("flag.png"))
print(rot_encode(7)(text))
```

Run it in an isolated environment (no host pollution — `tesseract` installed only inside
the container):

```
docker run --rm -v "$PWD":/work -w /work python:3.11-slim bash -c \
  "apt-get update -qq && apt-get install -y -qq tesseract-ocr && \
   pip install -q pytesseract pillow && python image-to-string.py"
```

OCR misreads a few letters of the rotated font (it returned
`CTF {caeparcipheripapubptitutioncipher}`), but decoding the exact characters read off the
image (`VMY{vtxltkv...}`) with ROT+7 gives the clean message
*"caesar cipher is a substitution cipher"*.

### Flag

```
CTF{caesarcipherisasubstitutioncipher}
```

---

## Foobarnizer 9000

**Category:** Forensics / Misc
**Files:** `fobanizer9000` (a zip), `challenge.pdf`, `foo.ico`
**Description:** Find the credentials in the shipped document.

### Write-up

`fobanizer9000` is a Zip archive (no extension) that simply contains `foo.ico`:

```
unzip fobanizer9000          # -> foo.ico (32x32 MS Windows icon)
```

The real payload is `challenge.pdf` — a fake "IOT Credentials" letter for the *Foobarnizer
9000* product. Extracting the PDF text reveals the password printed directly in the body:

```
docker run --rm -v "$PWD":/work -w /work python:3.11-slim bash -c \
  "pip install -q pypdf && python -c \"import pypdf; \
   print(pypdf.PdfReader('challenge.pdf').pages[0].extract_text())\""
```

```
Thanks for buying ... the Foobarnizer 9000!
Your credentials to the web interface are:
 ● Username: ...........................
 ● Password: CTF{ICanReadDis}
```

The whole point is "I can read this" — the text that looks like an image is selectable PDF
text.

### Flag

```
CTF{ICanReadDis}
```

---

## Other write-ups and resources

- [Google CTF 2018 Beginners Quest](https://capturetheflag.withgoogle.com/)
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract)
- [fcrackzip](https://github.com/hyc/fcrackzip)
- [bkcrack — ZipCrypto known-plaintext attack](https://github.com/kimci86/bkcrack)
