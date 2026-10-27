# Vendored test vectors

This file is about `tests/_data/`, plus the shipped data this package
holds that nothing else pins: `src/bip39_slip39/_data/wordlist.txt`,
SLIP-0039's word list. A word list is the most load-bearing vendored file
there is -- every share ever written with it decodes through it -- and
unlike `english.txt` it has no byte-identical copy under `tests/` for an
entry to name instead. The package's other word lists have no entry
because each is already pinned somewhere else or not at all:
`english.txt` through the test copy below, `electrum_old_english.txt` and
`electrum_portuguese.txt` through the pins `src/bip39_slip39/electrum.py`
carries beside the constants naming them, and the other BIP39 lists
nowhere, which is a gap rather than a statement about them.

The entries below came from btclib-wallet's own `tests/_data/README.md`
with the files they describe, as btclib-wallet's came from btclib's: an
entry pins where a file came from and whether our copy still matches it,
and a test module names its upstream and points here for the revision. A
citation that names the wrong upstream is corrected in the module; this
file is not where that correction lives.

## Naming

A vendored file carries the name its upstream publishes it under, wherever
upstream publishes a file at all. A name of our own has no upstream name
to be compared against, so the citation in the module that loads it can
drift to a path upstream never had and nobody catches it -- the byte
comparison below is the only check the naming cannot fool.

The files that keep a name of their own do so because there is no upstream
file whose name they could take, or because the upstream name is taken:

- `bip39_test_vectors.json` is trezor's `vectors.json` byte for byte, and
  keeps a name of its own anyway: `vectors.json` is taken in the very same
  directory, by SLIP-0039's own file of that name.
- `electrum_test_vectors.json`, `electrum_language_vectors.json` and
  `fakeenglish.txt` are btclib's own: no upstream file for any of them, so
  no upstream name to take.

## Reading an entry

Where an entry pins to a commit, it gives the upstream repository, the
path in it, and the commit. A `blob` line, where the entry carries one,
gives the git blob SHA-1 of what that entry pins; what it pins, and
whether it was compared byte for byte, is the entry's own to say. An
`ours` line gives the blob of the file kept here where that is not the
`blob`: a file with its trailing newline or its whitespace changed. Most
entries close on a verdict; one with nothing upstream to compare against
says so in prose instead. The verdicts used:

- **identical** -- our file and the upstream blob are the same bytes.
- **reformatted** -- same parsed JSON value, different whitespace.
- **composed locally** -- there is nothing upstream to compare, so the
  entry says what stands in for one.

`pulled` is the date of the btclib commit that put the current content in
btclib's tree, from `git log --follow --diff-filter=A` there: the files
came here unchanged, by way of btclib-wallet. `behind` counts upstream
revisions of that path since the pin. It is a staleness figure, not a
defect: a vector file is a fixed set of cases and refreshing it is a
decision, not a chore.

A vector this package fails is vendored anyway and marked `xfail`, never
left out: an absent vector hides the defect it would have shown, and
`xfail_strict` turns the marker red the day the defect is fixed.

## Re-checking a pin

The commit stands in a fence of its own, sitting inside the API path
rather than at the end of the command; the fence below reads it as
`${commit:?}`, the shell's must-be-set form, so a paste of that fence
alone fails naming the variable.

```shell
commit=<the pin the entry gives>
```

```shell
git hash-object tests/_data/vectors.json
gh api "repos/trezor/python-shamir-mnemonic/git/trees/${commit:?}" \
    --jq '.tree[] | select(.path == "vectors.json") | .sha'
```

The comparison is on git blob SHA-1, not sha256: it is what a tree entry
already carries, so nothing has to be downloaded, and `git hash-object`
reproduces it locally.

`.github/workflows/vendored-vectors.yml` runs weekly, for every entry
whose heading is one file's path and which carries a `blob` or an `ours`
line. It holds the file to `ours` (or `blob`), holds `blob` to upstream's
at `commit`, and fails, naming the file, on a mismatch: a file edited here
and a pin whose blob is not the one at its commit both fail. It also
reports an entry whose upstream moved past the pin. Add an `ours` line to
a new entry whose file is not upstream's bytes, and a `-text` line for the
file to `.gitattributes`.

## bitcoin/bips

### `tests/_data/english.txt`

```text
repo    bitcoin/bips
path    bip-0039/english.txt
commit  ce1862ac6bcffa1dd20aad858380e51e66e949ea  2014-02-07
blob    942040ed50f7205cafc465496229128ba4f78e75
pulled  2018-06-01
behind  0 revisions; that commit is the tip of the path
```

Verdict: **identical**. The BIP39 English wordlist has never been
changed, so this is the one pin that cannot go stale.

## Other projects

### `tests/_data/bip39_test_vectors.json`

```text
repo    trezor/python-mnemonic
path    vectors.json
commit  b57a5ad77a981e743f4167ab2f7927a55c1e82a8  2024-08-27
blob    d362a5d4eb1ba800a52aec30116915cd4576e1fd
pulled  2018-06-01, refreshed 2026-08-02
behind  0 revisions; that commit is the tip of the path
```

