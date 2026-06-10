# Megabeets 0x1

## Introduction

`megabeets_0x1` is a simple **crackme** written by Itay Cohen ([@megabeets](https://www.megabeets.net))
to teach the [radare2](https://www.radare.org/) framework. The goal is to find the single
command-line argument that makes the program print `Success!`.

Three files are provided:

| File | Type |
|------|------|
| `megabeets_0x1`      | ELF 32-bit (Intel 80386), Linux |
| `megabeets_0x1_mac`  | Mach-O 64-bit, macOS |
| `megabeets_0x1.c`    | the original C source |

```
$ ./megabeets_0x1_mac

  .:: Megabeets ::.
Think you can make it?
Nop, Wrong argument.
```

## The logic

Since the source is shipped ([`megabeets_0x1.c`](megabeets_0x1.c)), the check is easy to read.
The interesting part is `beet()` and the `rot13()` helper:

```c
int beet(char *name)
{
    char buf[128];
    strcpy(buf, name);            // your argv[1]
    char string[] = "Megabeets";
    rot13(string);                // string becomes ROT13("Megabeets")
    return !strcmp(buf, string);  // success when argv[1] == ROT13("Megabeets")
}
```

`main()` prints `Success!` only when `argc >= 2 && beet(argv[1])`. So the password is simply
**ROT13 of the literal `"Megabeets"`**.

## Solving it

### Without radare2 — just compute the ROT13

ROT13 is its own inverse, so encoding `Megabeets` gives the answer directly:

```bash
python3 -c "import codecs; print(codecs.encode('Megabeets','rot13'))"
# -> Zrtnorrgf
```

radare2 ships a hash/crypto tool that does the same:

```bash
rahash2 -E rot -S s:13 -s 'Megabeets'
# -> Zrtnorrgf
```

### Recovering it from the binary in radare2

If you didn't have the source, you'd find the `"Megabeets"` literal and the `rot13` call by
reversing `beet`:

```bash
r2 -A megabeets_0x1        # open and auto-analyse
[0x...]> afl               # list functions -> sym.beet, sym.rot13, main
[0x...]> iz                # strings -> "Megabeets" lives in .rodata
[0x...]> pdf @ sym.beet    # disassemble beet: strcpy(buf, argv[1]); rot13(string); strcmp
```

Seeing `beet` rot13-encode `"Megabeets"` and `strcmp` it against your input tells you the
expected argument is `ROT13("Megabeets")`.

## Confirming the flag

```bash
$ ./megabeets_0x1_mac Zrtnorrgf

  .:: Megabeets ::.
Think you can make it?
Success!
```

(The 32-bit ELF behaves identically; run it under a 32-bit-capable host, e.g.
`docker run --rm --platform linux/386 -v "$PWD":/work -w /work i386/ubuntu ./megabeets_0x1 Zrtnorrgf`.)

You can also just feed it straight to the binary inside radare2's debugger, as shown in the
parent [radare2 readme](../readme.md):

```bash
ood Zrtnorrgf   # reopen in debug mode with the argument
dc              # continue -> "Success!"
```

### Answer

```
Zrtnorrgf
```

(i.e. `ROT13("Megabeets")`)

## Other write-ups and resources

- [A Journey into Radare 2 – Part 1, by Megabeets](https://www.megabeets.net/a-journey-into-radare-2-part-1/)
- [radare2](https://www.radare.org/r/down.html)
- [ROT13](https://en.wikipedia.org/wiki/ROT13)
