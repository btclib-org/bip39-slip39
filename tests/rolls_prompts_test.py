# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Tests for the languages of `entropy.collect_rolls`' prompts.

Every language goes through the one set of checks in `entropy.py`
(`_rolls_prompts.py` says why), and these tests drive each of them
through the same scripts as English.
"""

import string
from io import StringIO

import pytest

from bip39_slip39._rolls_prompts import ROLLS_PROMPTS
from bip39_slip39.entropy import collect_rolls
from bip39_slip39.exceptions import (
    Bip39Slip39TypeError,
    Bip39Slip39ValueError,
)
from bip39_slip39.mnemonic import BIP39_LANGUAGE_FILES

_LANGS = sorted(ROLLS_PROMPTS)


def _fields(template: str) -> set[str]:
    """Return the names of the placeholders of a template."""
    return {
        name for _, name, _, _ in string.Formatter().parse(template) if name is not None
    }


def test_every_word_list_language_has_prompts() -> None:
    """The prompts are in each language the BIP39 word lists are in."""
    assert set(ROLLS_PROMPTS) == set(BIP39_LANGUAGE_FILES)


@pytest.mark.parametrize("lang", _LANGS)
@pytest.mark.parametrize("name", ROLLS_PROMPTS["en"]._fields)
def test_placeholders_match_english(lang: str, name: str) -> None:
    """A text has the placeholders of English's, no more and no fewer."""
    text = getattr(ROLLS_PROMPTS[lang], name)
    assert _fields(text) == _fields(getattr(ROLLS_PROMPTS["en"], name))
    assert _fields(text)


@pytest.mark.parametrize("lang", _LANGS)
def test_dice_sides_text_names_the_answers_it_accepts(lang: str) -> None:
    """The ASCII "a", and the "6" Enter stands for, are in the text, quoted."""
    text = ROLLS_PROMPTS[lang].dice_sides
    assert "'a'" in text
    assert "'6'" in text


@pytest.mark.parametrize("lang", _LANGS)
def test_every_language_goes_through_the_same_checks(
    lang: str, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Each language refuses and accepts what English does.

    The script offers a dice that does not exist, an underscore, a
    fullwidth "30", an Arabic-Indic digit, a sign, a negative, a zero and
    a roll above the usable base, and "5" followed by an ideographic
    space, before the usable roll. D30's usable base is 16.
    """
    answers = [
        "3",
        "1_2",
        "\N{FULLWIDTH DIGIT THREE}\N{FULLWIDTH DIGIT ZERO}",
        "30",
        "\N{ARABIC-INDIC DIGIT FIVE}",
        "+5",
        "-1",
        "0",
        "17",
        "5\N{IDEOGRAPHIC SPACE}",
        " 5\t",
    ]
    monkeypatch.setattr("sys.stdin", StringIO("".join(f"{a}\n" for a in answers)))
    assert collect_rolls(4, lang) == (30, [5])
    out = capsys.readouterr().out
    prompts = ROLLS_PROMPTS[lang]
    assert prompts.usable.format(base=16) in out
    assert prompts.roll.format(n=1, total=1) in out
    assert prompts.collected.format(total=1, sides=30) in out


@pytest.mark.parametrize("lang", _LANGS)
def test_every_language_automates_with_the_ascii_a(
    lang: str, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """An ASCII "a" automates the rolls in any language, a lookalike not."""
    monkeypatch.setattr("sys.stdin", StringIO("\N{CYRILLIC SMALL LETTER A}6\na6\n"))
    dice_sides, rolls = collect_rolls(8, lang)
    assert dice_sides == 6
    assert len(rolls) == 4
    assert all(0 < roll <= 4 for roll in rolls)
    out = capsys.readouterr().out
    assert ROLLS_PROMPTS[lang].usable.format(base=4) not in out
    assert ROLLS_PROMPTS[lang].collected.format(total=4, sides=6) in out


def test_english_is_the_default_and_its_text_is_unchanged(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Without a language the prompts are the English ones, word for word."""
    monkeypatch.setattr("sys.stdin", StringIO("4\n1\n1\n"))
    assert collect_rolls(4) == (4, [1, 1])
    assert capsys.readouterr().out == (
        "dice sides (4, 6, 8, 12, 20, 24, 30, 48, 60, 120; "
        "prefix with 'a' to automate rolls, hit enter for '6'): "
        "rolls are used only if in 1..4\n"
        "roll #1/2: roll #2/2: "
        "collected 2 usable D4 rolls\n"
    )


@pytest.mark.parametrize("lang", ["slip39", "xx", ""])
def test_an_unknown_language_is_refused(lang: str) -> None:
    """A language without prompts is refused before anything is asked."""
    with pytest.raises(Bip39Slip39ValueError, match="no prompts in language"):
        collect_rolls(4, lang)


@pytest.mark.parametrize("lang", [None, 1, b"en"])
def test_a_language_that_is_no_string_is_refused(lang: object) -> None:
    """A language of another type is the caller's mistake."""
    with pytest.raises(Bip39Slip39TypeError, match="lang"):
        collect_rolls(4, lang)  # type: ignore[arg-type]