Verdict: **identical**. Every language array, in order and value for
value, at the indentation upstream writes them with, so
`git hash-object` on our copy answers the blob id above and a refresh is
the fetch itself:

```shell
gh api -H 'Accept: application/vnd.github.raw' \
    '/repos/trezor/python-mnemonic/contents/vectors.json?ref=master' \
    > tests/_data/bip39_test_vectors.json
```

Each vector carries a BIP32 root extended private key beside its seed.
The seed is where this package stops, so `tests/bip39_test.py` reads the
seed and leaves the key unread rather than cutting a column out of
upstream's bytes. The one case that is ours, the last English vector with
tabs, newlines, doubled spaces and a form feed through the mnemonic, is a
`pytest.param` in `tests/bip39_test.py` beside the ones the file feeds: in
the array it would have to be re-added by hand at every refresh, and
would go missing the once nobody remembered.

### `tests/_data/test_JP_BIP39.json`

```text
repo    bip32JP/bip32JP.github.io
path    test_JP_BIP39.json
commit  360c05a6439e5c461bbe5e84c7567ec38eb4ac5f  2017-08-20
blob    6d8c40b19e5d4b899f9f3c2addbf994d150b245b
ours    4e7efab9ced430060a6646c77770cd387203b757
pulled  2026-08-02
behind  0 revisions; that commit is the tip of the path
```

Verdict: **reformatted**. JSON-equal; upstream's indentation wanders,
and ours is what `json.dumps(indent=4)` writes.

bip-0039 cites this file by URL in its own Test vectors section, beside
the reference implementation's, for the case that file does not cover:
"Japanese wordlist test with heavily normalized symbols as passphrase".
The passphrase is one string in NFC and another in NFKD, and the
sentences are published composed against word-lists published
decomposed, so these are the vectors that fail when normalisation is
skipped anywhere. The `bip32_xprv` field is left unread, as in the file
above.

### `tests/_data/electrum_language_vectors.json`

btclib's own, cross-checked against an application rather than copied
from a project. Electrum's `make_seed` run with `randrange` patched to a
constant, once per language, which is the same starting point
`mnemonic_from_entropy` takes: what it returned is the mnemonic, and
`mnemonic_to_seed` of it is the seed. Electrum publishes no vector of that
kind -- its own `SEED_TEST_CASES` are sentences to read, not entropies to
generate from -- so there is nothing upstream to pin or to refresh
against; regenerate them from electrum's `mnemonic.py` if they are ever
doubted.

The Portuguese sentences beside them answer electrum's
`bip39_is_checksum_valid` yes and no, over its own Portuguese list.

In a file rather than inline like every other electrum vector in
`tests/electrum_test.py`, and the reason is this directory: the lint
gate's spell checkers read a python source and skip `_data`, and `typos`
runs with `--write-changes`. Measured, it corrected a word of the
Portuguese sentence into the English word it is one letter away from.

Pulled 2026-08-02.

### `src/bip39_slip39/_data/wordlist.txt`

```text
repo    satoshilabs/slips
path    slip-0039/wordlist.txt
commit  1524583213f1392321109b0ff0a91330836ecb32  2019-03-02
blob    5673e7ca7f20ed7a5e70b3a7fa5e6df277ee29ab
pulled  2026-08-02
behind  0 revisions; that commit is the tip of the path
```

Verdict: **identical**. SLIP-0039's word list, and the only one it
defines: the SLIP supports no localization, so there is no second language
to leave out and no decision behind shipping one.

`tests/slip39_test.py` re-checks the criteria the SLIP states for the
list -- its length, the shortest and the longest word, and every
four-letter prefix distinct -- which is what turns a corrupted copy into
a red test rather than into shares nobody can read. Not the whole of
`slip-0039/test_wordlist.sh`, which also measures Damerau-Levenshtein
distance: that is a property of the list upstream chose, not of our copy
of it.

### `tests/_data/vectors.json`

```text
repo    trezor/python-shamir-mnemonic
path    vectors.json
commit  1525df19df504b1f69b49179140119959f317f24  2024-05-14
blob    d98c387aa1feb32ca9e6e4410cff870dfc6fb358
ours    2e6da291bdb7824d032e7962a4020f2a8bff9fa6
pulled  2026-08-02
behind  0 revisions; that commit is the tip of the path
```

Verdict: **identical but for a trailing newline** -- our copy is that
blob plus the `\n` the `end-of-file-fixer` hook added, so our blob is
`2e6da291`. Each vector is a description, mnemonics, a master secret and
a BIP32 root extended private key; an empty master secret means combining
those mnemonics must fail. Every vector is exercised, the failing ones
included: an invalid vector left out is a check nobody makes. The key is
left unread, the master secret being where this package stops.

The reference implementation rather than the SLIP: SLIP-0039's own "Test
vectors" section carries no file, it links to this one. The pin is the
commit that added the extendable backup flag and the vectors for it,
which is also the tip of the path.

