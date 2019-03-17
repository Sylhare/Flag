# Sharif CTF 2016 - RE150 ‘Serial’ Writeup

Starting out as I always do, I ran `file`, `strings`, etc.
Then ran in my VM in `gdb` and opened the binary in IDA Pro. 
The first thing I noticed is that IDA can't view main in graph mode.
 They are likely jumping around weird to trick disassemblers.

Looking in IDA, a few instruction into main there's a jump _back_ a few bytes, into the middle of another instruction -- suspicions confirmed.
That's no problem. 

- Hit `D` on the instruction that overlaps with the jump target to turn the code into data, 
- Move to the correct byte, and then hit `C` to start disassembling from there.

![before](gf1.png)

That makes more sense, but there's another jump into the middle of some instructions. 
You'll find this a lot in this binary, 
but you can just keep hitting `D` and `C` to fix it up. 

Since the jumps go backwards, you'll be disassembling 'over' some of the jumps, 
but because they're only there to confuse you, you can pretty much just follow the code straight down.
After doing that cleanup twice we see a reference to the first string we see "Please Enter the valid key!\n".

Continuing to clean as you proceed down, there's a call to `strlen` ensuring the length is 16 bytes. 
I like to put breakpoints on checks like these and restart the program to validate, but otherwise do most of my work statically.

```bash
b *0x400A2C
r
123456
# bp is hit, ensure it doesn't jump
r # restart
1234567890123456
# bp is hit, make sure it jumps
```

![char compare](gf2.png)

The rest of the check is straight forward:
 - It checks that the *x*th byte is some hard code value
 - and then checks that the value of the *x*th byte _from the back_, plus the *x*th byte adds up to some other hardcoded value.
 - You can hit `R` on the byte values to see the ASCII representation, 
 but this won't work on the back half checks, because the two characters' sums aren't likely still in the ASCII range. 
 - After 8 of these double checks you should have what you need.

flag: EZ9dmq4c8g9G7bAV

```bash
vagrant@kali:/vagrant$ echo EZ9dmq4c8g9G7bAV | ./serial
Please Enter the valid key!
Serial number is valid :)
```