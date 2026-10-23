# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""What a refusal of `bip39_slip39` says, and what it does not.

A wrong type leaves as a `BTClibMnemonicsTypeError` naming the
parameter, not as a builtin raised from underneath the package (issue
btclib-org/btclib-wallet#134) nor as a value refusal (issue
btclib-org/btclib-wallet#136): these are the calls
`tests/input_validation_test.py`'s walk does not reach, each taking a
plain `str`, `int` or sequence of them, or being a method. And no
refusal quotes secret material -- a word of the sentence, a checksum, a
padding bit, a hash prefix -- because an exception message ends up in
logs and crash reports (issues btclib-org/btclib-wallet#135 and
btclib-org/btclib-wallet#137).
"""

from __future__ import annotations

from base64 import b64encode
from collections.abc import Callable
from hashlib import sha256
from pathlib import Path
from types import MappingProxyType
from typing import Any

import pytest

from bip39_slip39 import bip39, dispatch, electrum, entropy, mnemonic, slip39
from bip39_slip39.exceptions import (
    BTClibMnemonicsTypeError,
    BTClibMnemonicsValueError,
)
from tests import load
from tests.secret_free import assert_secret_free

_ABOUT = "abandon " * 11 + "about"
_ABOUT_WORDS = _ABOUT.split()
# a fixed random entropy, as a bit string
_ENTROPY_BITS = "11111101110000101001000101010110101101011100111001001001000100100100001100000100101100101101100001100001101001001010010100101111"


def _spellings_of(secret: bytes) -> list[str | bytes]:
    """Return what a refusal could print of a secret held as bytes."""
    number = int.from_bytes(secret, "big")
    return [
        secret,
        secret.hex(),
        format(number, f"0{8 * len(secret)}b"),
        str(number),
        b64encode(secret).decode(),
    ]


_ENTROPY_SPELLINGS = _spellings_of(int(_ENTROPY_BITS, 2).to_bytes(16, "big"))
# digits a wrong-type row feeds in a secret's place: an index list as a str,
# a hex seed as an int
_WRONGLY_TYPED = ["1", "12"]


class _BytesPath:
    """A path object whose path is bytes, which no word-list is named by."""

    def __fspath__(self) -> bytes:
        """Return the path, as bytes."""
        return b"english.txt"


# issue btclib-org/btclib-wallet#134's table, one row per call, and what
# the refusal names
_WRONG_TYPES: list[tuple[str, Callable[[], Any], str]] = [
    (
        "bip39.seed_from_mnemonic",
        lambda: bip39.seed_from_mnemonic(_ABOUT, b""),  # type: ignore[arg-type]
        "invalid passphrase type: bytes",
    ),
    (
        "electrum.old_mnemonic_from_hex_seed",
        lambda: electrum.old_mnemonic_from_hex_seed(1),  # type: ignore[arg-type]
        "invalid hex_seed type: int",
    ),
    (
        "mnemonic.data_file",
        lambda: mnemonic.data_file(1),  # type: ignore[arg-type]
        "invalid filename type: int",
    ),
    (
        "mnemonic.mnemonic_from_indexes",
        lambda: mnemonic.mnemonic_from_indexes(1, "en"),  # type: ignore[arg-type]
        "invalid indexes type: int",
    ),
    (
        "mnemonic.WORDLISTS.index",
        lambda: mnemonic.WORDLISTS.index(1, "en"),  # type: ignore[arg-type]
        "invalid word type: int",
    ),
    (
        "mnemonic.WORDLISTS.langs_of_words",
        lambda: mnemonic.WORDLISTS.langs_of_words(1),  # type: ignore[arg-type]
        "invalid words type: int",
    ),
    # issue btclib-org/btclib-wallet#136: a lang reaches
    # WordLists.load_lang from every function taking one, which unchecked
    # would refuse it as a missing language file
    (
        "bip39.entropy_from_mnemonic(lang=int)",
        lambda: bip39.entropy_from_mnemonic(_ABOUT, 1),  # type: ignore[arg-type]
        "invalid lang type: int",
    ),
    (
        "mnemonic.indexes_from_mnemonic(lang=None)",
        lambda: mnemonic.indexes_from_mnemonic(_ABOUT, None),  # type: ignore[arg-type]
        "invalid lang type: NoneType",
    ),
    (
        "bip39.mnemonic_from_entropy(lang=int)",
        lambda: bip39.mnemonic_from_entropy(_ENTROPY_BITS, 1),  # type: ignore[arg-type]
        "invalid lang type: int",
    ),
    (
        "mnemonic.WORDLISTS.load_lang(filename=int)",
        lambda: mnemonic.WordLists().load_lang("xx", 1),  # type: ignore[arg-type]
        "invalid filename type: int",
    ),
    (
        "mnemonic.data_file(bytes path)",
        lambda: mnemonic.data_file(_BytesPath()),  # type: ignore[arg-type]
        "invalid filename type: bytes",
    ),
    # dispatch answers "" for a sentence no scheme claims, which is a fact
    # about the sentence; a lang of another type is the caller's mistake
    (
        "dispatch.seed_type_from_mnemonic(lang=int)",
        lambda: dispatch.seed_type_from_mnemonic(_ABOUT, 1),  # type: ignore[arg-type]
        "invalid lang type: int",
    ),
    (
        "dispatch.all_seed_types_from_mnemonic(lang=None)",
        lambda: dispatch.all_seed_types_from_mnemonic(_ABOUT, None),  # type: ignore[arg-type]
        "invalid lang type: NoneType",
    ),
    (
        "entropy.bin_str_entropy_from_random",
        lambda: entropy.bin_str_entropy_from_random("x"),  # type: ignore[arg-type]
        "invalid bits type: str",
    ),
    # the shapes around those rows: a lone str where its words go, an
    # element of the wrong type, and a bool where an index goes
    (
        "mnemonic.WORDLISTS.langs_of_words(str)",
        lambda: mnemonic.WORDLISTS.langs_of_words("abandon"),
        "invalid words type: str",
    ),
    (
        "mnemonic.WORDLISTS.langs_of_words([int])",
        lambda: mnemonic.WORDLISTS.langs_of_words([1]),  # type: ignore[list-item]
        "invalid word type: int",
    ),
    (
        "mnemonic.mnemonic_from_indexes(str)",
        lambda: mnemonic.mnemonic_from_indexes("12", "en"),  # type: ignore[arg-type]
        "invalid indexes type: str",
    ),
    (
        "mnemonic.mnemonic_from_indexes([bool])",
        lambda: mnemonic.mnemonic_from_indexes([True], "en"),
        "invalid index type: bool",
    ),
]


@pytest.mark.parametrize(
    "call, err_msg", [row[1:] for row in _WRONG_TYPES], ids=[r[0] for r in _WRONG_TYPES]
)
def test_a_wrong_type_is_the_packages_refusal(
    call: Callable[[], Any], err_msg: str
) -> None:
    """A `BTClibMnemonicsTypeError` naming the parameter, and no builtin."""
    with pytest.raises(BTClibMnemonicsTypeError, match=f"^{err_msg}$") as excinfo:
        call()
    assert_secret_free(
        excinfo.value, [*_ABOUT_WORDS, *_ENTROPY_SPELLINGS, *_WRONGLY_TYPED]
    )


def test_the_type_checks_let_the_right_types_through() -> None:
    """The same calls with the types they declare, which still answer."""
    assert len(bip39.seed_from_mnemonic(_ABOUT, "")) == 64
    words = electrum.old_mnemonic_from_hex_seed("00" * 16).split()
    assert len(words) == 12
    assert mnemonic.data_file("english.txt").endswith("english.txt")
    # a path object names a file as well as its str does, so it is taken
    assert mnemonic.data_file(Path("english.txt")) == mnemonic.data_file("english.txt")
    word_lists = mnemonic.WordLists()
    word_lists.load_lang("xx", Path(mnemonic.data_file("english.txt")))
    assert word_lists.language_files["xx"] == mnemonic.data_file("english.txt")
    assert dispatch.seed_type_from_mnemonic(_ABOUT, "en") == "bip39"
    assert mnemonic.mnemonic_from_indexes((0, 2047), "en") == "abandon zoo"
    assert mnemonic.WORDLISTS.index("zoo", "en") == 2047
    assert "en" in mnemonic.WORDLISTS.langs_of_words(["abandon", "zoo"])
    assert len(entropy.bin_str_entropy_from_random(128)) == 128


@pytest.mark.parametrize("index", [-1, 2048], ids=["negative", "past the end"])
def test_an_index_out_of_range_is_refused_by_its_position(index: int) -> None:
    """Refused where it would have read the wrong word, or none.

    A negative index would otherwise read from the end of the list, and
    the value is not quoted, being a digit of the secret: the anchored
    pattern is the whole message, so it holds no number but the position
    and the bound.
    """
    indexes = [1337, 1789]
    words = mnemonic.mnemonic_from_indexes(indexes, "en").split()
    err_msg = r"^invalid index at position 3: not in \[0, 2048\)$"
    with pytest.raises(BTClibMnemonicsValueError, match=err_msg) as excinfo:
        mnemonic.mnemonic_from_indexes([*indexes, index], "en")
    # 2048 is a bound the message states, so it is not listed; -1 is
    secrets = [*map(str, indexes), *words, *(["-1"] if index < 0 else [])]
    assert_secret_free(excinfo.value, secrets)


@pytest.mark.parametrize("index", [-7391, 9137], ids=["negative", "past the end"])
def test_an_index_out_of_range_is_not_quoted(index: int) -> None:
    """Neither the index refused, nor the ones before it, nor their words."""
    indexes = [1337, 1789]
    words = mnemonic.mnemonic_from_indexes(indexes, "en").split()
    err_msg = r"^invalid index at position 3: not in \[0, 2048\)$"
    with pytest.raises(BTClibMnemonicsValueError, match=err_msg) as excinfo:
        mnemonic.mnemonic_from_indexes([*indexes, index], "en")
    secrets = [
        str(abs(index)),
        format(abs(index), "x"),
        *map(str, indexes),
        *(format(i, "x") for i in indexes),
        format(abs(index), "b"),
        *(format(i, "b") for i in indexes),
        *words,
    ]
    assert_secret_free(excinfo.value, secrets)


def test_an_unknown_word_is_refused_by_its_position() -> None:
    """The misspelled word is one letter from a word of the secret."""
    # a spanish word and no english one, so the misspelling is a word
    # the spell checker leaves alone
    sentence = _ABOUT.replace("about", "abaco")
    err_msg = "^unknown 'en' word at position 12$"
    for call in (
        lambda: mnemonic.indexes_from_mnemonic(sentence, "en"),
        lambda: bip39.entropy_from_mnemonic(sentence, "en"),
    ):
        with pytest.raises(BTClibMnemonicsValueError, match=err_msg) as excinfo:
            call()
        assert_secret_free(excinfo.value, [sentence, *sentence.split()])
        # the word-list's own refusal is not left chained behind it
        assert excinfo.value.__context__ is None


def test_an_unknown_language_is_refused_as_itself() -> None:
    """Not as an unknown word, which the per-word loop would call it."""
    with pytest.raises(
        BTClibMnemonicsValueError, match="^Missing file for an unknown language$"
    ) as excinfo:
        mnemonic.indexes_from_mnemonic(_ABOUT, "xx")
    assert_secret_free(excinfo.value, _ABOUT_WORDS)


def test_a_bip39_checksum_refusal_quotes_no_checksum() -> None:
    """Both checksums are bits of the entropy or of its hash."""
    entropy_hex = "1f5c8d2a9be0473c6a81d5f2e9047b3c"
    entropy = bytes.fromhex(entropy_hex)
    sentence = bip39.mnemonic_from_entropy(entropy, "en")
    indexes = mnemonic.indexes_from_mnemonic(sentence, "en")
    # the last index holds four bits of checksum: flip one of them
    flipped = [*indexes[:-1], indexes[-1] ^ 1]
    broken = mnemonic.mnemonic_from_indexes(flipped, "en")
    with pytest.raises(
        BTClibMnemonicsValueError, match="^invalid checksum: 12 words$"
    ) as excinfo:
        bip39.entropy_from_mnemonic(broken, "en")
    digest = sha256(entropy).digest()
    secrets: list[str | bytes] = [
        *sentence.split(),
        *broken.split(),
        *_spellings_of(entropy),
        *_spellings_of(digest),
        format(digest[0] >> 4, "04b"),
        format((digest[0] >> 4) ^ 1, "04b"),
        *(str(i) for i in (indexes, flipped)),
        *(" ".join(map(str, i)) for i in (indexes, flipped)),
        *(",".join(map(str, i)) for i in (indexes, flipped)),
        *map(str, indexes),
        *map(str, flipped),
    ]
    assert_secret_free(excinfo.value, secrets)
    # four bits are too few to tell from other text, so the refusal is
    # pinned exactly
    e = excinfo.value
    message = ("invalid checksum: 12 words",)
    assert (e.args, vars(e), e.__cause__, e.__context__) == (message, {}, None, None)


def test_a_slip39_padding_refusal_quotes_no_bit() -> None:
    """The padding bits are bits of the share."""
    vectors = load("_data", "vectors.json")
    ((share,),) = [v[1] for v in vectors if "invalid padding (128 bits)" in v[0]]
    with pytest.raises(
        BTClibMnemonicsValueError, match="^invalid padding: must be all zeros$"
    ) as excinfo:
        slip39.share_from_mnemonic(share)
    idx = slip39._indexes_from_mnemonic(share)
    bits = "".join(format(i, "010b") for i in idx)
    value_bits = bits[slip39._HEADER_BITS : len(bits) - slip39._CHECKSUM_BITS]
    value = int(value_bits, 2)
    padding = len(value_bits) % 16
    secrets: list[str | bytes] = [
        share,
        *share.split(),
        bits,
        value_bits,
        hex(value),
        format(value, "x"),
        value.to_bytes((len(value_bits) + 7) // 8, "big"),
        str(int(value_bits[padding:], 2)),
        str(idx),
        " ".join(map(str, idx)),
        ",".join(map(str, idx)),
        *map(str, idx),
    ]
    assert_secret_free(excinfo.value, secrets)
    # two bits are too few to tell from other text, so the refusal is
    # pinned exactly
    e = excinfo.value
    message = ("invalid padding: must be all zeros",)
    assert (e.args, vars(e), e.__cause__, e.__context__) == (message, {}, None, None)


def test_an_unknown_electrum_version_quotes_no_hash_prefix() -> None:
    """For a sentence that is no electrum one, the prefix is a secret's hash."""
    version = electrum._seed_version(_ABOUT)
    prefix = version[:3]
    with pytest.raises(
        BTClibMnemonicsValueError, match="^unknown electrum mnemonic version; "
    ) as excinfo:
        electrum.version_from_mnemonic(_ABOUT)
    assert_secret_free(
        excinfo.value,
        [*_spellings_of(bytes.fromhex(version)), version[:2], prefix, *_ABOUT_WORDS],
    )


# a secret in the position of a language or of a version: the entropy
# of electrum.mnemonic_from_entropy's first parameter, the sentence of
# bip39.entropy_from_mnemonic's second
_SECRET_IN_THE_WRONG_PLACE: list[tuple[str, Callable[[str], Any]]] = [
    ("electrum.mnemonic_from_entropy", electrum.mnemonic_from_entropy),
    ("bip39.entropy_from_mnemonic", lambda s: bip39.entropy_from_mnemonic("en", s)),
    (
        "bip39.mnemonic_from_entropy",
        lambda s: bip39.mnemonic_from_entropy(_ENTROPY_BITS, s),
    ),
    (
        "mnemonic.indexes_from_mnemonic",
        lambda s: mnemonic.indexes_from_mnemonic("en", s),
    ),
    (
        "mnemonic.mnemonic_from_indexes",
        lambda s: mnemonic.mnemonic_from_indexes([0], s),
    ),
]


@pytest.mark.parametrize(
    "name, call",
    _SECRET_IN_THE_WRONG_PLACE,
    ids=[n for n, _ in _SECRET_IN_THE_WRONG_PLACE],
)
def test_a_secret_in_the_place_of_a_name_is_not_repeated(
    name: str, call: Callable[[str], Any]
) -> None:
    """The refusal of an unknown language or version quotes neither."""
    leaked = "zebra7f7f7f7f7f7f"
    with pytest.raises(BTClibMnemonicsValueError) as excinfo:
        call(leaked)
    secrets = [leaked, leaked.encode(), leaked.encode().hex(), *_ENTROPY_SPELLINGS]
    assert_secret_free(excinfo.value, secrets)


def test_a_word_list_file_that_cannot_be_read_is_a_value_error(
    tmp_path: Path,
) -> None:
    """A file that is missing, a directory, a NUL in a name, or no UTF-8."""
    not_utf8 = tmp_path / "not_utf8.txt"
    not_utf8.write_bytes(b"\xff\xfe")
    cases = {
        str(tmp_path / "missing.txt"): "^cannot read wordlist file: FileNotFoundError$",
        str(tmp_path): "^cannot read wordlist file: [A-Za-z]*Error$",
        "a\0b": "^cannot read wordlist file: ValueError$",
        str(not_utf8): "^invalid wordlist file: not UTF-8$",
    }
    for filename, err_msg in cases.items():
        with pytest.raises(BTClibMnemonicsValueError, match=err_msg) as excinfo:
            mnemonic.WordLists().load_lang("xx", filename)
        assert filename not in str(excinfo.value)
        assert excinfo.value.__suppress_context__
        assert "xx" not in mnemonic.WordLists().languages


def test_the_word_lists_constructor_validates_its_arguments() -> None:
    """The language files are a dict of file names, named by str."""
    for bad in ("abc", 5, [("xx", "x.txt")]):
        with pytest.raises(BTClibMnemonicsTypeError, match="^invalid language_files"):
            mnemonic.WordLists(bad)  # type: ignore[arg-type]
    with pytest.raises(BTClibMnemonicsTypeError, match="^invalid language type: int$"):
        mnemonic.WordLists({1: "x.txt"})  # type: ignore[dict-item]
    with pytest.raises(BTClibMnemonicsTypeError, match="^invalid filename type: int$"):
        mnemonic.WordLists({"xx": 5})  # type: ignore[dict-item]
    # a path object names a file as well as its str does
    word_lists = mnemonic.WordLists({"en": Path(mnemonic.data_file("english.txt"))})
    assert word_lists.language_length("en") == 2048
    # and so does any mapping
    files = MappingProxyType({"en": mnemonic.data_file("english.txt")})
    assert mnemonic.WordLists(files).language_length("en") == 2048


def test_the_wordlists_argument_is_validated() -> None:
    """Both functions taking one refuse what is no `WordLists`."""
    with pytest.raises(
        BTClibMnemonicsTypeError, match="^invalid wordlists type: int$"
    ) as excinfo:
        mnemonic.indexes_from_mnemonic("abandon", "en", 5)  # type: ignore[arg-type]
    assert_secret_free(excinfo.value, ["abandon"])
    with pytest.raises(
        BTClibMnemonicsTypeError, match="^invalid wordlists type: dict$"
    ) as excinfo:
        mnemonic.mnemonic_from_indexes([1337, 1789], "en", {})  # type: ignore[arg-type]
    words = mnemonic.mnemonic_from_indexes([1337, 1789], "en").split()
    assert_secret_free(excinfo.value, ["1337", "1789", *words])


_LONE = "\udcff"
_ELECTRUM = electrum.mnemonic_from_entropy("standard", "0" * 128)

_LONE_SURROGATES: list[tuple[str, Callable[[], Any]]] = [
    ("mnemonic", lambda: electrum.version_from_mnemonic(_ABOUT + _LONE)),
    ("mnemonic", lambda: electrum.entropy_from_mnemonic(_ABOUT + _LONE)),
    ("mnemonic", lambda: electrum.seed_from_mnemonic(_ELECTRUM + _LONE, "")),
    (
        "mnemonic",
        lambda: bip39.seed_from_mnemonic(_ABOUT + _LONE, "", verify_checksum=False),
    ),
    ("passphrase", lambda: bip39.seed_from_mnemonic(_ABOUT, "pw" + _LONE)),
    ("passphrase", lambda: electrum.seed_from_mnemonic(_ELECTRUM, "pw" + _LONE)),
]


@pytest.mark.parametrize("what, call", _LONE_SURROGATES)
def test_a_lone_surrogate_is_refused_as_a_value_error(
    what: str, call: Callable[[], Any]
) -> None:
    """In a mnemonic or a passphrase, with no UnicodeEncodeError behind it."""
    with pytest.raises(
        BTClibMnemonicsValueError, match=f"^invalid {what}: contains a lone surrogate$"
    ) as excinfo:
        call()
    assert excinfo.value.__context__ is None
    assert excinfo.value.__cause__ is None
    shown = repr(excinfo.value)
    assert "udcff" not in shown
    assert "abandon" not in shown
    assert "pw" not in shown
    secrets = [
        *_ABOUT_WORDS,
        *_ELECTRUM.split(),
        "pw",
        _LONE,
        ascii(_LONE)[1:-1],
    ]
    assert_secret_free(excinfo.value, secrets)


def test_dispatch_answers_a_lone_surrogate() -> None:
    """A sentence no scheme reads is answered with "", not refused."""
    assert dispatch.seed_type_from_mnemonic(_ABOUT + _LONE) == ""
