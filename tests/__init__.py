# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""The bip39_slip39 test suite, and the code its modules share.

The vector files are the reference implementations' and electrum's:
read them here and hand them to `pytest.mark.parametrize`, so that a
vector is a test rather than one turn of a loop inside a single test
function: a failure names the vector instead of the loop that was running
it, and the vectors after the first failure still run -- a loop stops at
the first one and reports nothing about the rest.

Here rather than in a `tests/vectors.py`: every Python file under `tests/`
is a test file except `__init__.py` and `conftest.py`, so shared test
code lives in the package `__init__`.

This package is imported by every test module, before that module's own
body runs. Whatever this file executes at import time therefore executes
inside every module's own measured reach: the suite's coverage floor
reads what the import reaches, never what a test body goes on to call. A
literal is safe to share here at module scope. Anything that calls into
the package's own arithmetic is shared as a function instead, computed
only when a caller invokes it.
"""

import json
import pkgutil
import re
from pathlib import Path
from typing import Any

import bip39_slip39

_TESTS_DIR = Path(__file__).parent


def module_names() -> list[str]:
    """Return every module of the installed bip39_slip39, the root included.

    Here rather than at each site that walks the package, none of which
    owns the walk. What the walk covers -- a second package root, a
    different prefix, a module it has to skip -- is settled here for all
    of them, and a copy that disagreed would be red nowhere: each site
    asserts against whatever its own walk found.
    """
    return [
        "bip39_slip39",
        *(
            module.name
            for module in pkgutil.walk_packages(bip39_slip39.__path__, "bip39_slip39.")
        ),
    ]


def load(*relative_path: str, encoding: str = "ascii") -> Any:
    """Read a vendored JSON vector file, named relative to `tests/`.

    Naming a vector file by its path from the test suite root, rather
    than from the test module that reads it, is what spares every reader
    the `dirname(__file__)` walk that breaks the moment a test module
    moves.
    """
    with _TESTS_DIR.joinpath(*relative_path).open(encoding=encoding) as file_:
        return json.load(file_)


# what makes an id unreadable in a report and unusable in a -k expression:
# anything that is not a letter, a digit or a dash. A vector's description
# holds spaces, quotes, parentheses and slashes, and a mnemonic is words
_NOT_IN_AN_ID = re.compile(r"[^0-9A-Za-z]+")


def vector_id(index: int, *description: object) -> str:
    """Name the vector at `index`: where it is, then what it is about.

    The position alone is what parametrize generates on its own, and it
    says where in the file to look but not what the case was testing;
    the description alone -- the comment of a SLIP-0039 vector, a
    language, a mnemonic -- reads well but is neither unique nor always
    there. Both, so that the red line of a report both identifies the
    vector in the file and says what it is, and `-k` can select it.

    Truncated, because a description is occasionally a whole sentence: an
    id is a name, and the vector file remains the place to read the
    case in full.
    """
    text = "-".join(str(d) for d in description if d)
    text = _NOT_IN_AN_ID.sub("-", text).strip("-")
    return f"{index}-{text[:60]}" if text else str(index)
