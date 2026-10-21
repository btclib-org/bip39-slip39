# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Every `bool` parameter of the package, classified and held to its class.

A kind written down and read back -- json, a configuration file, a
coordinator's message -- arrives as whatever it was written as, and
`"false"` is true (issue btclib-org/btclib#868).

## The line

A **truth** only decides whether the call refuses: `verify_checksum=False`
says do not check, and the answer is the same one. So a value read for its
truth runs a check or skips one and changes no answer, which is why
nothing is refused there.

A **kind** decides what a non-refusing call computes or returns. `"no"`
is true, so a kind read for its truth quietly computes the other answer
-- the other entropy, the other set of shares -- and that is what the
refusal is for.

## The polarity a truth has to have

`CONTRIBUTING.md`'s *A truth's `True` has to be its conservative value*
is the rule, with the wrong values it does not cover (issue
btclib-org/btclib#884).

The two tests below are that line, one each:

- a kind refuses `"no"`, `0`, `1` and (where the annotation does not
  declare it) `None`, with a `BTClibMnemonicsTypeError`
- a truth **accepts** them, on a fixture the flag's `True` accepts: a
  truth that starts refusing fails here, and the entry has to move rather
  than the test being edited

## The walk

`_bool_parameters` reads every public function of the package and every
`bool`-annotated parameter of one, so a flag added anywhere is either in a
table here or the run is red -- there is no third table, and that is the
state to keep.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest

from bip39_slip39 import bip39, slip39
from bip39_slip39.exceptions import BTClibMnemonicsTypeError
from bip39_slip39.mnemonic import WordLists

_LIBRARY = Path(__file__).parents[1] / "src" / "bip39_slip39"

# a value of no bool type: a truthy string, and the two integers `bool`
# inherits from. Every one of them is a call mypy refuses
_WRONG_TYPES: tuple[Any, ...] = ("no", 0, 1)


@dataclass(frozen=True)
class _Case:
    """One `bool` parameter, and a call of its function that works."""

    dotted: str
    flag: str
    function: Any
    # every argument but the flag, by keyword
    args: dict[str, Any] = field(default_factory=dict)
    # the classification, which is prose because it is a judgement: for a
    # truth what the flag turns on and what it therefore cannot change
    reason: str = ""


_KINDS = (
    _Case(
        "bip39_slip39.slip39.mnemonics_from_master_secret",
        "extendable",
        slip39.mnemonics_from_master_secret,
        {"master_secret": "00" * 16},
    ),
)

_TRUTHS = (
    _Case(
        "bip39_slip39.bip39.seed_from_mnemonic",
        "verify_checksum",
        bip39.seed_from_mnemonic,
        {"mnemonic": "abandon " * 11 + "about", "passphrase": ""},
        reason="whether the mnemonic's checksum is checked; the seed is the"
        " same either way, being a PBKDF2 of the words",
    ),
    _Case(
        "bip39_slip39.mnemonic.WordLists.__init__",
        "power_of_two",
        WordLists,
        {},
        reason="whether a word list whose length is not a power of two is"
        " refused, which is what Electrum's 1626 words need off",
    ),
)

_KIND_IDS = tuple(f"{case.dotted}({case.flag})" for case in _KINDS)
_TRUTH_IDS = tuple(f"{case.dotted}({case.flag})" for case in _TRUTHS)


def _flags_of(function: ast.FunctionDef) -> set[str]:
    """Return the `bool`-annotated parameters of one public function."""
    if function.name.startswith("_") and not function.name.startswith("__"):
        return set()
    arguments = [
        *function.args.posonlyargs,
        *function.args.args,
        *function.args.kwonlyargs,
    ]
    return {
        argument.arg
        for argument in arguments
        if argument.annotation is not None
        and ast.unparse(argument.annotation) in {"bool", "bool | None"}
    }


def _bool_parameters() -> set[tuple[str, str]]:
    """Return every (function, `bool` parameter) pair of the public API.

    Keyed on the annotation, `bool` and `bool | None`: what a flag is
    called says nothing. A method counts and a private function does not,
    and a function nested in another is a closure rather than API.
    """
    found: set[tuple[str, str]] = set()

    def walk(node: ast.Module | ast.ClassDef, module: str, prefix: str) -> None:
        for child in node.body:
            if isinstance(child, ast.ClassDef):
                walk(child, module, f"{prefix}{child.name}.")
            elif isinstance(child, ast.FunctionDef):
                dotted = f"{module}.{prefix}{child.name}"
                found.update((dotted, flag) for flag in _flags_of(child))

    for path in sorted(_LIBRARY.rglob("*.py")):
        module = ".".join(path.relative_to(_LIBRARY.parent).with_suffix("").parts)
        walk(ast.parse(path.read_text(encoding="utf-8")), module, "")
    return found


@pytest.mark.parametrize("case", [*_KINDS, *_TRUTHS], ids=[*_KIND_IDS, *_TRUTH_IDS])
def test_the_call_works(case: _Case) -> None:
    """The fixture is valid, which is what makes a refusal below a finding.

    Without this a case whose arguments had gone stale would pass every
    test in the file by refusing everything it is handed.
    """
    case.function(**case.args, **{case.flag: True})


@pytest.mark.parametrize("case", _KINDS, ids=_KIND_IDS)
def test_a_kind_refuses_a_non_bool(case: _Case) -> None:
    """A kind decides what is computed, so it is not read for its truth.

    `"no"` is the value that makes the point -- it is true, so the flag
    would be on -- and `0` and `1` are the two `bool` inherits from, which
    is what makes `isinstance(value, int)` no check at all here. `None`
    is wrong too, no kind here declaring `bool | None`.
    """
    for value in (*_WRONG_TYPES, None):
        with pytest.raises(BTClibMnemonicsTypeError, match=f"invalid {case.flag} type"):
            case.function(**case.args, **{case.flag: value})


@pytest.mark.parametrize("case", _TRUTHS, ids=_TRUTH_IDS)
def test_a_truth_is_read_for_its_truth(case: _Case) -> None:
    """The other half of the line, and the ratchet under this file.

    A truth turns a check on or off and changes no answer, so a value of
    another type is read for whether it is true and refused by nothing.
    An entry that starts refusing fails here rather than passing quietly:
    the fix is to move it to `_KINDS`, which is a decision about the
    parameter and not about this test.
    """
    assert case.reason
    for value in _WRONG_TYPES:
        case.function(**case.args, **{case.flag: value})


def test_every_bool_parameter_is_classified() -> None:
    """No third table: a flag is a kind or a truth, and the walk says so.

    A parameter added anywhere under `src/bip39_slip39/` fails here until
    somebody decides which of the two it is -- which is the decision this
    file exists to keep from being made by default.
    """
    classified = {(case.dotted, case.flag) for case in (*_KINDS, *_TRUTHS)}
    found = _bool_parameters()
    assert classified == found, (
        f"unclassified: {sorted(found - classified)};"
        f" gone from the tree: {sorted(classified - found)}"
    )


def test_the_walk_reaches_what_it_claims() -> None:
    """The shapes it must find, and the ones it must not.

    A walk that found nothing would pass the test above.
    """
    found = _bool_parameters()
    # a function's flag, and a method's
    assert ("bip39_slip39.bip39.seed_from_mnemonic", "verify_checksum") in found
    assert ("bip39_slip39.mnemonic.WordLists.__init__", "power_of_two") in found

    # a private function, and a parameter of another type
    assert ("bip39_slip39.slip39._feistel", "decrypt") not in found
    assert ("bip39_slip39.bip39.seed_from_mnemonic", "passphrase") not in found
