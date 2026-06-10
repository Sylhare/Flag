# NSEC 2018 : captcha

**Category:** Web / Misc (OCR automation)
**Points:**
**Solves:**
**Description:**

A web service at `http://xn--5z8h.ctf:5000/captcha` (the host is the punycode form of an
emoji domain) repeatedly serves a noisy 6-character alphanumeric CAPTCHA image. For each
correctly solved CAPTCHA the server increments a per-session counter; a wrong answer resets
it. The server message states: *"Sucess, you currently have N success. You need 5000 for the
flag"*. The goal is to programmatically solve **5000 CAPTCHAs in a row**, which is only
realistic with an automated OCR pipeline.

## Files

- `captcha.png` — a sample raw CAPTCHA served by the challenge (90x46, e.g. `xt3v3c`).
- `img.png` — the same kind of CAPTCHA after the cleaning/threshold pipeline (1-bit, upscaled).
- `captcha.py` — a clean, self-contained template-matching OCR (no Tesseract).
- `solve-auto.py` — the fully automated loop: fetch -> clean -> OCR (Tesseract) -> submit.
- `solve-manual-backup.py` — same loop, but falls back to manual input when OCR fails.
- `captcha.ipynb` — the working notebook used during the event (contains run outputs).
- `TWSE Captcha OCR Challenge.ipynb` — the reference OCR project the approach is based on.
- `requirements.txt` — Python deps (`opencv-python`, `pytesseract`, `pillow`, `scipy`, ...).
- `test_captcha.py` (in `../crypto/RC8_crypto/`) — the nose test harness for `captcha.solve`.

## Write-up

### The challenge loop

The CAPTCHA is stateful and cookie-bound. You GET an image, OCR it, then POST the answer
with the same session cookie; the response cookie carries the next round's state. From
`solve-auto.py`:

```python
def request_captcha(cookie):
    img = requests.get('http://xn--5z8h.ctf:5000/captcha', cookies=cookie,
                       headers={'Content-type': 'image/png'})
    return img.content

def send_captcha(cookie, captcha):
    r = requests.post('http://xn--5z8h.ctf:5000/captcha', cookies=cookie,
                      data={'captcha': captcha})
    print(re.search('<li>(.*?)</li>', r.text).group(1))   # "...you currently have N success..."
    return requests.utils.dict_from_cookiejar(r.cookies)

def solve():
    next_cookie = send_captcha(first_cookie, '977rll')     # seed cookie from the browser
    for i in range(5000):
        next_cookie = send_captcha(next_cookie, new_captcha(next_cookie))
```

### Image cleaning (the hard part)

The raw image has a stray line and dot noise, so it's thresholded, eroded, denoised and
upscaled before OCR. From `solve-auto.py:clean_captcha`:

```python
captcha = cv2.imdecode(np.asarray(bytearray(captcha), 'uint8'), cv2.IMREAD_GRAYSCALE)
(_, captcha) = cv2.threshold(captcha, 210, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
captcha = cv2.erode(captcha, np.ones((3, 3), np.uint8))        # kill the line + dot noise
(_, captcha) = cv2.threshold(captcha, 210, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
captcha = cv2.fastNlMeansDenoising(captcha, h=30)
captcha = toimage(captcha).resize([w*10, h*10])               # upscale helps Tesseract
```

Then Tesseract is constrained to the CAPTCHA alphabet and its output is patched for common
confusions:

```python
text = image_to_string(captcha, config="-c tessedit_char_whitelist=0123456789abcdefghijklmnopqrstuvwxyz -psm 6")
text = re.sub(r'\|', 'l', text).replace("'", "i").replace("]", "j").replace("><", "x")
```

`solve-manual-backup.py` runs several variants (ImageMagick `convert` with `-lat`,
`textcleaner`, plus both `gocr` and Tesseract) and tries each candidate; if all of them are
rejected by the server it `Image.open('img.png').show()`s the cleaned image and asks the
operator to type the answer:

```python
for i in img_text:                       # try every OCR candidate
    response_cookie = send_captcha(request_cookie, i)
    if response_cookie != request_cookie:   # cookie changed => accepted
        break
if response_cookie == request_cookie:    # every candidate rejected -> human fallback
    captcha_manual = input("What is the captcha?")
```

### A Tesseract-free alternative: `captcha.py`

`captcha.py` is a cleaner pure-PIL solver that avoids OCR entirely. It thresholds the image
to 1-bit, splits it into individual glyphs at whitespace columns (`split_by_whitespace`), and
classifies each glyph by **pixel-wise similarity against a template image** containing every
known character:

```python
def solve(captcha_image, params):
    template_image = PIL.Image.open(params['template'])
    captcha_chars, template_chars = map(split_by_whitespace, (captcha_image, template_image))
    for captcha_index in range(len(captcha_chars)):
        # pick the template glyph with the most matching pixels
        ...
        result.append(recognized_char if recognized_char >= 0 else None)
```

This is the approach exercised by `test_captcha.py` (JSON-configured fixtures specifying
`template`, crop box, `threshold`, and the `samples` directory whose filenames are the
ground-truth answers).

## Other write-ups and resources

- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) / [pytesseract](https://github.com/madmaze/pytesseract)
- [OpenCV thresholding & morphology](https://docs.opencv.org/)
- [TWSE Captcha OCR Challenge](https://github.com/) — the reference project this build was based on (see `TWSE Captcha OCR Challenge.ipynb`)
- [Flask session cookie / itsdangerous](https://flask.palletsprojects.com/en/latest/quickstart/#sessions)
