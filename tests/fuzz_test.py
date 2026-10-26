# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Every decoder, on input nobody wrote down.

The rest of the suite is fixed vectors: exactly what conformance needs,
and blind to the malformed sentences that never make it into a
specification's test section. This file is the converse. It does not
assert that a decoder accepts the right things -- the vectors do that --
but that it *fails the way the package says it fails*, whatever it is
handed: an IndexError off a short slice or a KeyError off a word-list
lookup reaches a caller who catches `Bip39Slip39ValueError` to reject
bad input and has no reason to expect anything else.

`fuzz/`'s atheris harness asks the same question of the same decoders
for an hour a week; this asks it on every run, for as long as hypothesis
spends on a test. Arbitrary text rarely spells a word, so the sentences
below are also drawn from the word-lists themselves, which is what
reaches the checksum, the padding and the header fields behind the
lookup.
"""

from __future__ import annotations

import contextlib
import random
import re
from collections.abc import Callable
from functools import partial
from typing import Any, NamedTuple

import pytest
from hypothesis import example, given
from hypothesis import strategies as st

from bip39_slip39 import bip39, dispatch, electrum, slip39
from bip39_slip39.exceptions import (
    Bip39Slip39TypeError,
    Bip39Slip39ValueError,
)
from bip39_slip39.mnemonic import WORDLISTS, indexes_from_mnemonic

# what a decoder of this package is allowed to raise. Anything else
# leaves the contract src/bip39_slip39/exceptions.py documents
CONTRACT = (Bip39Slip39ValueError, Bip39Slip39TypeError)

DECODERS: dict[str, Callable[[str], Any]] = {
    "bip39.entropy_from_mnemonic": bip39.entropy_from_mnemonic,
    "bip39.lang_from_mnemonic": bip39.lang_from_mnemonic,
    "electrum.version_from_mnemonic": electrum.version_from_mnemonic,
    "electrum.entropy_from_mnemonic": electrum.entropy_from_mnemonic,
    "electrum.lang_from_mnemonic": electrum.lang_from_mnemonic,
    "electrum.hex_seed_from_old_mnemonic": electrum.hex_seed_from_old_mnemonic,
    "slip39.share_from_mnemonic": slip39.share_from_mnemonic,
    "bip39.seed_from_mnemonic": lambda s: bip39.seed_from_mnemonic(s, ""),
    "electrum.seed_from_mnemonic": lambda s: electrum.seed_from_mnemonic(s, ""),
    "electrum.old_master_prv_key_from_mnemonic": (
        electrum.old_master_prv_key_from_mnemonic
    ),
    "mnemonic.indexes_from_mnemonic": lambda s: indexes_from_mnemonic(s, "en"),
    # one share per line
    "slip39.master_secret_from_mnemonics": (
        lambda s: slip39.master_secret_from_mnemonics(s.split("\n"))
    ),
    "slip39.encrypted_master_secret_from_mnemonics": (
        lambda s: slip39.encrypted_master_secret_from_mnemonics(s.split("\n"))
    ),
}


def _sentences(lang: str, min_size: int, max_size: int) -> st.SearchStrategy[str]:
    """Return a strategy for sentences of words from one word-list."""
    words = st.sampled_from(list(WORDLISTS.wordlist(lang)))
    return st.lists(words, min_size=min_size, max_size=max_size).map(" ".join)


def _read(decoder: Callable[[str], Any], sentence: str) -> None:
    with contextlib.suppress(*CONTRACT):
        decoder(sentence)


@pytest.mark.parametrize("name", DECODERS)
@given(text=st.text(max_size=256))
def test_a_decoder_refuses_text_within_the_contract(name: str, text: str) -> None:
    """Arbitrary text is read, or refused as the package's own exception."""
    _read(DECODERS[name], text)


@pytest.mark.parametrize("name", DECODERS)
@given(sentence=_sentences("en", 0, 25))
def test_a_decoder_refuses_english_words_within_the_contract(
    name: str, sentence: str
) -> None:
    """Sentences of BIP39 words reach the checksum and the version."""
    _read(DECODERS[name], sentence)


@given(sentence=_sentences("slip39", 0, 40))
def test_a_share_is_read_within_the_contract(sentence: str) -> None:
    """Sentences of SLIP-0039 words reach the header and the checksum."""
    _read(slip39.share_from_mnemonic, sentence)


# None, every registered language, and a few that name no word-list. The
# empty string is no language, as for entropy_from_mnemonic
_LANGS = st.sampled_from([None, *WORDLISTS.languages, "", "xx", "EN", "english"])

