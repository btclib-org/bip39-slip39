# Release notes

Notable changes are documented here.
[CHANGELOG.md](./CHANGELOG.md) is the record behind them: this file says
what a user has to act on, that one says what changed.

Versions are *[calendar versions](https://calver.org/)*, `YYYY.M.D`: the
number says when a release was cut, and promises nothing about
compatibility, so a breaking change is announced in this file — read it
before upgrading, rather than a digit.

## v2026.11.13

- **`dispatch.seed_type_from_mnemonic` and
  `dispatch.all_seed_types_from_mnemonic` default `lang` to `None`, and try
  every BIP39 word-list that holds the words** (#253), where v2026.11.12 tried
  English alone. An Italian mnemonic answers `"bip39"` where it answered
  `""`; `lang=""` tries every list where it tried none; `lang=None` is
  accepted where it was refused with `Bip39Slip39TypeError`. A caller that
  relied on the English default passes `lang="en"`. Against v2026.11.12,
  griffe reports these two defaults, and `api_gaps.py` the annotation of the
  same `lang`, `str` to `str | None`; neither reports anything else.
- **`bip39.langs_from_mnemonic` is new**: it returns every BIP39 language whose
  word-list holds each word of the sentence.
- **`bip39.seed_from_mnemonic` seeds a sentence valid in two word-lists with a
  different entropy in each** (#257), where v2026.11.12 refused it as
  ambiguous with `verify_checksum=True`. The seed stretches the sentence, so it
  is the same whichever list is meant. A caller that relied on the refusal
  gets a seed instead.
- **The attestations name `reusable-build.yml` at btclib-org/.github's commit
  `cb5a79443399980ba717df2dea23dbedf6bdbc3a`, its tag v2026.11.12**, where
  v2026.11.12's named `305b1840909ffd49d653d20cc6f5f9e1ab6a3382`. The command
  `SECURITY.md` gives names the signer without a ref and verifies both. A check
  that pins `--signer-workflow` to the old commit fails: drop the ref.

## v2026.11.12

- **Nothing in the code to act on.** The code under `src/` takes Sourcery's
  rewrites, and griffe and `api_gaps.py` find no break in the public API
  against v2026.11.2. [CHANGELOG.md](./CHANGELOG.md) lists what moved.
- **The attestations name `reusable-build.yml` at btclib-org/.github's commit
  `305b1840909ffd49d653d20cc6f5f9e1ab6a3382`, its tag v2026.11.10**, where
  v2026.11.2's named `ed616d71c43cd4c8bded40d1182befccd99e6ee7`. The command
  `SECURITY.md` gives names the signer without a ref and verifies both. A check
  that pins `--signer-workflow` to the old commit fails: drop the ref.

## v2026.11.2

- **`electrum.old_master_prv_key_from_mnemonic` derives from a pre-2.0 mnemonic
  whose words decode to an odd number of hex characters** (#185), where
  v2026.10.24 refused it as not octets. Its master public key matches Electrum's
  own test of such a seed, which is on Electrum's master branch and in no
  Electrum release on 2026-11-02. A caller that relied on the refusal gets a key
  instead.
- **`old_master_prv_key_from_mnemonic` and `old_mnemonic_from_hex_seed` change
  a refusal's message**, for a caller that matches it; the exception is still
  `Bip39Slip39ValueError`. `old_master_prv_key_from_mnemonic` refuses a seed
  written as hex with whitespace between pairs as "pre-2.0 electrum seed is not
  a hex string", where it said the seed decodes to hex characters "which are
  not octets". `old_mnemonic_from_hex_seed` refuses a hex seed of odd length as
  "not a multiple of eight", where it said "not a hex string".
- **The attestations name `reusable-build.yml` at a commit, not at
  `refs/heads/main`.** The signer is btclib-org/.github's
  `reusable-build.yml` at `ed616d71c43cd4c8bded40d1182befccd99e6ee7`, its tag
  v2026.10.29, where v2026.10.24's was at `refs/heads/main`. The command
  `SECURITY.md` gives names the signer without a ref and verifies both. A check
  that pins `--signer-workflow` to `@refs/heads/main` fails: drop the ref.
- **The homepage is <https://btclib.org/bip39-slip39/>** in the package
  metadata, where it was the documentation, which stays at
  <https://bip39-slip39.readthedocs.io/>.

## v2026.10.24

The first release of `bip39-slip39`, the new name of `btclib-mnemonics`,
which gets no release after v2026.10.17.

- **Install `bip39-slip39` instead of `btclib-mnemonics`.** Replace the
  requirement `btclib-mnemonics` by `bip39-slip39>=2026.10.24`, and
  uninstall the old distribution, which would otherwise stay beside it.
- **Import `bip39_slip39` instead of `btclib_mnemonics`.** The modules
  `bip39`, `dispatch`, `electrum`, `entropy`, `exceptions`, `mnemonic` and
  `slip39` keep their names, as do the functions and classes in them
  except the exceptions below, so `from btclib_mnemonics import bip39`
  becomes `from bip39_slip39 import bip39`. Read the version with
  `importlib.metadata.version("bip39-slip39")`.
- **The exceptions are renamed** (#148): `Bip39Slip39Exception`,
  `Bip39Slip39ValueError` and `Bip39Slip39TypeError` replace
  `BTClibMnemonicsException`, `BTClibMnemonicsValueError` and
  `BTClibMnemonicsTypeError`. Change every `except` and `import` that
  names one.
- **The release files are named `bip39_slip39-*`**: the wheel, the sdist
  and the SBOM `.cdx.json`, where they were `btclib_mnemonics-*`. A script
  that downloads one by the old name fails.
- **Verify a release by the repository's id** (#158), as `SECURITY.md` says:
  `gh attestation verify --owner btclib-org`, with `sourceRepositoryIdentifier`
  checked against `gh api repos/btclib-org/bip39-slip39 --jq .id`. `--repo`
  compares the current name, and refuses every release signed before a rename.
- **The repository and the documentation moved.**
  <https://github.com/btclib-org/bip39-slip39> and
  <https://bip39-slip39.readthedocs.io/> replace the old addresses.
- **`entropy.bin_str_entropy_from_rolls` loses its `shuffle` parameter.**
  The rolls are read in the order given, so the same rolls give the same
  entropy. Drop the argument.
- **`entropy.bin_str_entropy_from_random` loses its `entropy` and
  `to_be_hashed` parameters.** It is a plain draw of `bits` bits from
  `secrets`, no longer hashed and no longer capped at 512 bits, and it
  refuses fewer than one bit. Drop the arguments.
- **`entropy.collect_rolls` reads Enter alone as a D6 rolled by hand.**
  `a` alone still automates a D6, and the prompts say `6` where they said
  `a6`. An answer of more than three digits, for the dice sides or a roll,
  is asked for again.
- **Electrum's `entropy_from_mnemonic` refuses a sentence of more than 47
  words**, 48 for the Portuguese list, before it decodes the words. A longer
  one from `make_seed --nbits 600` is refused, while `version_from_mnemonic`
  and `seed_from_mnemonic` still accept it and give the same seed.

## v2026.10.17

- **Nothing to act on.** The code under `src/` is v2026.10.8's, and
  griffe finds no break in the public API against that release. The tests,
  the tooling, the workflows and the contributor documents moved;
  [CHANGELOG.md](./CHANGELOG.md) lists them.

## v2026.10.8

- **A mnemonic or passphrase holding a lone surrogate is no longer kept whole
  on the error**
  ([GHSA-qjpp-8mp6-7744](https://github.com/btclib-org/btclib-mnemonics/security/advisories/GHSA-qjpp-8mp6-7744)).
  `bip39.seed_from_mnemonic`, and `electrum`'s `seed_from_mnemonic`,
  `version_from_mnemonic` and `entropy_from_mnemonic`, kept the whole
  mnemonic or passphrase in a `UnicodeEncodeError` when it held a lone
  surrogate: 2026.10.2 in the refusal's `__context__`, 2026.9.29 as the error
  raised, which `dispatch.seed_type_from_mnemonic` and
  `dispatch.all_seed_types_from_mnemonic` raised too. Upgrade, and treat a
  mnemonic or passphrase that such an error may have recorded, in a log or an
  error report, as exposed.
- **The attestation bundle is attached as `v<version>.intoto.jsonl`** from
  v2026.10.2 on, where earlier releases attach
  `v<version>.attestation.jsonl`. A script that downloads it by name, or
  passes it to `gh attestation verify --bundle`, uses the new name.

## v2026.10.2

- **BIP39 refuses 512-bit entropy and 48-word mnemonics.** Pass at most
  256 bits. Entropy over the largest size is refused rather than
  truncated, in every scheme.
- **SLIP-0039 refuses master secrets over 64 bytes and shares over 59
  words.** The specification sets no maximum, and 64 bytes is the largest
  BIP32 seed.
- **Verifying a release's attestation names a new signer and the tag.**
  `gh attestation verify` takes
  `--signer-workflow btclib-org/.github/.github/workflows/reusable-build.yml@refs/heads/main`
  and `--source-ref refs/tags/v<version>`; SECURITY.md has the command.
  Earlier releases keep `reusable-attest.yml`.
- **`WordLists.language_files` holds each file name as a `str`.** A
  `pathlib.Path` given to the constructor is stored as its `str`, where it
  was kept as given.

## v2026.9.29

The first release of `btclib-mnemonics`: there is no earlier version of
it to upgrade from.

Coming from `btclib_wallet.mnemonic`, import the modules from
`btclib_mnemonics` instead: `bip39`, `dispatch`, `electrum`, `entropy`,
`mnemonic` and `slip39` keep their names. What does not carry over, one
name at a time:

- **`btclib_wallet.mnemonic`'s own names** -- `WORDLISTS`, `BinStr`,
  `Entropy`, `Mnemonic`, `indexes_from_mnemonic`,
  `mnemonic_from_indexes`, `normalize_mnemonic` and the three public
  entropy functions it re-exported, `bin_str_entropy_from_random`,
  `bin_str_entropy_from_rolls` and `collect_rolls` -- are not
  re-exported by `btclib_mnemonics`, whose root publishes its modules
  only: import each from the module that defines it, `mnemonic` or
  `entropy`. The other seven entropy functions it re-exported are
  private, each named below.
- **`bip39.mxprv_from_mnemonic`** is not here: derive the master key
  from `bip39.seed_from_mnemonic`'s seed.
- **`electrum.mxprv_from_mnemonic`** is not here: derive the master key
  from `electrum.seed_from_mnemonic`'s seed, a function new in this
  package, as the version `electrum.version_from_mnemonic` answers asks.
- **`electrum.old_master_pub_key_from_mnemonic`** is not here: take the
  public key of `electrum.old_master_prv_key_from_mnemonic`'s private key,
  uncompressed and without its `04` prefix, the 128 hexadecimal digits an
  Electrum wallet file holds.
- **`slip39.mxprv_from_mnemonics`** is not here: derive the master key
  from `slip39.master_secret_from_mnemonics`'s master secret.
- **`entropy.bin_str_entropy_from_bytes`** is private: pass the bytes to
  the scheme's `mnemonic_from_entropy`, which reads them.
- **`entropy.bin_str_entropy_from_entropy`** is private, for the same
  reason.
- **`entropy.bin_str_entropy_from_int`** is private, for the same reason.
- **`entropy.bin_str_entropy_from_str`** is private: pass the binary
  string itself.
- **`entropy.bin_str_entropy_from_wordlist_indexes`** is private: use
  `mnemonic.mnemonic_from_indexes` and the scheme's
  `entropy_from_mnemonic`.
- **`entropy.bytes_entropy_from_str`** is private: `int(entropy,
  2).to_bytes(len(entropy) // 8, "big")` is the conversion.
- **`entropy.wordlist_indexes_from_bin_str_entropy`** is private: use the
  scheme's `mnemonic_from_entropy` and `mnemonic.indexes_from_mnemonic`.
- **The exceptions** are `BTClibMnemonicsException`,
  `BTClibMnemonicsTypeError` and `BTClibMnemonicsValueError`, not
  btclib's; each of the last two is also a `TypeError` or a `ValueError`.
