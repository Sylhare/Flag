# NSEC 2019 : NeuroPass

**Category:** Web / Reverse Engineering (Chrome extension + native messaging host)
**Points:**
**Solves:**
**Description:**

"NeuroPass — the one password manager you need for your life." A Chrome extension password
manager built by the in-CTF company *Neurosoft*. It auto-detects login forms, stores the
credentials it sees through a **native-messaging host** (`neuropass`, a Haskell binary
writing to a local SQLite DB), and auto-fills them on return visits. The challenge ships the
packed extension (`neuropass.crx`), the native host (`neuropass`), its registration JSON, and
install/uninstall scripts. The goal is to reverse the credential-protection scheme well
enough to recover a stored password (which is/contains the flag).

## Files

- `neuropass.crx` — the Chrome extension (a CRXv3 = zip with a 593-byte header). Contains
  `manifest.json`, `background.js`, `index.js`, `index.html`, `ctf.neurosoft.neuropass.js`
  (content script) and the CSS.
- `neuropass` — the native messaging host: `ELF 64-bit x86-64`, **Haskell** (uses
  `sqlite-simple`), not stripped. Implements `set_master_pass`, `create_password`,
  `get_password`, `get_users_for_domain` over stdio JSON, persisting to `/opt/neurosoft/data/db`.
- `ctf.neurosoft.neuropass.json` — native-messaging-host registration; restricts the host to
  the extension id `fhbhinloffnbpciglfhgeaenlonbemih`.
- `install.sh` / `uninstall.sh` — deploy the host + JSON and create the SQLite `passwords` table.

## Write-up

### Architecture

```
web page  --(content script ctf.neurosoft.neuropass.js)-->  background.js
                                                               |  chrome.runtime.sendNativeMessage
                                                               v
                                                       neuropass (ELF) --> sqlite db
```

The content script scans every page for a username-like field
(`/(user|username|nom|access|code|email|courriel)/i`) and a password-like field
(`/(pass|password|secret|flag)/i`); when both exist it hooks `submit` to save credentials and
adds a "Choose user" dropdown that auto-fills stored passwords. All storage/retrieval is
delegated to `background.js`, which talks to the native `neuropass` host.

`index.js` + `index.html` are the popup where the user sets the **master password**
(`cmd: "set_master_pass"`).

### The crux: `protect()` in `background.js`

`background.js` is minified/hex-obfuscated. Decoding the `\xNN` string table reveals a single
custom cipher, `protect()`, used to encrypt passwords before they hit the DB (and to decrypt
on read). It is a **keystream XOR cipher seeded by a constant and keyed by the master
password** — i.e. fully reversible if you know (or recover) the master password:

```javascript
function protect(data){
  if(masterPass == "") throw "masterPass is not set";
  var seed = 6854932374839;
  var out = [], k;
  for(var i = 0; i < data.length; i++){
    seed *= masterPass.charCodeAt(i % masterPass.length);   // mix in master pass byte
    seed += 45765432;
    seed %= 4294967296;                                     // keep 32-bit
    k = (seed >> 13) & 0xff;                                // keystream byte
    out.push(data.charCodeAt(i) ^ k);                       // XOR with plaintext
  }
  return String.fromCharCode.apply(null, out);
}
```

Stored value = `btoa(protect(password))` (base64 of the XOR output). Because `protect` is its
own inverse for a fixed master password, reading back is `protect(atob(stored))`.

Key observations / weaknesses for the attack:

1. **The "key" is the user's master password**, fully under attacker control if you can set it.
   The keystream is `(seed >> 13) & 0xff` where `seed` only ever depends on the master-pass
   bytes and public constants `6854932374839`, `45765432`, `2^32`. Nothing secret lives in the
   ELF host — it just base64-stores whatever `background.js` hands it.
2. The state is only 32 bits and advances deterministically, so with any known plaintext
   (the content script even matches fields named `flag`) the keystream — and therefore the
   master password bytes — can be recovered byte-by-byte (each output byte constrains
   `seed` and hence `masterPass.charCodeAt(i % len)`).

### Connection to the `login` challenge

This NeuroPass track pairs with [`../login`](../login/README.md): that photo shows a
*Neurosoft* login form pre-filled by NeuroPass — username `justin`, password rendered as
glyphs. The password the manager auto-fills for `justin` is what protects the target account;
recovering it (via the glyph cipher and/or the `protect`/DB path above) is the objective.

### Commands used

```
unzip neuropass.crx -d crx/            # CRXv3 = zip + 593-byte prefix (unzip warns, still extracts)
file neuropass                         # ELF 64-bit ... Haskell (sqlite-simple)
strings -a neuropass | grep -iE 'flag|password|insert|select'   # confirms plain CRUD host
# background.js hex string table decoded by hand -> protect() above
```

## Other write-ups and resources

- [Chrome native messaging](https://developer.chrome.com/docs/extensions/develop/concepts/native-messaging)
- [CRX file format (v3)](https://chromium.googlesource.com/chromium/src/+/master/components/crx_file/)
- [sqlite-simple (Haskell)](https://hackage.haskell.org/package/sqlite-simple)