The valid vectors whose one share is the whole backup are checked in
both directions: such a share's value is the encrypted master secret itself
and therefore involves no randomness the vector does not record, so each
mnemonic is regenerated word for word from the master secret. The other
valid ones are recovery only, a share of a larger threshold being random
by construction.

## Not vendored from anywhere

### `tests/_data/electrum_test_vectors.json`

**Unresolved, and probably unresolvable.** These mnemonics with their
root keys and addresses are in no upstream repository: a GitHub code
search for the first mnemonic returns btclib and one fork of btclib, and
they are not in spesmilo/electrum's `tests/`. They were produced by
running Electrum, and no record says which version.

So they are btclib's, cross-checked against an application rather than
copied from a project. Treat them as ours: nothing upstream will ever
refresh them. The file holds no seed, so the root key is what the seed
is checked against: `tests/electrum_test.py` takes BIP32's master key
generation, and the one hardened step a "segwit" seed takes, over the
seed `electrum.seed_from_mnemonic` answers, and compares the chain code
and the key with the ones the extended key serializes. The public key and
the address are left unread.

They are not the only Electrum vectors: `tests/electrum_test.py` carries
spesmilo/electrum's own, inline -- the `SEED_TEST_CASES` seeds and the
`Test_seeds` seed-type table of its `tests/test_mnemonic.py`, and the
`UNICODE_HORROR` passphrase of its `tests/test_wallet_vertical.py`. Not
vendored as files here: each block is small enough to read, and a
citation just above the values is one that gets checked. The
revisions those blocks were read at are pinned in the comments beside
them.

The pre-2.0 scheme is the same arrangement and more of upstream's
values, added for issue btclib-org/btclib#208. The scheme has no
specification -- it predates the BIPs -- so a vector btclib generated
would be testing btclib against itself, and each of these is a value
published by spesmilo/electrum:

- the mnemonic-to-hex pair of `Test_OldMnemonic.test`, in
  `tests/test_mnemonic.py`, which is the only published pair and the only
  thing that pins the encoder;
- the mnemonic, hex seed and master public key of
  `test_electrum_seed_old`, and the mnemonic and master public key of
  `test_sending_offline_old_electrum_seed_online_mpk`, both in
  `tests/test_wallet_vertical.py`;
- the hex seed and `master_public_key` of the pre-2.0 wallet file in
  `tests/test_storage_upgrade.py`.

A master public key is a point of the curve, which this package does not
compute: `tests/electrum_test.py` multiplies the master private key the
package answers by the generator, over ecc, and compares.

The word-list they run over has no entry here, and being outside
`tests/` is not the reason -- `wordlist.txt` is outside it and has one.
`src/bip39_slip39/_data/electrum_old_english.txt` is pinned where it is
used: it is shipped code, transcribed from the `_words` tuple of
`electrum/old_mnemonic.py`, and `src/bip39_slip39/electrum.py` carries
that pin beside the constant that names the file.

Pulled 2018-06-11; the pre-2.0 values 2026-08-02.

### `tests/_data/fakeenglish.txt`

Verdict: **composed locally**. btclib's own, and deliberately broken:
`english.txt` with the first word, `abandon`, deleted, so that
`WordLists.load_lang` raises "invalid wordlist length". Not vendored,
nothing to pin; regenerate it from `english.txt` if that ever changes,
which its entry above says it has not.

Pulled 2018-06-01.

## What is not pinned, and why

- **`tests/_data/electrum_test_vectors.json`** has no upstream. Stated
  above rather than guessed at.
- **`tests/_data/electrum_language_vectors.json`** has none either, and
  for a reason that will not change: electrum publishes no vector for the
  sentence it *generates* from a given entropy. Ours were produced by
  running its code, which is a procedure to repeat rather than a revision
  to pin, and the entry above gives it.
- **The suite asks upstream for nothing.** It hashes each pinned file
  offline, against the `ours` or `blob` its entry records, and that is a
  deliberate stopping point: a network call in the test suite would trade
  a documented drift for a flaky one. The weekly `vendored-vectors`
  workflow asks upstream instead: a byte mismatch fails the run, and a pin
  that moved opens an issue.

## Summary

No count here, and no count in front of the lists below: a count is a
line every open branch has to edit. The lists *are* the fact the number
summarized, and the tree answers whenever the number is wanted:

```shell
git ls-files 'tests/_data/*' src/bip39_slip39/_data/wordlist.txt \
    | grep -cv 'README.md'
```

Against a pinned upstream blob:

- identical byte for byte: `english.txt`, `wordlist.txt` and
  `bip39_test_vectors.json`.
- identical but for a trailing newline: `vectors.json`.
- JSON-equal, reformatted: `test_JP_BIP39.json`.

Not checked byte for byte against one:

- transcribed: none.
- not vendored: `electrum_test_vectors.json`,
  `electrum_language_vectors.json` and `fakeenglish.txt` (btclib's own).
  `fakeenglish.txt` is composed rather than recorded: `english.txt` with
  one word deleted.
