# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""The btclib_mnemonics package: what it publishes, and the version metadata.

BIP39, SLIP-0039 and the Electrum mnemonic schemes, from the entropy to
the seed, with the entropy sources they are generated from. Nothing
above the seed is here: the standard library is the package's only
dependency.

`__all__` here is the root of the package's public tree: the modules a
caller reaches from this name. Each of them declares its own `__all__`,
so a walk that starts here has a declared surface at every node -- which
is why the list is not `pkgutil.iter_modules`: discovery would answer
the file tree, and a module added to the directory would publish itself
rather than being published.

`name` is not in it, nor are the metadata dunders. `name` is the
distribution's name and not a member of the tree, `__version__` bound by
a star import would overwrite the importing module's own, and each is
still an attribute here: `btclib_mnemonics.__version__` is how a caller
reads the version and `btclib_mnemonics.name` how it reads the name.

Nothing is imported eagerly. A module is imported when it is first asked
for, through the `__getattr__` at the bottom of this file, so `import
btclib_mnemonics` imports nothing but the standard library's `types` and
`importlib`. The same `__getattr__` reads the version: `importlib.metadata`
is imported when `__version__` is first asked for, and not by every program
that only wants a seed. The import graph also keeps its shape: importing
every module here would put the whole package in `sys.modules` before any
single module of it could be imported first, which is the situation
tests/imports_test.py exists to make impossible.

What that costs is worth stating: mypy reads a module-level `__getattr__`
as a promise that any attribute may exist, so `btclib_mnemonics.bip93` is
`Any` to it, that function's return type, and a misspelling on this
package is a runtime `AttributeError` rather than a reported error. The
spellings a caller actually writes -- `from btclib_mnemonics import bip39`,
`import btclib_mnemonics.bip39`, `from btclib_mnemonics.bip39 import
seed_from_mnemonic` -- resolve against the real modules and stay checked.
"""

from importlib import import_module
from typing import Any

name = "btclib-mnemonics"
# a bare annotation binds nothing, so `__getattr__` still answers; it tells
# type checkers the attribute is a str rather than `__getattr__`'s return type
__version__: str

__all__ = [
    "bip39",
    "dispatch",
    "electrum",
    "entropy",
    "exceptions",
    "mnemonic",
    "slip39",
]


def __getattr__(published: str) -> Any:
    """Import a published module, or read the version, on first ask.

    PEP 562: this runs only for a name the package does not already have,
    so it answers `btclib_mnemonics.bip39` once and the import machinery's
    own attribute answers it from then on -- and it never runs for
    `import btclib_mnemonics.bip39` or `from btclib_mnemonics import bip39`,
    which import the submodule themselves. What it makes work is
    `getattr(btclib_mnemonics, "bip39")` on a fresh interpreter, which is how
    a walker reading `__all__` descends, and `from btclib_mnemonics import
    *`, which asks for each name in the list.

    `__version__` is read from the installed metadata here, so the import of
    `importlib.metadata` is paid by the first caller that asks, and kept
    after that. Anything else not in `__all__` raises `AttributeError`,
    private modules included: `import btclib_mnemonics._utils` still reaches
    one. The message is the interpreter's own wording, so a typo reads as it
    does anywhere else.

    The return type is `Any`. A union of a module and a `str` would make
    `btclib_mnemonics.bip39.mnemonic_from_entropy(...)` a mypy error in a
    strict caller that wrote only `import btclib_mnemonics`; the bare
    `__version__: str` above is what types the version.
    """
    if published == "__version__":
        from importlib.metadata import (  # noqa: PLC0415 -- the point
            PackageNotFoundError,
            version,
        )

        try:
            found = version("btclib-mnemonics")
        except PackageNotFoundError:
            # a source tree with no metadata beside it: git clone and import,
            # or read the docs, which builds without installing this package.
            # Any number here would be a guess, and reading pyproject.toml
            # back is not the way to stop guessing: the file is not in the
            # wheel. Importing has to keep working, so the version says it
            # does not know
            found = "unknown"
        globals()["__version__"] = found
        return found
    if published in __all__:
        return import_module(f"{__name__}.{published}")
    raise AttributeError(f"module {__name__!r} has no attribute {published!r}")


def __dir__() -> list[str]:
    """Answer with the published tree beside what the package already has.

    `dir(btclib_mnemonics)` consults this rather than the namespace, so
    without it a module not yet imported is missing from the completion a
    caller gets at an interactive prompt -- the same names `__getattr__`
    above will answer for, `__version__` among them.
    """
    return sorted({*__all__, "__version__", *globals()})
