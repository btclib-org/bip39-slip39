# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""The coercions of `bip39_slip39._utils`, against btclib's originals.

`_utils.py` copies `assert_type`, `bytes_from_octets`, `is_integer` and
`Octets` from `btclib` so that the package imports nothing of it, and a
copy can drift from its original with every other gate green. So each
input of one table is handed to both, and the two have to agree: the
same answer, or a refusal of the same built-in class and message, the
copy's being this package's own exception where the original's is
btclib's.

btclib is a test dependency and never a runtime one, which is what lets
it be the oracle here: tests/imports_test.py is what keeps it out of the
package.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, get_args

import pytest
from btclib import alias as btclib_alias
from btclib import utils as btclib_utils
from btclib.exceptions import BTClibException

from bip39_slip39 import _utils
from bip39_slip39.exceptions import Bip39Slip39Exception

_OCTETS = [
    b"",
    b"\x00\xff",
    bytearray(b"\x01\x02"),
    memoryview(b"\x03\x04"),
    "",
    "00ff",
    " 00ff ",
    "0x00",
    "not hex",
    "abc",
    "\N{FULLWIDTH DIGIT ONE}0",
    memoryview(b"abcd")[::2],
    memoryview(b"abcd").cast("b"),
    None,
    1,
    1.5,
    [0, 1],
]

_VALUES: list[Any] = [0, 1, -1, True, False, 1.0, "1", None, b"1", 2**300]

# what `isinstance` takes as its second argument: one type, or a tuple
_EXPECTED: list[Any] = [str, bytes, int, (str, bytes), (int, float)]

_CASES: list[tuple[str, Callable[[Any], Any], Callable[[Any], Any], Any]] = [
    *(
        (
            "bytes_from_octets",
            _utils.bytes_from_octets,
            btclib_utils.bytes_from_octets,
            v,
        )
        for v in _OCTETS
    ),
    *(("is_integer", _utils.is_integer, btclib_utils.is_integer, v) for v in _VALUES),
    *(
        (
            "assert_type",
            lambda v, e=e: _utils.assert_type(v, e, "value"),
            lambda v, e=e: btclib_utils.assert_type(v, e, "value"),
            v,
        )
        for e in _EXPECTED
        for v in _VALUES
    ),
]


def _outcome(function: Callable[[Any], Any], value: Any) -> tuple[str, Any]:
    """Return what one call answered, or the built-in and message it raised.

    The class compared is the built-in beneath the package's own: the
    copy raises this package's exceptions and the original btclib's, and
    each is a `ValueError` or a `TypeError` beside its package's base.
    """
    try:
        return "answer", function(value)
    except (Bip39Slip39Exception, BTClibException) as error:
        builtin = next(c for c in type(error).__mro__ if c in {ValueError, TypeError})
        return builtin.__name__, str(error)


@pytest.mark.parametrize(
    "copy, original, value",
    [case[1:] for case in _CASES],
    ids=[f"{index}-{case[0]}" for index, case in enumerate(_CASES)],
)
def test_the_copy_answers_as_the_original(
    copy: Callable[[Any], Any], original: Callable[[Any], Any], value: Any
) -> None:
    """One input, both functions, one outcome."""
    assert _outcome(copy, value) == _outcome(original, value)


def test_the_copy_raises_the_packages_own_exceptions() -> None:
    """The half the comparison above abstracts away, asserted by name."""
    with pytest.raises(Bip39Slip39Exception):
        _utils.bytes_from_octets("not hex")
    with pytest.raises(Bip39Slip39Exception):
        _utils.bytes_from_octets(1.5)  # type: ignore[arg-type]
    with pytest.raises(Bip39Slip39Exception):
        _utils.assert_type(1, str, "value")


def test_octets_is_the_same_union() -> None:
    """The alias names the same four types as btclib's."""
    assert set(get_args(_utils.Octets)) == set(get_args(btclib_alias.Octets))


def test_the_table_reaches_every_outcome() -> None:
    """An answer, a value refusal and a type refusal, from each copy it asks.

    A table that only held valid inputs would agree on every row and
    say nothing about the refusals, which is where a copy drifts.
    """
    outcomes = {(name, _outcome(copy, value)[0]) for name, copy, _, value in _CASES}
    assert outcomes >= {
        ("bytes_from_octets", "answer"),
        ("bytes_from_octets", "ValueError"),
        ("bytes_from_octets", "TypeError"),
        ("is_integer", "answer"),
        ("assert_type", "answer"),
        ("assert_type", "TypeError"),
    }
