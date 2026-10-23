# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""The gate for the two rules about a public function's inputs.

> Every public function guarantees the validation of all its inputs,
> directly or indirectly. A malformed argument leaves as
> `BTClibMnemonicsTypeError` or `BTClibMnemonicsValueError`.

CONTRIBUTING.md's "Every public function validates its inputs" states it,
and which of the two classes comes out is not a coin toss -- it is the
distinction issue btclib-org/btclib#814 settled, so this file drives the
two separately:

- **a value of a type the signature does not declare** is the caller's
  own mistake, and leaves as a `BTClibMnemonicsTypeError`.
- **a value of a declared type that no valid input carries** is a fact
  about the input, and leaves as a `BTClibMnemonicsException`.

## How it calls what it calls

The input types are few and declared in this package: `Mnemonic` in
`mnemonic.py`, `BinStr` and `Entropy` in `entropy.py`, `Octets` in
`_utils.py`. `_WRONG_TYPE` and `_WRONG_VALUE` give each of them values of
the two kinds, and the walk finds every public module-level function
whose *required* parameters are all of those types. Those it can call
with no fixture and no knowledge of what the function does.

Every argument is wrong at once, which is not weaker than one wrong
argument among valid ones: whichever the function refuses first, the rule
says how it must refuse it. And it needs no valid values, which is what
makes the walk automatic.

## What it does not reach

A **parameter with a default** is never driven: to reach it the arguments
before it would have to be valid, which is the table this design is built
to do without. `tests/bool_parameter_test.py` carries that table for the
`bool` ones.

A **method**, and a function taking a plain `str`, `int`, a `Share` or a
callback, needs a value the vocabulary does not build, and is driven by
the tests of its own module. `test_the_walk_reaches_what_it_claims` pins
what the walk does find, so a narrowing of it fails here rather than
quietly running over less.

