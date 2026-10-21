# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Tests for the `bip39_slip39` package metadata."""

import importlib.metadata
import subprocess
import sys

import pytest

import bip39_slip39


def test_version() -> None:
    """Verify __version__ matches the installed metadata."""
    version: str = bip39_slip39.__version__  # type-checks only as a str
    assert version == importlib.metadata.version("bip39-slip39")


def test_submodule_through_the_package_type_checks() -> None:
    """A submodule reached from the bare package passes mypy.

    The gate that fails is mypy's, not this assertion: `__getattr__`'s
    return type is what it reads.
    """
    mnemonic = bip39_slip39.bip39.mnemonic_from_entropy(bytes(16))
    assert mnemonic.split()[-1] == "about"


def test_version_without_installed_metadata(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A source tree with no metadata beside it reads the version as "unknown".

    The suite cannot exercise that situation as it is, the package being
    installed in the environment running it, so the lookup is made to fail.
    Reading the version must not raise PackageNotFoundError
    (issue btclib-org/btclib#150).
    """

    def raise_package_not_found(_: str) -> str:
        raise importlib.metadata.PackageNotFoundError

    # patch the attribute of the module: the `from importlib.metadata import
    # version` inside `__getattr__` looks it up on every first access
    monkeypatch.setattr(importlib.metadata, "version", raise_package_not_found)
    # forget a version an earlier access read and kept
    vars(bip39_slip39).pop("__version__", None)
    try:
        assert bip39_slip39.__version__ == "unknown"
    finally:
        # forget the kept "unknown", so the module every other test sees
        # reads the real version again. monkeypatch would undo the patch by
        # itself, but not the module state it produced
        monkeypatch.undo()
        vars(bip39_slip39).pop("__version__", None)

    assert bip39_slip39.__version__ == importlib.metadata.version("bip39-slip39")


def test_version_listed_before_it_is_read() -> None:
    """`dir` lists `__version__` on a fresh namespace, before any access."""
    vars(bip39_slip39).pop("__version__", None)
    assert "__version__" in dir(bip39_slip39)


def test_import_does_not_import_metadata() -> None:
    """Importing a scheme leaves `importlib.metadata` unimported."""
    code = (
        "import sys, bip39_slip39.bip39;sys.exit('importlib.metadata' in sys.modules)"
    )
    result = subprocess.run(  # noqa: S603
        [sys.executable, "-c", code], check=False
    )
    assert result.returncode == 0
