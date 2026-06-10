# NSEC 2019 : catchat (vision.ctf)

**Category:** Misc / Web (image classification automation)
**Points:**
**Solves:**
**Description:**

A web service at `http://vision.ctf/catchat.php` serves an image each request and asks
you to classify it as either an **animal** or a **thing** by POSTing `result=animal` or
`result=thing` to `http://vision.ctf/index.php`. The server keeps a per-session
(`PHPSESSID`) success counter; the server text shows progress toward **15 000** correct
classifications, after which the flag is awarded. The goal is to automate the
classification well enough to reach 15 000.

## Files

- `catchat.py` — the automation loop: fetch image -> classify -> POST -> save misses.
- `ImageCompare.py` — a small library of image-difference metrics (histogram, pixel, XOR).
- `test.py` — a tiny sanity check of the pixel-difference metric on two `dog6` samples.
- `sample.png` — scratch file the loop writes each fetched image to.
- `samples/animals/` (dog*.png) and `samples/things/` (donut*/muffin*/serp*.png) — the
  reference image library used to classify by nearest-match.
- `__init__.py` — one line; only references the author's local path.

## Write-up

### The loop

`catchat.py` fetches an image, decides animal-vs-thing by comparing it against the local
reference library, posts the answer, and parses the server response for the
"Congrats ... 15 000" success regex. On a wrong guess it **saves the image into the
opposite class folder** so the reference library improves over time:

```python
while True:
    response = requests.get('http://vision.ctf/catchat.php', headers=headers, cookies=cookies)
    open(sample_png, 'wb').write(response.content)

    if not in_things():                                  # looks more like an animal
        post = requests.post('http://vision.ctf/index.php', data={'result':'animal'}, ...)
        if_wrong_save_image(re.search("(C.* 15 000<)+", str(post.content)))
    else:                                                # looks more like a thing
        post = requests.post('http://vision.ctf/index.php', data={'result':'thing'}, ...)
        if_wrong_save_image(re.search("(C.* 15 000<)+", str(post.content)), image_type="animals")
```

### The classifier

Classification is **nearest-reference by mean per-channel pixel difference** (no ML). The
fetched image is compared against every reference in `samples/things/`; if any is closer
than a 10% threshold, it is called a "thing", otherwise an "animal":

```python
def image_compare(i1, i2):
    pairs = zip(i1.getdata(), i2.getdata())
    dif = sum(abs(c1 - c2) for p1, p2 in pairs for c1, c2 in zip(p1, p2))   # RGB
    ncomponents = i1.size[0] * i1.size[1] * 3
    return (dif / 255.0 * 100) / ncomponents          # mean % difference

def in_things():
    for filename in os.listdir(things_path):
        if image_compare(Image.open(sample_png), Image.open(things_path+filename)) < 10:
            return True            # close enough to a known "thing"
    return False
```

`ImageCompare.py` provides richer metrics (`HistoCompare`, `PixelCompare`, `XORCompare`)
and was the author's experiment toward a better discriminator; `catchat.py` ultimately
used the simple mean-difference above.

### Note on the "FLAG-" in the path

The hard-coded path in `catchat.py` / `test.py` /`__init__.py` is:

```python
catchat = os.path.join(os.getcwd(), "/FLAG-bXlyZXBvc2l0b3J5dG9maW5kZmxhZ3M/NSEC2019/catchat")
```

This is **not** the challenge flag. It is just the author's local repository directory
name; the base64 segment decodes to ordinary text:

```
$ python3 -c "import base64; print(base64.b64decode('bXlyZXBvc2l0b3J5dG9maW5kZmxhZ3M==').decode())"
myrepositorytofindflags
```

## Other write-ups and resources

- ["Puppy or bagel" / "chihuahua or muffin" image-classification meme](https://www.freecodecamp.org/news/chihuahua-or-muffin-my-search-for-the-best-computer-vision-api-cbda4d6b425d/)
- [Pillow (PIL) image handling](https://pillow.readthedocs.io/)
