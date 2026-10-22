# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Tests for `python -m btclib_mnemonics`, the `__main__` module."""

from __future__ import annotations

import runpy
from collections.abc import Iterator
from hashlib import sha256
from pathlib import Path

import pytest

import btclib_mnemonics.__main__ as main
from btclib_mnemonics import bip39, slip39

_MAIN = "btclib_mnemonics.__main__"

# the vector: two contributors' D6 rolls, 50 each for 128 bits, and R
_ROLLS_1 = [1, 2, 3, 4, 5, 6] * 8 + [1, 2]
_ROLLS_2 = [6, 5, 4, 3, 2, 1] * 8 + [6, 5]
_R = bytes(range(32))
_COMMITMENT = "630dcd2966c4336691125448bbb25b4ff412a49c732db2c8abc1b8581bd710dd"
_ENTROPY = "dbe61cbdb00fa79d6ffeb01ab203602f"
_MNEMONIC = "swim couch control gas whip solid say stock boy mosquito submit game"


def _lines(rolls: list[int], per_line: int) -> list[str]:
    """Return the rolls as typed, `per_line` to a line."""
    return [
        " ".join(map(str, rolls[i : i + per_line]))
        for i in range(0, len(rolls), per_line)
    ]


def _answer(monkeypatch: pytest.MonkeyPatch, getpass_lines: list[str]) -> None:
    """Draw R as the vector's, type the lines unseen, and press Enter."""
    typed: Iterator[str] = iter(getpass_lines)
    monkeypatch.setattr(f"{_MAIN}.secrets.token_bytes", lambda _: _R)
    monkeypatch.setattr(f"{_MAIN}.getpass.getpass", lambda _: next(typed))
    monkeypatch.setattr("builtins.input", lambda _: "")


def test_the_vector_recomputes_with_hashlib_alone() -> None:
    """The entropy is sha256(rolls_1 || rolls_2 || R), one byte per roll."""
    assert sha256(_R).hexdigest() == _COMMITMENT
    data = bytes(_ROLLS_1) + bytes(_ROLLS_2) + _R
    assert sha256(data).digest()[:16].hex() == _ENTROPY
    assert main._entropy(128, [_ROLLS_1, _ROLLS_2], _R).hex() == _ENTROPY
    assert bip39.mnemonic_from_entropy(bytes.fromhex(_ENTROPY)) == _MNEMONIC


@pytest.mark.parametrize(
    "bits, sides, rolls",
    [(256, 6, 100), (128, 6, 50), (256, 2, 256), (256, 4, 128), (256, 255, 33)],
)
def test_every_face_counts(bits: int, sides: int, rolls: int) -> None:
    """The fewest rolls whose outcomes reach 2**bits, and not one fewer."""
    assert main._rolls_needed(bits, sides) == rolls
    assert sides**rolls >= 2**bits > sides ** (rolls - 1)


def test_bip39_shows_the_commitment_r_and_the_mnemonic(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Two contributors: the commitment first, then R, then the mnemonic."""
    _answer(monkeypatch, _lines(_ROLLS_1, 6) + _lines(_ROLLS_2, 50))
    argv = ["bip39", "--bits", "128", "--contributors", "2"]
    assert main._main(argv) == 0
    out = capsys.readouterr().out
    assert out.index(_COMMITMENT) < out.index(_R.hex()) < out.index(_MNEMONIC)
    assert f"{main._CLEAR}1 of 1:\n\n{_MNEMONIC}\n" in out


def test_slip39_shows_each_share_on_a_cleared_screen(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Each share is alone between two clears, and two recover the entropy."""
    _answer(monkeypatch, _lines(_ROLLS_1, 50))
    argv = ["slip39", "--bits", "128", "--groups", "2-of-3"]
    assert main._main(argv) == 0
    screens = capsys.readouterr().out.split(main._CLEAR)
    shares = [screen.split("\n\n")[1].strip() for screen in screens[1::2]]
    assert len(shares) == 3
    # nothing is printed between a share's closing clear and the next one's
    assert screens[2::2] == ["", "", ""]
    expected = sha256(bytes(_ROLLS_1) + _R).digest()[:16]
    assert slip39.master_secret_from_mnemonics(shares[1:]) == expected


def test_a_line_is_refused_whole_and_unseen(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """A bad roll, a roll too many or a non-digit refuses its whole line."""
    lines = [
        "",
        "1 7",
        "1 x",
        "1 \N{FULLWIDTH DIGIT TWO}",
        "0",
        "1 2 3 4",
        "2\t3 ",
        "4",
    ]
    typed = iter(lines)
    monkeypatch.setattr(f"{_MAIN}.getpass.getpass", lambda _: next(typed))
    assert main._read_rolls(1, 1, 3, 6) == [2, 3, 4]
    out = capsys.readouterr().out
    assert out.count("line refused: rolls from 1 to 6, at most 3 more") == 5
    assert "7" not in out
    assert "x" not in out


def test_a_roll_too_long_for_int_is_refused(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Over 4300 digits `int` raises; the line is refused and typed again."""
    typed = iter(["9" * 5000, "006", "1"])
    monkeypatch.setattr(f"{_MAIN}.getpass.getpass", lambda _: next(typed))
    assert main._read_rolls(1, 1, 1, 6) == [6]
    assert capsys.readouterr().out.count("line refused") == 1


def test_the_scrollback_is_cleared_after_the_screen() -> None:
    """A terminal may push the cleared screen into the scrollback.

    So `3J`, which erases the scrollback, comes after `2J`, as ncurses'
    `clear` sends them.
    """
    assert main._CLEAR == "\033[H\033[2J\033[3J"


@pytest.mark.parametrize("stop", [EOFError, KeyboardInterrupt])
def test_an_interruption_clears_the_screen(
    stop: type[BaseException],
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """End of input or Ctrl-C, while a share is shown, exits 1 and clears it."""
    answers = iter(["", ""])

    def enter(_: str) -> str:
        try:
            return next(answers)
        except StopIteration:
            raise stop from None

    _answer(monkeypatch, _lines(_ROLLS_1, 50))
    monkeypatch.setattr("builtins.input", enter)
    assert main._main(["slip39", "--bits", "128", "--groups", "2-of-3"]) == 1
    assert capsys.readouterr().out.endswith(f"{main._CLEAR}interrupted\n")


@pytest.mark.parametrize(
    "argv",
    [
        ["bip39", "--contributors", "0"],
        ["bip39", "--sides", "1"],
        ["bip39", "--sides", "256"],
        ["bip39", "--bits", "512"],
        ["slip39", "--groups", "2of3"],
        ["slip39", "--groups", "1-of-3"],
        ["slip39", "--groups", "2-of-3", "--group-threshold", "2"],
        [],
    ],
)
def test_a_bad_command_line_is_refused_before_anybody_rolls(
    argv: list[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Exit 2, argparse's, before R is drawn."""
    drawn: list[int] = []
    monkeypatch.setattr(f"{_MAIN}.secrets.token_bytes", drawn.append)
    with pytest.raises(SystemExit) as excinfo:
        main._main(argv)
    assert excinfo.value.code == 2
    assert not drawn


def test_python_dash_m_runs_the_command(monkeypatch: pytest.MonkeyPatch) -> None:
    """The `__main__` guard hands the command line to `_main`."""
    monkeypatch.setattr("sys.argv", ["btclib_mnemonics", "--help"])
    with pytest.raises(SystemExit) as excinfo:
        runpy.run_path(str(Path(main.__file__)), run_name="__main__")
    assert excinfo.value.code == 0
