# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Exception classes.

These exist only to tell an exception raised by bip39_slip39 from one
raised by any other code: each derives from the built-in that says what
kind of failure it is, and adds nothing to it.

`Bip39Slip39Exception` is what makes that telling apart a single
`except` rather than a tuple a caller has to keep in step with this
hierarchy. It is inherited *beside* the built-in and not instead of it,
which is the half that matters: `Bip39Slip39ValueError` is a
`ValueError`, so code catching the built-in catches it, and
`json.JSONDecodeError` is the standard library doing the same.

It is caught and never raised: every raise in the package is one of the
two below it, and which one answers a question the base cannot carry --
whether the value was wrong or the type was. A caller with something to
do about that difference names the specific class; `except
Bip39Slip39Exception` is for the caller who only needs to know it came
from here.

The classes are this package's own rather than `btclib`'s, which is what
keeps the package free of any import of `btclib`: a caller catching
`btclib.exceptions.BTClibValueError` does not catch these, and one
catching `ValueError` catches both.
"""

from __future__ import annotations

__all__ = [
    "Bip39Slip39Exception",
    "Bip39Slip39TypeError",
    "Bip39Slip39ValueError",
]


class Bip39Slip39Exception(Exception):  # noqa: N818 -- a kind, like Exception itself, not a leaf raised
    """Anything bip39_slip39 raised, whatever kind of failure it is.

    The one name to catch for a caller who handles the standard library's
    exceptions anyway and needs to know which came from here. Never
    raised: the two below it are, and each says which kind of failure it
    was.
    """


class Bip39Slip39ValueError(Bip39Slip39Exception, ValueError):
    """A value no valid input could carry; the package's usual refusal."""


class Bip39Slip39TypeError(Bip39Slip39Exception, TypeError):
    """An input of a type no conversion accepts: a caller error."""
