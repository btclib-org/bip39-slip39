# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""BIP39 entropy / mnemonic / seed functions.

https://github.com/bitcoin/bips/blob/master/bip-0039.mediawiki.

Checksummed entropy (**ENT+CS**) is converted from/to mnemonic.

* bits per word = bpw = 11
* **ENT** = raw entropy
* **CS** = checksum = **ENT** / 32
* **MS** = words in the mnemonic sentence = (**ENT+CS**) / bpw

+-----+----+--------+----+
| ENT | CS | ENT+CS | MS |
+=====+====+========+====+
| 128 |  4 |    132 | 12 |
+-----+----+--------+----+
| 160 |  5 |    165 | 15 |
+-----+----+--------+----+
| 192 |  6 |    198 | 18 |
+-----+----+--------+----+
| 224 |  7 |    231 | 21 |
+-----+----+--------+----+
| 256 |  8 |    264 | 24 |
+-----+----+--------+----+

Every word-list of the reference implementation is here, and three
things follow from a mnemonic being more than English.

- the sentence is NFKD-normalized before it is looked up, hashed or
  stretched, and so is the passphrase. That is what BIP39 asks for and
  what `trezor/python-mnemonic` does; a Spanish sentence typed with
  precomposed accents and the same sentence decomposed are one mnemonic
  and one seed
- a japanese mnemonic is joined with the ideographic space U+3000, as the
  reference implementation joins it. NFKD maps that space to a plain one,
  so the seed is the same either way; the sentence is not
- the language need not be given: `lang_from_mnemonic` reads it off the
  words, which is what makes `seed_from_mnemonic` work for a mnemonic
  that is not English

