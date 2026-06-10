#!/usr/bin/env python3
from functools import reduce
leak_to_state = lambda a: reduce(lambda x, y: (x << 8) + y, a[::-1])
s1 = leak_to_state([0xd3,0xea,0x3d,0x6a,0xfd,0x66,0xee,0x30])
s2 = leak_to_state([0x5f,0xf4,0x22,0x9e,0xc9,0xd9,0x00,0xc6])

# Exact replication of rc8_solve.py (sage) construction:
pack = lambda a,b: [list(map(int, list('{:064b}'.format((a >> n) | ((b << (64-n)) & (2**64-1)))))) for n in range(64)]
A = pack(s1, s2)                       # 64x64 matrix over GF(2)
b = [int(c) for c in "{:08b}".format(s2)][::-1]   # length-64 target vector

# Solve A x = b over GF(2). A.solve_right(b) in sage.
N = 64
# Augmented matrix
M = [A[r][:] + [b[r]] for r in range(N)]
piv_col_of_row = []
r = 0
for c in range(N):
    sel = None
    for rr in range(r, N):
        if M[rr][c]:
            sel = rr; break
    if sel is None:
        continue
    M[r], M[sel] = M[sel], M[r]
    for rr in range(N):
        if rr != r and M[rr][c]:
            M[rr] = [a ^ d for a, d in zip(M[rr], M[r])]
    piv_col_of_row.append(c)
    r += 1

x = [0]*N
for i, c in enumerate(piv_col_of_row):
    x[c] = M[i][N]

# sage: key = int(''.join('01'[i] for i in A.solve_right(b)), 2)  -> x is MSB-first
key = int(''.join(str(v) for v in x), 2)
print("[+] Seed:", s1)
print("[+] Key:", key, hex(key))

# Verify with the actual rc8 generator
def rc8(state, key, n):
    while n > 0:
        yield state & 0xff
        for _ in range(8):
            c, s = key, state
            bb = 0
            while c:
                bb ^= (c & 1 * s & 1)
                c >>= 1; s >>= 1
            state = state >> 1 | bb << 63
        n -= 1

ks = list(rc8(s1, key, 16))
expected = [0xd3,0xea,0x3d,0x6a,0xfd,0x66,0xee,0x30,0x5f,0xf4,0x22,0x9e,0xc9,0xd9,0x00,0xc6]
print("[+] keystream matches leak:", ks == expected)
print("ks:", [hex(z) for z in ks])

# Decrypt the whole transcript
data = bytearray(open('transcript.wav.enc','rb').read())
for i, x in enumerate(rc8(s1, key, len(data))):
    data[i] ^= x
open('transcript.wav','wb').write(data)
print("[+] decrypted", len(data), "bytes. header:", bytes(data[:16]))