_SENTENCES = st.one_of(
    st.text(max_size=256),
    _sentences("en", 0, 25),
    # valid ones, which arbitrary words almost never are
    st.tuples(st.binary(min_size=16, max_size=32), st.sampled_from(["en", "fr"])).map(
        lambda t: bip39.mnemonic_from_entropy(t[0][: len(t[0]) // 4 * 4], t[1])
    ),
)


@given(text=_SENTENCES, lang=_LANGS)
# a valid sentence in its own language, which the draws above meet
# only by chance, so that every run reaches entropy_from_mnemonic
@example(text=bip39.mnemonic_from_entropy(bytes(16), "en"), lang="en")
def test_is_valid_mnemonic_answers_every_str(text: str, lang: str | None) -> None:
    """An `is_*` is total: a bool for any str, with nothing suppressed.

    A True is a sentence `entropy_from_mnemonic` accepts as well.
    """
    valid = bip39.is_valid_mnemonic(text, lang)
    assert isinstance(valid, bool)
    if valid and lang:
        bip39.entropy_from_mnemonic(text, lang)


_FIELD = st.integers(min_value=0, max_value=15)
_COUNT = st.integers(min_value=1, max_value=16)
_GROUPS = st.integers(min_value=1, max_value=3)


@st.composite
def _shares(draw: st.DrawFn) -> slip39.Share:
    """Return a share whose every field is within what the format holds."""
    group_count = draw(_COUNT)
    n_bytes = 2 * draw(st.integers(min_value=8, max_value=24))
    return slip39.Share(
        identifier=draw(st.integers(min_value=0, max_value=(1 << 15) - 1)),
        extendable=draw(st.booleans()),
        iteration_exponent=draw(_FIELD),
        group_index=draw(_FIELD),
        group_threshold=draw(st.integers(min_value=1, max_value=group_count)),
        group_count=group_count,
        member_index=draw(_FIELD),
        member_threshold=draw(_COUNT),
        value=draw(st.binary(min_size=n_bytes, max_size=n_bytes)),
    )


@given(share=_shares())
def test_a_share_encodes_and_decodes_back(share: slip39.Share) -> None:
    """The decoder is the encoder's inverse over every field it holds.

    Random words almost never carry a valid checksum, so the round trip
    is driven from the share rather than from the sentence.
    """
    mnemonic = slip39.mnemonic_from_share(share)
    assert slip39.share_from_mnemonic(mnemonic) == share


@given(text=st.text(max_size=128))
def test_dispatch_answers_every_text(text: str) -> None:
    """Dispatch refuses nothing that is a str: it answers "" instead."""
    seed_types = dispatch.all_seed_types_from_mnemonic(text)
    assert dispatch.seed_type_from_mnemonic(text) == (
        seed_types[0] if seed_types else ""
    )


# text with exactly one lone surrogate in it, which is what
# `surrogateescape` decoding of bytes that are no UTF-8 produces and
# `st.text()` never draws. Drawn from a union alphabet the surrogate
# would almost never appear
_SURROGATES = st.tuples(
    st.text(max_size=32),
    st.characters(min_codepoint=0xD800, max_codepoint=0xDFFF),
    st.text(max_size=32),
).map("".join)


@given(text=_SURROGATES, sentence=_sentences("en", 12, 12))
def test_a_lone_surrogate_is_refused_within_the_contract(
    text: str, sentence: str
) -> None:
    """A lone surrogate is a `Bip39Slip39ValueError`, not a codec error."""
    for decoder in DECODERS.values():
        _read(decoder, sentence + " " + text)
    with contextlib.suppress(*CONTRACT):
        bip39.seed_from_mnemonic(sentence + " " + text, "", verify_checksum=False)
    with contextlib.suppress(*CONTRACT):
        bip39.seed_from_mnemonic(sentence, text, verify_checksum=False)
    with contextlib.suppress(*CONTRACT):
        electrum.seed_from_mnemonic(sentence + " " + text, text)
    assert isinstance(dispatch.all_seed_types_from_mnemonic(sentence + text), list)


class _Split(NamedTuple):
    """A master secret and the checksum-valid shares it is split into."""

    secret: bytes
    groups: list[tuple[int, int]]
    group_threshold: int
    mnemonics: list[list[str]]


@st.composite
def _splits(draw: st.DrawFn) -> _Split:
    """Return a master secret split into groups of valid SLIP-0039 shares."""
    n_bytes = 2 * draw(st.integers(min_value=8, max_value=16))
    secret = draw(st.binary(min_size=n_bytes, max_size=n_bytes))
    groups = []
    for _ in range(draw(_GROUPS)):
        member_count = draw(st.integers(min_value=1, max_value=4))
        # a threshold of 1 is only for a group of one
        threshold = draw(
            st.integers(min_value=min(2, member_count), max_value=member_count)
        )
        groups.append((threshold, member_count))
    group_threshold = draw(st.integers(min_value=1, max_value=len(groups)))
    rng = random.Random(draw(st.integers()))
    mnemonics = slip39.mnemonics_from_master_secret(
        secret,
        groups,
        group_threshold,
        iteration_exponent=0,
        entropy_source=rng.randbytes,
    )
    return _Split(secret, groups, group_threshold, mnemonics)


@given(split=_splits(), data=st.data())
def test_recombination_recovers_the_secret(split: _Split, data: st.DataObject) -> None:
    """A threshold of groups, each a threshold of its shares, is the secret.

    Random words almost never carry a valid checksum, so recombination
    is driven from shares a split made.
    """
    chosen = data.draw(
        st.lists(
            st.sampled_from(range(len(split.groups))),
            min_size=split.group_threshold,
            max_size=split.group_threshold,
            unique=True,
        )
    )
    picked = []
    for index in chosen:
        shares = data.draw(st.permutations(split.mnemonics[index]))
        picked += shares[: split.groups[index][0]]
    assert slip39.master_secret_from_mnemonics(picked) == split.secret


@given(
    first=_splits(),
    second=_splits(),
    data=st.data(),
)
def test_recombination_of_valid_shares_stays_within_the_contract(
    first: _Split, second: _Split, data: st.DataObject
) -> None:
    """Valid shares of two splits, in any number and order, stay in contract."""
    pool = [m for split in (first, second) for group in split.mnemonics for m in group]
    chosen = data.draw(st.lists(st.sampled_from(pool), max_size=12))
    with contextlib.suppress(*CONTRACT):
        slip39.master_secret_from_mnemonics(chosen)


def _answer(call: Callable[[], bytes]) -> bytes | str:
    """Return what the call answers, or the message of its refusal."""
    try:
        return call()
    except CONTRACT as e:
        return str(e)


# the whole set's refusal of a set short of shares or of groups: the
# count found, then the threshold
_TOO_FEW = re.compile(
    r"^(\d+) (?:shares in group \d+, member|groups, group) threshold is (\d+)$"
)


_DIGEST = "invalid digest: the shares do not belong together"


def _short(refusal: bytes | str) -> bool:
    """Whether the whole set was refused only for holding too few shares.

    Never asked of an empty set: the recovery takes every first share.
    """
    found = _TOO_FEW.match(refusal) if isinstance(refusal, str) else None
    return found is not None and int(found[1]) < int(found[2])


def _add_and_compare(recovery: slip39.Recovery, mnemonic: str) -> None:
    """Add the mnemonic, then ask the whole set about the shares held.

    Where the recovery is complete, the two answers are equal: the same
    secret, or the same refusal. Where it is not, the two differ in the
    message only: the recovery refuses as incomplete, and the whole set
    is refused for too few shares or groups, or on the digest of a
    complete group holding shares of two splits that share an
    identifier, never for anything else. A refused share makes the
    whole set refused once added to the shares held.
    """
    try:
        recovery.add_mnemonic(mnemonic)
    except CONTRACT:
        held = [slip39.mnemonic_from_share(s) for s in recovery.shares]
        whole = [*held, mnemonic]
        refusal = _answer(partial(slip39.master_secret_from_mnemonics, whole))
        assert isinstance(refusal, str)
    held = [slip39.mnemonic_from_share(s) for s in recovery.shares]
    expected = _answer(partial(slip39.master_secret_from_mnemonics, held))
    answer = _answer(recovery.master_secret)
    if recovery.is_complete:
        assert answer == expected
    else:
        assert answer == "incomplete set of shares"
        assert _short(expected) or expected == _DIGEST, expected


@given(first=_splits(), second=_splits(), data=st.data())
def test_a_recovery_agrees_with_the_whole_set(
    first: _Split, second: _Split, data: st.DataObject
) -> None:
    """Valid shares of two splits, added one at a time, as the whole set.

    `_add_and_compare` says what agreeing means.
    """
    pool = [m for split in (first, second) for group in split.mnemonics for m in group]
    recovery = slip39.Recovery()
    for mnemonic in data.draw(st.lists(st.sampled_from(pool), max_size=12)):
        _add_and_compare(recovery, mnemonic)


def test_a_partial_recovery_of_two_splits_is_refused_on_the_digest() -> None:
    """A group completed from two splits, another group still partial.

    One seed gives both splits one identifier, so every share is taken;
    the whole set is refused on the first group's digest before it
    counts the second group's shares.
    """
    first, second = (
        slip39.mnemonics_from_master_secret(
            secret,
            [(2, 2), (2, 2)],
            2,
            iteration_exponent=0,
            entropy_source=random.Random(0).randbytes,
        )
        for secret in (bytes(16), bytes(range(16)))
    )
    recovery = slip39.Recovery()
    for mnemonic in (first[0][0], second[0][1], first[1][0]):
        _add_and_compare(recovery, mnemonic)
    assert recovery.groups == {0: (2, 2), 1: (1, 2)}
    held = [slip39.mnemonic_from_share(s) for s in recovery.shares]
    assert _answer(partial(slip39.master_secret_from_mnemonics, held)) == _DIGEST
