# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Tests for `bip39_slip39.exceptions`, and for who catches what it raises.

The classes add nothing to their bases, so what is tested is the
hierarchy: one base to catch everything the package raises, and each
class a subclass of the built-in that names its kind of failure. The
second half is what a caller written against `except ValueError` relies
on, and the last test asks it of a refusal the package actually raises
rather than of the class alone.
"""

from __future__ import annotations

import pickle

import pytest

from bip39_slip39 import bip39, exceptions, slip39
from bip39_slip39.exceptions import (
    Bip39Slip39Exception,
    Bip39Slip39TypeError,
    Bip39Slip39ValueError,
)


def test_every_exception_of_the_module_is_one_base_to_catch() -> None:
    """`except Bip39Slip39Exception` tells this package's failure apart.

    The classes are found rather than listed, so one added to the module
    is one this covers: a new exception that forgot the base would be a
    failure a caller catching it could not catch, and nothing else in the
    suite would say so.
    """
    classes = [
        getattr(exceptions, name)
        for name in exceptions.__all__
        if isinstance(getattr(exceptions, name), type)
    ]
    assert len(classes) == len(exceptions.__all__), "a non-class in __all__"
    uncatchable = [
        cls.__name__ for cls in classes if not issubclass(cls, Bip39Slip39Exception)
    ]
    assert not uncatchable


@pytest.mark.parametrize(
    "cls, builtin",
    [(Bip39Slip39ValueError, ValueError), (Bip39Slip39TypeError, TypeError)],
    ids=["ValueError", "TypeError"],
)
def test_the_base_is_inherited_beside_the_builtin_not_instead_of_it(
    cls: type[Bip39Slip39Exception], builtin: type[Exception]
) -> None:
    """The half that keeps every `except ValueError` already written working."""
    assert issubclass(cls, builtin)
    assert issubclass(cls, Bip39Slip39Exception)


def test_the_base_carries_no_behaviour_of_its_own() -> None:
    """It adds a name to catch and nothing else, which is the whole design."""
    assert Bip39Slip39Exception.__init__ is Exception.__init__
    assert Bip39Slip39Exception.__str__ is Exception.__str__
    error = Bip39Slip39ValueError("bad")
    assert str(error) == "bad"
    assert error.args == ("bad",)
    back = pickle.loads(pickle.dumps(error))  # noqa: S301 -- bytes this test wrote
    assert type(back) is Bip39Slip39ValueError
    assert back.args == error.args


def test_the_exceptions_are_not_btclibs() -> None:
    """A caller catching btclib's classes does not catch these.

    Which is what the module docstring says, and the reason a caller
    moving from btclib-wallet's mnemonic modules, which raise btclib's
    classes, to this package catches the
    built-in or this package's base rather than keeping btclib's name.
    btclib is a test dependency here, so asking it costs nothing the
    package pays for.
    """
    from btclib.exceptions import BTClibException  # noqa: PLC0415

    assert not issubclass(Bip39Slip39Exception, BTClibException)


def test_a_refusal_raised_inside_the_package_is_a_value_error() -> None:
    """A real refusal, from deep in a decoder, caught by the built-in alone.

    A wrong checksum is refused inside BIP39's decoder and a malformed
    share inside SLIP-0039's, several calls below the public function; an
    `except ValueError` written by a caller who never heard of this
    package's classes catches both.
    """
    with pytest.raises(ValueError, match="invalid checksum: ") as bip39_refusal:
        bip39.entropy_from_mnemonic("abandon " * 12, "en")
    assert isinstance(bip39_refusal.value, Bip39Slip39ValueError)

    with pytest.raises(ValueError, match="checksum") as slip39_refusal:
        slip39.share_from_mnemonic(" ".join(["academic"] * 20))
    assert isinstance(slip39_refusal.value, Bip39Slip39ValueError)

    # and a wrong type is a TypeError the same way
    with pytest.raises(TypeError, match="invalid passphrase type: ") as refusal:
        slip39.master_secret_from_mnemonics([], b"")  # type: ignore[arg-type]
    assert isinstance(refusal.value, Bip39Slip39TypeError)