Translating a mnemonic from one word-list to another is *not* here, and
BIP39 says why in its own Shortcomings section: the seed is stretched
from the sentence rather than from the entropy it encodes, so the
translated sentence is a valid mnemonic of a different wallet. What the
entropy round trip below expresses -- read in one language, write in
another -- is a re-spelling of the entropy and nothing more.
"""

from __future__ import annotations

import secrets
import unicodedata
from hashlib import pbkdf2_hmac, sha256

from bip39_slip39._utils import assert_type, utf8_bytes
from bip39_slip39.entropy import (
    BinStr,
    Entropy,
    _bin_str_entropy_from_entropy,
    _bin_str_entropy_from_wordlist_indexes,
    _bytes_entropy_from_str,
    _wordlist_indexes_from_bin_str_entropy,
)
from bip39_slip39.exceptions import BTClibMnemonicsValueError
from bip39_slip39.mnemonic import (
    WORDLISTS,
    Mnemonic,
    WordList,
    _indexes_in,
    _mnemonic_in,
    normalize_mnemonic,
)

__all__ = [
    "entropy_from_mnemonic",
    "is_valid_mnemonic",
    "lang_from_mnemonic",
    "mnemonic_from_entropy",
    "seed_from_mnemonic",
]

# the reference implementation joins a japanese mnemonic with the
# ideographic space and every other one with a plain space, and its
# vectors are written that way. Not a property of the word-list, which is
# why it is not in mnemonic.py: electrum reads the same japanese
# word-list and joins it with a plain space
_SEPARATORS = {"ja": "\u3000"}

# BIP39 is eleven bits to a word, and so 2048 words to a list: "the
# wordlist contains 2048 words" is the specification, not a property of
# the english list. WORDLISTS holds every BIP39 and SLIP-0039 list this
# package ships, slip39's 1024 words among them, so the length has to be
# asked for rather than assumed
_BIP39_WORDLIST_LENGTH = 1 << 11

# the entropy sizes of the table above, and the words they make
_ENTROPY_BITS = 128, 160, 192, 224, 256
_WORD_COUNTS = tuple((n + n // 32) // 11 for n in _ENTROPY_BITS)


def _base(wordlist: WordList) -> int:
    """Return the length of a word-list, which BIP39 requires to be 2048.

    WORDLISTS.load_lang already refuses a length that is not a power of
    two, and that is the weaker test: a 1024-word list passes it and then
    encodes ten bits to a word, so the sentence it builds is a base-1024
    number no BIP39 wallet reads and the checksum it verifies is over the
    wrong bits. The registry is shared and by design -- slip39 is
    registered on it under a key of its own -- so refusing here is what
    keeps `lang="slip39"` from being a silent wrong answer instead of an
    error.
    """
    base = len(wordlist)
    if base != _BIP39_WORDLIST_LENGTH:
        err_msg = f"invalid bip39 wordlist length: {base}; "
        err_msg += f"expected: {_BIP39_WORDLIST_LENGTH}"
        raise BTClibMnemonicsValueError(err_msg)
    return base


def _assert_word_count(n_words: int) -> None:
    """Refuse a sentence of a length BIP39 has no mnemonic for.

    It is asked before the sentence is decoded, whose cost grows with the
    square of the words.
    """
    if n_words not in _WORD_COUNTS:
        err_msg = f"invalid mnemonic length: {n_words} words, "
        err_msg += f"not in {list(_WORD_COUNTS)}"
        raise BTClibMnemonicsValueError(err_msg)


def _entropy_checksum(entropy: Entropy) -> tuple[BinStr, BinStr]:
    """Return the checksum of the binary string input entropy.

    Entropy must be expressed as binary 0/1 string and must be 128, 160,
    192, 224, or 256 bits. Leading zeros are considered genuine entropy,
    not redundant padding.
    """
    bin_str_entropy = _bin_str_entropy_from_entropy(entropy, _ENTROPY_BITS)
    bytes_entropy = _bytes_entropy_from_str(bin_str_entropy)

    # 256-bit checksum
    bytes_checksum = sha256(bytes_entropy).digest()
    # integer checksum (leading zeros are lost)
    int_checksum = int.from_bytes(bytes_checksum, byteorder="big", signed=False)
    # convert checksum to binary '01' string
    checksum = f"{int_checksum:b}"
    checksum = checksum.zfill(256)  # pad with leading lost zeros
    # leftmost bits
    checksum_bits = len(bytes_entropy) // 4
    return bin_str_entropy, checksum[:checksum_bits]


def mnemonic_from_entropy(entropy: Entropy | None = None, lang: str = "en") -> Mnemonic:
    """Convert input entropy to BIP39 checksummed mnemonic sentence.

    Input entropy can be expressed as binary 0/1 string, bytes-like, or
    integer; it must be 128, 160, 192, 224, or 256 bits.

    In the case of binary 0/1 string and bytes-like, leading zeros are
    not considered redundant padding.

    In the case of integer, where leading zeros cannot be represented,
    if the bit length is not an allowed value, then the binary 0/1
    string is padded with leading zeros up to the next allowed bit
    length.

    Entropy longer than 256 bits is refused.
    """
    # not `not entropy`: entropy can be an int, and int 0 is a value to
    # convert, not a missing one -- only the empty *string* means that
    if entropy is None or entropy == "":
        entropy = secrets.randbits(128)
    bin_str_entropy, checksum = _entropy_checksum(entropy)
    # read once: the base and the words of one load, were the language
    # replaced meanwhile
    record = WORDLISTS._record(lang)
    base = _base(record.words)
    indexes = _wordlist_indexes_from_bin_str_entropy(bin_str_entropy + checksum, base)
    return _mnemonic_in(record, indexes, _SEPARATORS.get(lang, " "))


def _candidate_langs(mnemonic: Mnemonic) -> list[str]:
    """Return the BIP39 word-lists that hold every word of the sentence."""
    # the registry is shared with slip39, so the candidates are filtered by
    # _BIP39_WORDLIST_LENGTH: slip39's list is 1024 words, and a sentence
    # written from it is not a BIP39 mnemonic in a language nobody named --
    # it is not a BIP39 mnemonic at all
    return WORDLISTS._langs_of(mnemonic.split(), _BIP39_WORDLIST_LENGTH)


def lang_from_mnemonic(mnemonic: Mnemonic) -> str:
    """Return the language of the BIP39 mnemonic sentence.

    The word-lists that hold every word of the sentence are the
    candidates, and where there is more than one the checksum decides.
    Both steps are needed, and neither settles every sentence.

    Simplified and Traditional Chinese share 1275 of their 2048 words, so
    a Chinese sentence is in both about once in three hundred; english and
    french share a hundred words, which is the same thing far less often.
    The two Chinese lists are aligned, a shared word sitting at the same
    index in each, so an ambiguous chinese sentence usually spells the
    *same* entropy either way -- the checksum then rules nothing out, and
    the first candidate is returned because the two are indistinguishable
    and not because one was picked over the other.

    What is refused is the sentence that is valid in two languages and
    spells a different entropy in each: there the language is a question
    only the caller can answer. A sentence that is valid in none is not
    that case, and the first candidate is returned so that the caller
    hears about the checksum, which is what is actually wrong with it.

    Prefixes are not accepted, unlike `trezor/python-mnemonic`'s
    `detect_language`: there is no `expand` here, so a four-letter prefix is
    not a word anywhere else in this module either.
    """
    assert_type(mnemonic, str, "mnemonic")
    candidates = _candidate_langs(mnemonic)
    if not candidates:
        # never the sentence itself: a mnemonic one typo away from being
        # valid is one typo away from being recovered, and an exception
        # message ends up in logs and crash reports
        n_words = len(mnemonic.split())
        raise BTClibMnemonicsValueError(
            f"unknown language for mnemonic: {n_words} words"
        )
    if len(candidates) == 1:
        return candidates[0]

    valid = [lang for lang in candidates if is_valid_mnemonic(mnemonic, lang)]
    if len(valid) != 1:
        entropies = {entropy_from_mnemonic(mnemonic, lang) for lang in valid}
        if len(entropies) > 1:
            err_msg = f"ambiguous language for mnemonic: {valid}"
            raise BTClibMnemonicsValueError(err_msg)
        return (valid or candidates)[0]
    return valid[0]


def is_valid_mnemonic(mnemonic: Mnemonic, lang: str | None = None) -> bool:
    """Return whether the sentence is a valid BIP39 mnemonic.

    Valid is what `entropy_from_mnemonic` accepts: a word count BIP39
    has a mnemonic for, every word in the word-list, and the checksum.
    Any string is answered, with `False` for one that is not valid, so
    there is no exception to catch; a `mnemonic` or `lang` of another
    type is the caller's mistake and leaves as a
    `BTClibMnemonicsTypeError`, as everywhere in this package.

    The language is read off the words if it is not provided, and the
    sentence is valid if it is in *any* word-list that holds its words.
    That is where this differs from `entropy_from_mnemonic`, which
    refuses a sentence valid in two languages with a different entropy
    in each as ambiguous: such a sentence is a valid mnemonic, and the
    ambiguity is only about which entropy it spells. For such a sentence
    `seed_from_mnemonic` with `verify_checksum=True` still raises
    "ambiguous language", as it takes no `lang`; `verify_checksum=False`
    avoids it.

    A `lang` that names no BIP39 word-list -- a typo, a language that
    was never registered, or `"slip39"`, whose list is not 2048 words --
    answers `False`: no sentence is a mnemonic of a language that does
    not exist, and CONTRIBUTING.md's *The public surface* makes an
    `is_*` total over the declared types, `lang` being a `str`. The
    cost is that a misspelled `lang` reads as an invalid sentence;
    `entropy_from_mnemonic` is the function that refuses it.
    """
    assert_type(lang, (str, type(None)), "lang")
    mnemonic = normalize_mnemonic(mnemonic)
    if len(mnemonic.split()) not in _WORD_COUNTS:
        return False
    # an empty lang is no language, as entropy_from_mnemonic reads it
    langs = [lang] if lang else _candidate_langs(mnemonic)
    for candidate in langs:
        try:
            entropy_from_mnemonic(mnemonic, candidate)
        except BTClibMnemonicsValueError:
            continue
        return True
    return False


def entropy_from_mnemonic(mnemonic: Mnemonic, lang: str | None = None) -> BinStr:
    """Return the entropy from the BIP39 checksummed mnemonic sentence.

    The language is read off the words if it is not provided.

    The sentence is normalized first, so that the word looked up in the
    word-list is the NFKD one the word-list holds: a mnemonic typed on a
    japanese IME arrives in fullwidth latin, and U+FF41 is not "a" until
    it is decomposed. The language is read off the normalized sentence
    for the same reason.
    """
    mnemonic = normalize_mnemonic(mnemonic)
    _assert_word_count(len(mnemonic.split()))
    lang = lang or lang_from_mnemonic(mnemonic)
    # read once: the base and the positions of one load
    record = WORDLISTS._record(lang)
    base = _base(record.words)
    indexes = _indexes_in(record, mnemonic, lang)
    cs_entropy = _bin_str_entropy_from_wordlist_indexes(indexes, base)

    bits = int(len(cs_entropy) * 32 / 33)
    # entropy is only the first part of cs_entropy
    # the second part being the checksum, to be verified
    bin_str_entropy, checksum = _entropy_checksum(cs_entropy[:bits])
    if cs_entropy[bits:] != checksum:
        # neither checksum is quoted: each is bits of the entropy, or of
        # its hash, and an exception message ends up in logs
        raise BTClibMnemonicsValueError(f"invalid checksum: {len(indexes)} words")

    return bin_str_entropy


def seed_from_mnemonic(
    mnemonic: Mnemonic, passphrase: str, verify_checksum: bool = True
) -> bytes:
    """Return the seed from the provided BIP39 mnemonic sentence.

    The mnemonic checksum verification can be skipped if needed.

    Both the sentence and the passphrase are normalized NFKD, which is
    what BIP39 stretches: "a mnemonic sentence (in UTF-8 NFKD) used as
    the password and the string 'mnemonic' + passphrase (again in UTF-8
    NFKD) used as the salt". Without it the twenty-four japanese vectors
    are twenty-four wrong seeds, and every english one still passes --
    "TREZOR" and the english word-list being ASCII, which is NFKD
    already. The two spellings of an accented word are one mnemonic for
    the same reason, and the ideographic space a japanese sentence is
    written with decomposes to a plain one, so the seed does not depend
    on which of the two joined the words.

    The whitespace collapse on top of that is this package's and not the
    reference implementation's, and it is why a sentence with a doubled
    space stretches to the seed of the sentence without it;
    normalize_mnemonic says why it is worth the difference.
    """
    mnemonic = normalize_mnemonic(mnemonic)
    assert_type(passphrase, str, "passphrase")

    if verify_checksum:
        entropy_from_mnemonic(mnemonic)

    # the passphrase is decomposed and otherwise left alone: its
    # whitespace is content the user chose, not a separator between
    # words, so collapsing a doubled space there would stretch a
    # passphrase nobody typed and lose the wallet it opens
    passphrase = unicodedata.normalize("NFKD", passphrase)

    hf_name = "sha512"
    password = utf8_bytes(mnemonic, "mnemonic")
    salt = utf8_bytes(f"mnemonic{passphrase}", "passphrase")
    iterations = 2048
    dksize = 64
    return pbkdf2_hmac(hf_name, password, salt, iterations, dksize)
