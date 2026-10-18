# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""An atheris harness fuzzing every decoder that reads a mnemonic.

A SLIP-0039 share is handed back by whoever held it, and SLIP-0039's
threshold is there because some of those holders may be compromised:
`slip39.share_from_mnemonic` reads its header, padding and checksum
before anything about the share is known. The BIP39 and Electrum
readers are the other two ways a sentence enters the package, and they
take the same input: `bip39.entropy_from_mnemonic` and
`electrum.version_from_mnemonic` both read the words, the latter
hashing the sentence and testing it against the pre-2.0 word-list
first.

Every other decoder `tests/fuzz_test.py` lists is called on the same
text: the language, entropy, seed, master key and word index readers, and
the recombination of shares, which takes one share per line.

A crash here on hostile input is a defect in the decoder, never in this
harness: `data` is decoded as UTF-8 and handed straight to each entry
point, bytes that are no UTF-8 being refused before any of them could
be. `BTClibMnemonicsException` is what each answers malformed input
with, so that family is caught below as the expected outcome; any other
exception propagates to atheris as the finding it is. A share that
decodes is encoded again, and has to spell the sentence it came from as
`normalize_mnemonic` reads it: a word is looked up in its NFKD form, so
a fullwidth letter is read as the letter.

The seed corpus is one sentence of each scheme.
"""

from __future__ import annotations

import contextlib
import sys

import atheris

from btclib_mnemonics import bip39, electrum, mnemonic, slip39
from btclib_mnemonics.exceptions import BTClibMnemonicsException
from btclib_mnemonics.mnemonic import normalize_mnemonic

# tests/fuzz_corpus_test.py reads this by ast.literal_eval, never by
# importing the module -- atheris below is CI-only and undeclared in
# pyproject.toml, so the test must not execute this file
ENTRY_POINTS = (
    "btclib_mnemonics.bip39:entropy_from_mnemonic",
    "btclib_mnemonics.electrum:version_from_mnemonic",
    "btclib_mnemonics.slip39:share_from_mnemonic",
)


def fuzz_target(data: bytes) -> None:
    """Read `data` as a BIP39, an Electrum and a SLIP-0039 sentence.

    `BTClibMnemonicsException` is swallowed as each entry point's own
    refusal of malformed input; any other exception propagates, which is
    how atheris tells a defect in the decoder from the domain of input it
    already rejects.
    """
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return
    with contextlib.suppress(BTClibMnemonicsException):
        bip39.entropy_from_mnemonic(text)
    with contextlib.suppress(BTClibMnemonicsException):
        electrum.version_from_mnemonic(text)
    with contextlib.suppress(BTClibMnemonicsException):
        bip39.lang_from_mnemonic(text)
    with contextlib.suppress(BTClibMnemonicsException):
        electrum.entropy_from_mnemonic(text)
    with contextlib.suppress(BTClibMnemonicsException):
        electrum.lang_from_mnemonic(text)
    with contextlib.suppress(BTClibMnemonicsException):
        electrum.hex_seed_from_old_mnemonic(text)
    with contextlib.suppress(BTClibMnemonicsException):
        bip39.seed_from_mnemonic(text, "")
    with contextlib.suppress(BTClibMnemonicsException):
        electrum.seed_from_mnemonic(text, "")
    with contextlib.suppress(BTClibMnemonicsException):
        electrum.old_master_prv_key_from_mnemonic(text)
    with contextlib.suppress(BTClibMnemonicsException):
        mnemonic.indexes_from_mnemonic(text, "en")
    with contextlib.suppress(BTClibMnemonicsException):
        slip39.master_secret_from_mnemonics(text.split("\n"))
    with contextlib.suppress(BTClibMnemonicsException):
        slip39.encrypted_master_secret_from_mnemonics(text.split("\n"))
    with contextlib.suppress(BTClibMnemonicsException):
        share = slip39.share_from_mnemonic(text)
        if slip39.mnemonic_from_share(share) != normalize_mnemonic(text):
            msg = "a decoded share encodes to another sentence"
            raise AssertionError(msg)


def main() -> None:
    """Wire `fuzz_target` to libFuzzer through atheris."""
    atheris.instrument_all()
    atheris.Setup(sys.argv, fuzz_target, enable_python_coverage=True)
    atheris.Fuzz()


if __name__ == "__main__":
    main()
