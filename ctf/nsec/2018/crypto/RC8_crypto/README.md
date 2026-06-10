# NSEC 2018 : RC8 crypto

**Category:** Crypto
**Points:** 4
**Solves:**
**Description:**

A recent transcript suspected to contain incriminating conversations between the officials in charge of the Mars colonization plan has leaked but is encrypted with the latest top-secret encryption algorithm: RC8! You've recovered the source code to their new encryption algorithm, but the key and seed value are missing. Find a weakness in the scheme and recover the transcript.

> This is the implementation/solver directory for the `crypto leak`
> ([crypto-leak-4](../crypto-leak-4/README.md)) challenge.

## Files

- `RC8_Encrypt.py` — original cipher source with `seed, key` blanked out (`?, ?`).
- `RC8.py` — same source with a *placeholder* `seed, key = 'flag', 123` (NOT the real key).
- `transcript.wav.enc` — the encrypted WAV transcript (the target).
- `test.txt`, `test.txt.enc` — a tiny round-trip test sample (`test.txt.enc` is empty here).
- `rc8_solve.py` — the SageMath key-recovery solver.
- `rc8_solve_pure.py` — a pure-Python port (no Sage) that also decrypts and finds the flag.
- `test_captcha.py` — unrelated test harness (belongs to the captcha challenge); ignore.

## Write-up

### The cipher is a linear (LFSR) stream cipher

`RC8_Encrypt.py` XORs the data with the output of `rc8(seed, key, n)`:

```python
def rc8(state, key, n):
    while (n > 0):
        yield state & 0xff               # emit low byte of the 64-bit state
        for _ in range(8):               # advance state 8 bit-steps
            c, s = key, state
            b = 0
            while c:
                b ^= c & 1 * s & 1       # b = parity(key & state)  (linear over GF(2))
                c >>= 1 ; s >>= 1
            state = state >> 1 | b << 63 # feedback bit shifts in at bit 63
        n -= 1
```

Two structural facts make this breakable:

1. The feedback bit `b = parity(key & state)` is a **linear function** of the
   state over GF(2) (the key is just the tap mask of a 64-bit LFSR).
2. Each emitted byte is `state & 0xff`, and between emissions the state is
   shifted right by 8 bits. Therefore **8 consecutive output bytes are 8
   consecutive bytes of a single 64-bit state**, so any 8 keystream bytes
   reconstruct a full internal state.

### Step 1 — Known plaintext from the WAV header

The plaintext is a `.wav`, so the first 16 bytes are the predictable RIFF/WAVE
header (`RIFF <filesize-8> WAVE fmt `). XORing this against the first 16
ciphertext bytes gives 16 keystream bytes — i.e. two full consecutive states:

```
s1 = leak_to_state([0xd3,0xea,0x3d,0x6a,0xfd,0x66,0xee,0x30])   # outputs 0..7
s2 = leak_to_state([0x5f,0xf4,0x22,0x9e,0xc9,0xd9,0x00,0xc6])   # outputs 8..15
```

`leak_to_state` reassembles the bytes little-endian into a 64-bit integer.

### Step 2 — Solve for the key over GF(2)

Advancing `s1` by 8 LFSR steps must produce `s2`. That is a 64x64 linear system
in the 64 unknown key bits. The Sage solver builds and solves it directly:

```python
pack = lambda a, b: [list(map(int, list('{:064b}'.format(a >> n | b << 64 - n & 2**64 - 1)))) for n in range(64)]
leak_to_state = lambda a: reduce(lambda x, y : (x << 8) + y, a[::-1])

s1 = leak_to_state([0xd3, 0xea, 0x3d, 0x6a, 0xfd, 0x66, 0xee, 0x30])
s2 = leak_to_state([0x5f, 0xf4, 0x22, 0x9e, 0xc9, 0xd9, 0x00, 0xc6])

A = Matrix(Zmod(2), pack(s1, s2))               # GF(2) coefficient matrix
b = vector(int_to_bits(s2)[::-1])               # target = bits of s2
key = int(''.join('01'[i] for i in A.solve_right(b)), 2)
```

I ported this to pure Python (`rc8_solve_pure.py`) so it runs without Sage,
using the same `pack`/target construction and a GF(2) Gaussian elimination:

```python
# build the same A and b, then solve A x = b over GF(2) by elimination
M = [A[r][:] + [b[r]] for r in range(64)]
# ... pivot/eliminate ...
key = int(''.join(str(v) for v in x), 2)
```

Both recover:

```
[+] Seed: 3525868796872878803
[+] Key:  36028806108921863   (0x8000021dcdc007)
[+] keystream matches leak: True
```

### Step 3 — Decrypt and grab the flag

With the initial state `s1` and the key, the whole keystream is reproducible.
Re-running `rc8(s1, key, len(data))` and XORing decrypts `transcript.wav.enc`
into a valid WAV. The flag is stored in the file's ID3/metadata tags.

Commands run:

```
unzip ../crypto-leak-4/crypto_leak.zip   # (or use transcript.wav.enc here)
python3 rc8_solve_pure.py                # solves key + writes transcript.wav
file transcript.wav
#   RIFF (little-endian) data, WAVE audio, Microsoft PCM, 16 bit, mono 44100 Hz
strings -a transcript.wav | grep -i flag
#    FLAG-ccfd9b48a255a25e2557373e429d9dc5
```

### Flag

```
FLAG-ccfd9b48a255a25e2557373e429d9dc5
```

## Other write-ups and resources

- [Challenge 275 on ringzer0team.com](https://ringzer0team.com/challenges/275)
- [Linear-feedback shift register](https://en.wikipedia.org/wiki/Linear-feedback_shift_register)
- [Solving linear systems over GF(2)](https://en.wikipedia.org/wiki/Gaussian_elimination)
