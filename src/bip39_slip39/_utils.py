# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""The coercions every public function runs its inputs through.

Copies of `btclib.utils.assert_type`, `bytes_from_octets` and
`is_integer`, and of `btclib.alias.Octets`, raising this package's own
exceptions: importing them from `btclib` would make a package that
answers for mnemonics up to the seed depend on the whole of a bitcoin
library. `bytes_from_octets` is copied without the `out_size` parameter,
which nothing here passes.

A copy can drift from its original with every gate green, so
`tests/utils_test.py` runs both on one table of inputs and asks them for
the same answer, or for a refusal from the same built-in class. `utf8_bytes`
is this package's own and has no original.
"""

from __future__ import annotations

from typing import Any

from bip39_slip39.exceptions import (
    BTClibMnemonicsTypeError,
    BTClibMnemonicsValueError,
)

__all__ = [
    "Octets",
    "assert_type",
    "bytes_from_octets",
    "is_integer",
    "utf8_bytes",
]

#: Bytes, or the hex-string that decodes to them, wherever raw bytes are
#: asked for.
Octets = bytes | str | bytearray | memoryview


def _assert_byte_shaped(octets: bytes | bytearray | memoryview) -> None:
    """Refuse a memoryview whose layout or format is not plain bytes.

    `bytes` and `bytearray` are always C-contiguous and always format
    "B" (unsigned bytes); a `memoryview` need not be either, and the
    copy `bytes_from_octets` makes takes both without a word. A strided
    slice such as `mv[::2]` is not C-contiguous, and `bytes()` of one
    gathers its strides into a run that no buffer holds; a view cast to
    a signed "b", or over an array of a wider format such as "I", is
    contiguous and still counts elements where `bytes()` yields
    `itemsize` octets of each.
    """
    if not isinstance(octets, memoryview):
        return
    if not octets.c_contiguous:
        err_msg = "invalid octets: non-contiguous memoryview"
        raise BTClibMnemonicsValueError(err_msg)
    if octets.format != "B":
        err_msg = f"invalid octets: memoryview format {octets.format!r} instead of 'B'"
        raise BTClibMnemonicsValueError(err_msg)


def bytes_from_octets(octets: Octets) -> bytes:
    """Return bytes from a hex-string, stripping leading/trailing spaces.

    A `bytearray` or a `memoryview` is copied, which is what makes the
    `bytes` this promises true: handed back as it came, either is still
    the caller's own object, so a write to it afterwards reaches into
    whatever kept the return value.
    """
    if isinstance(octets, str):  # hex string
        # the message is fromhex's own, which names a position and never
        # the string: an Octets parameter is candidate seed material
        try:
            return bytes.fromhex(octets)
        except ValueError as e:
            raise BTClibMnemonicsValueError(f"invalid hex string: {e}") from e
    if isinstance(octets, (bytes, bytearray, memoryview)):
        _assert_byte_shaped(octets)
        return bytes(octets)
    # what is neither would otherwise reach whatever the caller does next
    # with it, and fail there as a complaint about a builtin
    err_msg = f"invalid octets type: {type(octets).__name__}"  # type: ignore[unreachable]
    raise BTClibMnemonicsTypeError(err_msg)


def is_integer(value: Any) -> bool:
    """Return whether the value is an integer, a bool not being one.

    `isinstance(x, int)` is True for `True` and `False`, `bool` being a
    subclass of `int`, and `true` is what a json document decodes to
    `True`: a schema mistake would become a roll of one or an index of
    one instead of failing next to the input that caused it.

    `isinstance` and not `type(value) is int`, so an `IntEnum` and any
    other deliberate integer subclass stay integers. `bool` is the one
    subclass excluded, and by name.
    """
    return isinstance(value, int) and not isinstance(value, bool)


def utf8_bytes(text: str, what: str) -> bytes:
    """Return the UTF-8 encoding of a str, refusing a lone surrogate.

    A lone surrogate is a str no UTF-8 text holds, and arrives through
    ``surrogateescape`` decoding. `str.encode` would raise a
    `UnicodeEncodeError` carrying the whole text in its `object`, so the
    refusal is the package's own and chains nothing.
    """
    try:
        return text.encode()
    except UnicodeEncodeError:
        pass
    # raised outside the except: inside it, the error would stay in
    # __context__ even with "from None"
    raise BTClibMnemonicsValueError(f"invalid {what}: contains a lone surrogate")


def assert_type(value: Any, expected: Any, what: str) -> None:
    """Refuse a value of a type the signature does not declare.

    `expected` is what `isinstance` takes: one type, or a tuple of them.
    `value` is `Any` rather than the declared type, which is what makes
    the check reachable: mypy proves the argument cannot be wrong, and
    the caller who has not run mypy is who this is for.
    """
    if not isinstance(value, expected):
        err_msg = f"invalid {what} type: {type(value).__name__}"
        raise BTClibMnemonicsTypeError(err_msg)
