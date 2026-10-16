# btclib-mnemonics

The mnemonic schemes of bitcoin wallets -- BIP39, SLIP-0039 and
Electrum's -- from the entropy to the seed, in typed Python.

<!-- The badges are what the reader decides with, in three groups: what the
software is and whether it can be used, whether it works, and what the
OpenSSF makes of it.

Inside the second group the gates come first, in the order a commit meets
them, and the sentinels follow in the order section 10 of the organization
standard schedules them -- the badge order *is* the calendar order over
that subset, which is why the two move together or not at all. The day and
hour each sentinel owns live in that section and are not copied here: a
reader wanting the schedule reads it there, where it is still true.

One badge per line keeps a change to one line and every line inside MD013,
whose 80 columns bind only where a space follows them.

A badge that reports no state -- "we use ruff", "we use uv" -- reports a
choice instead, and those are in CONTRIBUTING.md, beside the prose that
says how the choice is enforced.
-->
[![PyPI version](https://img.shields.io/pypi/v/btclib-mnemonics.svg?logo=pypi)](https://pypi.org/project/btclib-mnemonics/)
[![GitHub release](https://img.shields.io/github/v/release/btclib-org/btclib-mnemonics.svg)](https://github.com/btclib-org/btclib-mnemonics/releases)
[![development status](https://img.shields.io/pypi/status/btclib-mnemonics.svg)](https://pypi.org/project/btclib-mnemonics/)
[![license](https://img.shields.io/github/license/btclib-org/btclib-mnemonics.svg)](https://github.com/btclib-org/btclib-mnemonics/blob/main/LICENSE)
[![downloads](https://static.pepy.tech/badge/btclib-mnemonics)](https://pepy.tech/projects/btclib-mnemonics)
[![supported Python versions](https://img.shields.io/pypi/pyversions/btclib-mnemonics.svg?logo=python)](https://pypi.org/project/btclib-mnemonics/)
[![implementation](https://img.shields.io/pypi/implementation/btclib-mnemonics.svg)](https://pypi.org/project/btclib-mnemonics/)
[![wheel](https://img.shields.io/pypi/wheel/btclib-mnemonics.svg)](https://pypi.org/project/btclib-mnemonics/)

[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/btclib-org/btclib-mnemonics/main.svg)](https://results.pre-commit.ci/latest/github/btclib-org/btclib-mnemonics/main)
[![lint workflow status](https://github.com/btclib-org/btclib-mnemonics/actions/workflows/lint.yml/badge.svg?branch=main)](https://github.com/btclib-org/btclib-mnemonics/actions/workflows/lint.yml?query=branch%3Amain)
[![test workflow status](https://github.com/btclib-org/btclib-mnemonics/actions/workflows/test.yml/badge.svg?branch=main)](https://github.com/btclib-org/btclib-mnemonics/actions/workflows/test.yml?query=branch%3Amain)
[![docs workflow status](https://github.com/btclib-org/btclib-mnemonics/actions/workflows/docs.yml/badge.svg?branch=main)](https://github.com/btclib-org/btclib-mnemonics/actions/workflows/docs.yml?query=branch%3Amain)
[![documentation build](https://app.readthedocs.org/projects/btclib-mnemonics/badge/?version=latest)](https://btclib-mnemonics.readthedocs.io)
[![vendored-vectors workflow status](https://github.com/btclib-org/btclib-mnemonics/actions/workflows/vendored-vectors.yml/badge.svg?branch=main)](https://github.com/btclib-org/btclib-mnemonics/actions/workflows/vendored-vectors.yml?query=branch%3Amain)
[![mutation workflow status](https://github.com/btclib-org/btclib-mnemonics/actions/workflows/mutation.yml/badge.svg?branch=main)](https://github.com/btclib-org/btclib-mnemonics/actions/workflows/mutation.yml?query=branch%3Amain)
[![fuzz workflow status](https://github.com/btclib-org/btclib-mnemonics/actions/workflows/fuzz.yml/badge.svg?branch=main)](https://github.com/btclib-org/btclib-mnemonics/actions/workflows/fuzz.yml?query=branch%3Amain)
[![deps-latest workflow status](https://github.com/btclib-org/btclib-mnemonics/actions/workflows/deps-latest.yml/badge.svg?branch=main)](https://github.com/btclib-org/btclib-mnemonics/actions/workflows/deps-latest.yml?query=branch%3Amain)
[![pypi-install workflow status](https://github.com/btclib-org/btclib-mnemonics/actions/workflows/pypi-install.yml/badge.svg?branch=main)](https://github.com/btclib-org/btclib-mnemonics/actions/workflows/pypi-install.yml?query=branch%3Amain)
[![deps-oldest workflow status](https://github.com/btclib-org/btclib-mnemonics/actions/workflows/deps-oldest.yml/badge.svg?branch=main)](https://github.com/btclib-org/btclib-mnemonics/actions/workflows/deps-oldest.yml?query=branch%3Amain)
[![os-macos workflow status](https://github.com/btclib-org/btclib-mnemonics/actions/workflows/os-macos.yml/badge.svg?branch=main)](https://github.com/btclib-org/btclib-mnemonics/actions/workflows/os-macos.yml?query=branch%3Amain)
[![os-ubuntu workflow status](https://github.com/btclib-org/btclib-mnemonics/actions/workflows/os-ubuntu.yml/badge.svg?branch=main)](https://github.com/btclib-org/btclib-mnemonics/actions/workflows/os-ubuntu.yml?query=branch%3Amain)
[![os-windows workflow status](https://github.com/btclib-org/btclib-mnemonics/actions/workflows/os-windows.yml/badge.svg?branch=main)](https://github.com/btclib-org/btclib-mnemonics/actions/workflows/os-windows.yml?query=branch%3Amain)
[![links workflow status](https://github.com/btclib-org/btclib-mnemonics/actions/workflows/links.yml/badge.svg?branch=main)](https://github.com/btclib-org/btclib-mnemonics/actions/workflows/links.yml?query=branch%3Amain)
[![sdist-rebuild workflow status](https://github.com/btclib-org/btclib-mnemonics/actions/workflows/sdist-rebuild.yml/badge.svg?branch=main)](https://github.com/btclib-org/btclib-mnemonics/actions/workflows/sdist-rebuild.yml?query=branch%3Amain)
[![codeql workflow status](https://github.com/btclib-org/btclib-mnemonics/actions/workflows/codeql.yml/badge.svg?branch=main)](https://github.com/btclib-org/btclib-mnemonics/actions/workflows/codeql.yml?query=branch%3Amain)

[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/btclib-org/btclib-mnemonics/badge)](https://scorecard.dev/viewer/?uri=github.com/btclib-org/btclib-mnemonics)
[![OpenSSF Best Practices](https://www.bestpractices.dev/projects/15087/badge)](https://www.bestpractices.dev/projects/15087)
[![OpenSSF Baseline](https://www.bestpractices.dev/projects/15087/baseline)](https://www.bestpractices.dev/projects/15087)

It is fully annotated and ships `py.typed`, and it imports nothing
but the standard library.

## What is here

- [BIP39](https://github.com/bitcoin/bips/blob/master/bip-0039.mediawiki)
  mnemonics, in every language of the reference implementation's word
  lists: from entropy to sentence and back, the language read off the
  words, and the seed a sentence and a passphrase stretch to (`bip39`)
- [SLIP-0039](https://github.com/satoshilabs/slips/blob/master/slip-0039.md)
  Shamir backups: a master secret split into groups of shares and put
  back together, the passphrase encryption and the extendable backup
  flag included (`slip39`)
- Electrum's own mnemonics: the versioned ones, generated and read the
  way Electrum generates and reads them, their seed, and the pre-2.0
  scheme with its hex seed and master private key (`electrum`)
- which of those schemes a sentence belongs to, where more than one
  claims it (`dispatch`)
- the entropy the schemes are generated from, drawn from the operating
  system's CSPRNG or from dice rolls, prompted in the mnemonic's language
  (`entropy`)
- the word lists and the normalization every scheme reads a sentence
  through (`mnemonic`)

What a seed derives to -- a BIP32 key, an address, a wallet -- is not
here: [btclib-wallet](https://github.com/btclib-org/btclib-wallet) is the
library above this one.

The suite answers to vectors their authors publish -- the reference
implementations' own and Electrum's -- and
[tests/_data/README.md](./tests/_data/README.md) pins each vendored file
to the upstream commit it was copied from.

## Installing

```shell
python -m pip install --upgrade btclib-mnemonics
```

## A seed from a mnemonic, and a secret split into shares

```python
from btclib_mnemonics import bip39, dispatch, slip39

words = bip39.mnemonic_from_entropy(bytes(16))
assert words == "abandon " * 11 + "about"
seed = bip39.seed_from_mnemonic(words, "TREZOR")
assert seed.hex().startswith("c55257c360c07c72")
assert dispatch.seed_type_from_mnemonic(words) == "bip39"

# SLIP-0039's master secret is itself the seed a wallet derives from, so
# it is a secret of its own here: a 2-of-3 split, and two shares back
master_secret = bytes(range(16))
(shares,) = slip39.mnemonics_from_master_secret(master_secret, [(2, 3)])
assert slip39.master_secret_from_mnemonics(shares[1:]) == master_secret
```

`tests/readme_test.py` runs every Python block of this file, so the
example above is the one the suite checks.

## Security

[SECURITY.md](./SECURITY.md) says how to report a vulnerability, which
versions are supported, and how a published file is traced back to the
run that built it.
[ASSURANCE_CASE.md](./ASSURANCE_CASE.md) argues why what it promises
holds: the threat model, the trust boundaries, and the weaknesses a
package of this kind is exposed to.

## Contributing

[CONTRIBUTING.md](./CONTRIBUTING.md) has the commands each CI job runs,
verbatim. `uv sync` creates the environment; uv is the only tool that has
to be installed. [REVIEWING.md](./REVIEWING.md) is what a pull request is
answered against.

How the organization decides, and who holds which role, is its
[GOVERNANCE.md](https://github.com/btclib-org/.github/blob/main/GOVERNANCE.md);
what it intends to do, and what it deliberately does not, is its
[ROADMAP.md](https://github.com/btclib-org/.github/blob/main/ROADMAP.md).

## Links

- Documentation: <https://btclib-mnemonics.readthedocs.io/>
- Source: <https://github.com/btclib-org/btclib-mnemonics>
- Releases: <https://github.com/btclib-org/btclib-mnemonics/releases>
- [CHANGELOG.md](./CHANGELOG.md), and [RELEASE_NOTES.md](./RELEASE_NOTES.md)
  for what a release asks a user to act on

---

The btclib organization and its projects are actively supported by
[DGI](https://dgi.io) and [CheckSig](https://checksig.com).
