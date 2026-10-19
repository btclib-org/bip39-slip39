# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Tests for the one policy on integer fields: a bool is not a number.

One file rather than a case per module, because the decision is one and
`btclib_mnemonics._utils.is_integer` states it. What makes it worth a
refusal is the json boundary: `true` decodes to `True`, and a schema
mistake would become a roll of one, an index of one or a threshold of
one instead of failing beside the input that caused it.
"""

from __future__ import annotations

from collections.abc import Callable
from enum import IntEnum
from functools import partial
from typing import Any

import pytest

from btclib_mnemonics._utils import is_integer
from btclib_mnemonics.entropy import (
    _bin_str_entropy_from_wordlist_indexes,
    bin_str_entropy_from_rolls,
)
from btclib_mnemonics.exceptions import BTClibMnemonicsTypeError
from btclib_mnemonics.slip39 import (
    EncryptedMasterSecret,
    Recovery,
    Share,
    master_secret_from_mnemonics,
    mnemonic_from_share,
    mnemonics_from_encrypted_master_secret,
    mnemonics_from_master_secret,
)


def _share(**field: Any) -> Share:
    """Return a 1-of-1 SLIP-0039 share, with one field of it replaced."""
    fields: dict[str, Any] = {
        "identifier": 1,
        "extendable": True,
        "iteration_exponent": 0,
        "group_index": 0,
        "group_threshold": 1,
        "group_count": 1,
        "member_index": 0,
        "member_threshold": 1,
        "value": bytes(16),
    }
    return Share(**(fields | field))


_SHARE_FIELDS = (
    "identifier",
    "iteration_exponent",
    "group_index",
    "group_threshold",
    "group_count",
    "member_index",
    "member_threshold",
)


def _share_with(name: str, value: Any) -> Share:
    """Return `_share` with the field `name` set to `value`."""
    return _share(**{name: value})


# every field whose contract is an integer quantity, with the shortest
# call that reaches its validator
_CASES: list[tuple[str, Callable[[Any], object]]] = [
    ("word-list index", lambda v: _bin_str_entropy_from_wordlist_indexes([v], 2048)),
    ("dice roll bits", lambda v: bin_str_entropy_from_rolls(v, 2, [1, 2, 1, 2])),
    ("dice base", lambda v: bin_str_entropy_from_rolls(4, v, [1, 2, 1, 2])),
    ("dice roll", lambda v: bin_str_entropy_from_rolls(4, 2, [v, 2, 1, 2])),
    (
        "slip39 group threshold",
        lambda v: mnemonics_from_master_secret(bytes(16), group_threshold=v),
    ),
    (
        "slip39 iteration exponent",
        lambda v: mnemonics_from_master_secret(bytes(16), iteration_exponent=v),
    ),
    (
        "slip39 member threshold",
        lambda v: mnemonics_from_master_secret(bytes(16), groups=[(v, 1)]),
    ),
    (
        "slip39 member count",
        lambda v: mnemonics_from_master_secret(bytes(16), groups=[(1, v)]),
    ),
    (
        "slip39 max iteration exponent",
        lambda v: master_secret_from_mnemonics(
            [mnemonic_from_share(_share())], max_iteration_exponent=v
        ),
    ),
    (
        "slip39 encrypted master secret identifier",
        lambda v: EncryptedMasterSecret(v, True, 0, bytes(16)),
    ),
    (
        "slip39 encrypted master secret iteration exponent",
        lambda v: EncryptedMasterSecret(1, True, v, bytes(16)),
    ),
    (
        "slip39 encrypted master secret max iteration exponent",
        lambda v: EncryptedMasterSecret(1, True, 0, bytes(16)).master_secret(
            max_iteration_exponent=v
        ),
    ),
    (
        "slip39 encrypted split group threshold",
        lambda v: mnemonics_from_encrypted_master_secret(
            EncryptedMasterSecret(1, True, 0, bytes(16)), group_threshold=v
        ),
    ),
    (
        "slip39 recovery max iteration exponent",
        lambda v: Recovery(max_iteration_exponent=v),
    ),
    # partial and not a lambda, which would close over the loop variable
    *((f"slip39 share {name}", partial(_share_with, name)) for name in _SHARE_FIELDS),
]

_IDS = [case[0] for case in _CASES]
_CALLS = [case[1] for case in _CASES]


@pytest.mark.parametrize("call", _CALLS, ids=_IDS)
@pytest.mark.parametrize("value", [True, False], ids=["true", "false"])
def test_a_bool_is_not_an_integer_field(
    call: Callable[[Any], object], *, value: bool
) -> None:
    """Every integer field refuses a boolean, and refuses it as a type.

    `isinstance(True, int)` is what would let each of these through as one
    or zero.
    """
    with pytest.raises(BTClibMnemonicsTypeError):
        call(value)


def test_the_integers_a_bool_refusal_must_not_take_with_it() -> None:
    """The same calls with a number, which is what the refusal is around.

    A test that only checks refusals passes just as well when the field
    refuses everything.
    """
    assert _bin_str_entropy_from_wordlist_indexes([1], 2048) == "00000000001"
    assert bin_str_entropy_from_rolls(4, 2, [1, 2, 1, 2]) == "0101"
    one_of_one = mnemonics_from_master_secret(
        bytes(16), [(1, 1)], group_threshold=1, iteration_exponent=0
    )
    assert [len(group) for group in one_of_one] == [1]
    combined = master_secret_from_mnemonics(one_of_one[0], max_iteration_exponent=1)
    assert combined == bytes(16)
    ems = EncryptedMasterSecret(1, True, 1, bytes(16))
    assert ems.master_secret(max_iteration_exponent=1) == ems.master_secret()
    assert len(mnemonics_from_encrypted_master_secret(ems, group_threshold=1)) == 1
    assert Recovery(max_iteration_exponent=1).groups == {}
    assert all(getattr(_share_with(n, 1), n) == 1 for n in _SHARE_FIELDS)


def test_an_int_subclass_that_is_not_a_bool_is_still_an_integer() -> None:
    """`IntEnum` stays a number, which is why the predicate names bool.

    `type(value) is int` would refuse every `int` subclass, where the
    policy refuses one.
    """

    class Small(IntEnum):
        ONE = 1

    assert is_integer(Small.ONE)
    assert _bin_str_entropy_from_wordlist_indexes([Small.ONE], 2048) == "00000000001"

    assert is_integer(0)
    assert is_integer(-1)
    assert not is_integer(True)
    assert not is_integer(False)
    assert not is_integer(1.0)
    assert not is_integer("1")