A function whose answer is a reading of any value of its type, rather
than a check of it, answers a wrong value too: `_ANSWERS_A_WRONG_VALUE`
names each the walk reaches, with its reason, and the second rule is
asserted of them the other way round.
"""

from __future__ import annotations

import ast
import importlib
from collections.abc import Callable, Iterator
from functools import partial
from pathlib import Path
from typing import Any

import pytest

from bip39_slip39.exceptions import (
    BTClibMnemonicsException,
    BTClibMnemonicsTypeError,
)

_LIBRARY = Path(__file__).parents[1] / "src" / "bip39_slip39"

# a value of no type the alias declares: the caller's own mistake, and a
# call mypy refuses. The tuples are read round-robin so that a function
# taking three parameters of one type is called with three different
# wrong values. Constants and not a strategy: what this gate reports has
# to be the same on two runs, the lists below being read as statements
# about the tree
_WRONG_TYPE: dict[str, tuple[Any, ...]] = {
    # bytes, which int(x, 2) reads as the digits they spell
    "BinStr": (None, 1.5, 1, b"0101"),
    # an int is an Entropy
    "Entropy": (None, 1.5),
    "Mnemonic": (None, 1.5, b"abandon"),
    "Octets": (None, 1.5, tuple(range(4))),
    # a lone mnemonic, which is a Sequence[str] as far as mypy goes
    # (issue btclib-org/btclib#1405)
    "Sequence[Mnemonic]": (None, 1.5, "abandon"),
}

# a value of a declared type that no valid input carries: a fact about
# the input. Every one of these type checks -- that is what puts it in
# this dict rather than in the one above -- so a `# type: ignore` is never
# needed to build the call, which is the same line drawn twice
_WRONG_VALUE: dict[str, tuple[Any, ...]] = {
    "BinStr": ("not binary",),
    # a string that is not 0/1 digits, and an int below zero
    "Entropy": ("not binary", -1),
    "Mnemonic": ("not a mnemonic",),
    # a hex string that is not hex, and one of odd length
    "Octets": ("not hex at all", "9"),
    "Sequence[Mnemonic]": (["not a mnemonic"],),
}


def _alias_of(annotation: ast.expr) -> str | None:
    """Return the input type an annotation names, `X | None` included."""
    name = ast.unparse(annotation).replace(" | None", "").strip()
    return name if name in _WRONG_TYPE else None


def _drivable() -> dict[str, list[str]]:
    """Return every public function the vocabulary can call, by dotted name.

    Required parameters only: what carries a default is what a caller may
    leave out, so a function is driven on the arguments it insists on.
    All of them have to be in the vocabulary -- one `str` and the walk has
    nothing to pass.
    """
    found: dict[str, list[str]] = {}
    for path in sorted(_LIBRARY.rglob("*.py")):
        module = ".".join(path.relative_to(_LIBRARY.parent).with_suffix("").parts)
        for node in ast.parse(path.read_text(encoding="utf-8")).body:
            if not isinstance(node, ast.FunctionDef) or node.name.startswith("_"):
                continue
            positional = [*node.args.posonlyargs, *node.args.args]
            required = positional[: len(positional) - len(node.args.defaults)]
            # `is not None` narrows for mypy and never filters: mypy runs
            # strict over this package, so a parameter without an
            # annotation is a state the library does not reach
            annotations = [a.annotation for a in required if a.annotation is not None]
            aliases = [_alias_of(a) for a in annotations]
            if required and len(aliases) == len(required) and all(aliases):
                found[f"{module}.{node.name}"] = [a for a in aliases if a]
    return found


_DRIVABLE = _drivable()


def _calls(
    dotted: str, vocabulary: dict[str, tuple[Any, ...]]
) -> Iterator[Callable[[], Any]]:
    """Yield one prepared call per round, every argument wrong at once.

    The vocabulary is the parameter, and it is the whole of what tells the
    two rules apart: the same walk, the same function, two kinds of wrong
    value.
    """
    module_name, _, name = dotted.rpartition(".")
    function = getattr(importlib.import_module(module_name), name)
    aliases = _DRIVABLE[dotted]
    for round_ in range(max(len(vocabulary[a]) for a in aliases)):
        args = [vocabulary[a][round_ % len(vocabulary[a])] for a in aliases]
        # partial and not a lambda, which would close over the loop
        # variables and be read on a later round
        yield partial(function, *args)


_DRIVEN = sorted(_DRIVABLE)

# what answers every wrong value of _WRONG_VALUE instead of refusing it,
# by dotted name, with the reason that is its contract
_ANSWERS_A_WRONG_VALUE = {
    # an `is_*` is total over the declared types: False is its answer
    "bip39_slip39.bip39.is_valid_mnemonic",
    # a sentence no scheme claims: the empty list, and "", are the answers
    # the two docstrings give for it
    "bip39_slip39.dispatch.all_seed_types_from_mnemonic",
    "bip39_slip39.dispatch.seed_type_from_mnemonic",
    # a reading of the sentence that checks nothing of its value, so any
    # str is normalized whether or not it is a mnemonic
    "bip39_slip39.mnemonic.normalize_mnemonic",
}


@pytest.mark.parametrize("dotted", _DRIVEN)
def test_a_wrong_type_leaves_as_a_type_error_of_the_package(dotted: str) -> None:
    """The first rule, and it has no exceptions.

    `BTClibMnemonicsTypeError` and not the base: this is where the class is
    the point. A bare `TypeError` fails here as a `BTClibMnemonicsValueError`
    does -- the first is a leak from underneath the package, the second
    is the package calling a caller's mistake a fact about the input.
    """
    for call in _calls(dotted, _WRONG_TYPE):
        with pytest.raises(BTClibMnemonicsTypeError):
            call()


@pytest.mark.parametrize(
    "dotted", [d for d in _DRIVEN if d not in _ANSWERS_A_WRONG_VALUE]
)
def test_a_wrong_value_leaves_as_an_exception_of_the_package(dotted: str) -> None:
    """The second rule, over what the walk drives and does not answer.

    The base and not one of the two: which of them a malformed value
    deserves is the function's to decide, and the contract a caller is
    given is the base.
    """
    for call in _calls(dotted, _WRONG_VALUE):
        with pytest.raises(BTClibMnemonicsException):
            call()


@pytest.mark.parametrize("dotted", sorted(_ANSWERS_A_WRONG_VALUE))
def test_what_answers_a_wrong_value_answers_it(dotted: str) -> None:
    """An exemption from the second rule holds, or it is one left behind.

    A function in `_ANSWERS_A_WRONG_VALUE` that starts refusing, or that
    the walk stops reaching, fails here.
    """
    assert dotted in _DRIVABLE
    for call in _calls(dotted, _WRONG_VALUE):
        call()


def test_the_vocabulary_is_the_packages_input_types() -> None:
    """A renamed type would narrow the walk without failing anything.

    Every name in the two vocabularies is declared at module level in
    this package, and every type the package declares and a public
    parameter is annotated with is in the vocabulary.
    """
    declared: set[str] = set()
    annotated: set[str] = set()
    for path in sorted(_LIBRARY.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        declared |= {
            node.targets[0].id
            for node in tree.body
            if isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id[0].isupper()
        }
        annotated |= {
            ast.unparse(a.annotation).replace(" | None", "").strip()
            for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef) and not node.name.startswith("_")
            for a in [*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs]
            if a.annotation is not None
        }

    assert set(_WRONG_TYPE) == set(_WRONG_VALUE)
    # `Sequence[Mnemonic]` is no declaration of its own -- `Mnemonic` is
    unwrapped = {
        alias.removeprefix("Sequence[").removesuffix("]") for alias in _WRONG_TYPE
    }
    assert unwrapped <= declared
    assert declared & annotated <= set(_WRONG_TYPE)


def test_the_walk_reaches_what_it_claims() -> None:
    """The shapes the walk must find, and two it must not.

    A walk that found nothing would pass every test above. One function
    per shape it has to reach -- a single parameter, a sequence of them,
    one behind a default it must ignore -- and the two kinds it must
    leave alone: a private name, and a function whose required parameters
    are not all in the vocabulary.
    """
    assert _DRIVABLE["bip39_slip39.slip39.share_from_mnemonic"] == ["Mnemonic"]
    assert _DRIVABLE["bip39_slip39.slip39.master_secret_from_mnemonics"] == [
        "Sequence[Mnemonic]"
    ]
    # `lang` carries a default and is not driven
    assert _DRIVABLE["bip39_slip39.bip39.entropy_from_mnemonic"] == ["Mnemonic"]

    # `_entropy_checksum` takes an `Entropy`, which the vocabulary builds
    assert "bip39_slip39.bip39._entropy_checksum" not in _DRIVABLE
    # a required parameter the vocabulary does not build: the passphrase
    assert "bip39_slip39.bip39.seed_from_mnemonic" not in _DRIVABLE
