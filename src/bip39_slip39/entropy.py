# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Entropy conversion functions.

Depending on the function, input entropy can be expressed as raw (i.e.
binary 0/1 string), bytes, or integer and their equivalent
representations.

Leading zeros in raw or bytes entropy are never considered redundant
padding.

Output entropy is always raw.

The public surface is the entropy sources -- dice rolls, read
interactively or given, and the CSPRNG -- and the types they are written
in. The conversions between the representations are private: BIP39
and Electrum call them, and a caller holding entropy hands it to a
scheme's `mnemonic_from_entropy` rather than converting it first.
"""

from __future__ import annotations

import math
import secrets
import string
from collections.abc import Iterable, Sequence

from bip39_slip39._rolls_prompts import ROLLS_PROMPTS
from bip39_slip39._utils import Octets, assert_type, bytes_from_octets, is_integer
from bip39_slip39.exceptions import (
    BTClibMnemonicsTypeError,
    BTClibMnemonicsValueError,
)

__all__ = [
    "BinStr",
    "Entropy",
    "OneOrMoreInt",
    "bin_str_entropy_from_random",
    "bin_str_entropy_from_rolls",
    "collect_rolls",
]

_bits = 128, 160, 192, 224, 256, 512

# the main internal representation of entropy is binary 0/1 string
BinStr = str
# but int or bytes are fine too
Entropy = BinStr | int | bytes


def _bits_per_digit(base: int) -> int:
    """Return the whole bits one digit of that base holds, floor(log2).

    In integer arithmetic, where `math.floor(math.log2(base))` is the
    obvious spelling and is the one that is wrong at the edge: the float
    stops being exact at 2**49 - 1, where `log2` rounds up to 49 and the
    caller then reads one bit more per digit than the base holds -- a
    roll a die does not have, counted as usable.

        math.floor(math.log2(2**49 - 1))  # 49
        (2**49 - 1).bit_length() - 1      # 48

    `_bin_str_entropy_from_wordlist_indexes` computes its own width the
    same integer way.
    """
    return base.bit_length() - 1


def _is_ascii_digits(text: str, digits: str) -> bool:
    """Return True for a non-empty string of those ASCII digits alone.

    `int(text, base)` reads more than digits: the digit-grouping
    underscore of Python's number literals, a sign, the prefix of its own
    base, whitespace around them, U+3000 among it, and every Unicode
    decimal digit, U+0661 (ARABIC-INDIC ONE) as readily as "1". Each is a
    second spelling of one number, and so of one seed, which is why the
    text is checked here before `int` reads it.
    """
    return bool(text) and all(c in digits for c in text)


def _small_int(text: str, max_digits: int) -> int:
    """Return the number up to `max_digits` ASCII decimal digits spell, else 0.

    Bounded before `int` reads it: `int` refuses a decimal string over
    4300 digits with a ValueError, which would end an interactive prompt
    instead of asking again. Every caller refuses 0.
    """
    if len(text) > max_digits or not _is_ascii_digits(text, string.digits):
        return 0
    return int(text)


def _int_from_bin_str(entropy: BinStr) -> int:
    """Return the number a binary 0/1 string spells, or refuse the string.

    Only ASCII "0" and "1" are digits of it, as `_is_ascii_digits` says;
    what is no string at all is refused too, bytes and bytearray
    included, which `int(x, 2)` reads as the digits they spell.

    The refusal does not carry the value: raw entropy is seed material,
    and every error in this module says a length or a count and never
    the digits (issue btclib-org/btclib#137).
    """
    assert_type(entropy, str, "entropy")
    if not _is_ascii_digits(entropy, "01"):
        raise BTClibMnemonicsValueError("invalid entropy: not a binary 0/1 string")
    return int(entropy, 2)


def _wordlist_indexes_from_bin_str_entropy(entropy: BinStr, base: int) -> list[int]:
    """Return the digit indexes for the provided raw entropy.

    Return the list of integer indexes into a digit set, usually a
    language word-list, for the provided raw (i.e. binary 0/1 string)
    entropy; leading zeros are not considered redundant padding.
    """
    int_entropy = _int_from_bin_str(entropy)
    bits = len(entropy)
    indexes = []
    while int_entropy:
        int_entropy, index = divmod(int_entropy, base)
        indexes.append(index)

    # do not lose leading zeros entropy
    bits_per_digit = _bits_per_digit(base)
    nwords = math.ceil(bits / bits_per_digit)
    indexes += [0] * (nwords - len(indexes))

    return list(reversed(indexes))


def _bin_str_entropy_from_wordlist_indexes(indexes: Sequence[int], base: int) -> BinStr:
    """Return the raw entropy from a list of word-list indexes.

    Return the raw (i.e. binary 0/1 string) entropy from the provided
    list of integer indexes into a given language word-list.

    An index the word list has no word for is refused rather than
    carried: base-`base` arithmetic accepts any number as a digit, so
    2048 in a 2048-word list is not an error but a carry into the digit
    above it -- entropy nothing spells, out of a function whose whole
    job is to say what a mnemonic means. The refusal names the bound and
    not the index, which with the wrong `base` is a word of the mnemonic.
    """
    entropy = 0
    for index in indexes:
        if not is_integer(index):
            raise BTClibMnemonicsTypeError(
                f"invalid index type: {type(index).__name__}"
            )
        if not 0 <= index < base:
            raise BTClibMnemonicsValueError(f"invalid index: not in [0, {base})")
        entropy = entropy * base + index

    binentropy = f"{entropy:b}"

    # do not lose leading zeros entropy. The width is that of the largest
    # value the digits can spell, in integer arithmetic: for a base that
    # is a power of two that is `_bits_per_digit` times the digit count,
    # and for electrum's 1626-word Portuguese -- 10.667 bits a word -- it
    # is the 139 bits thirteen words hold rather than the 130 that
    # rounding down claims
    bits = (base ** len(indexes) - 1).bit_length()
    return binentropy.zfill(bits)


OneOrMoreInt = int | Iterable[int]


def _bin_str_entropy_from_entropy(entr: Entropy, bits: OneOrMoreInt) -> BinStr:
    """Return raw entropy from the input entropy.

    Input entropy can be expressed as:

    - raw (i.e. binary 0/1 string) entropy
    - bytes (no hex-string, as they would conflict with
      raw entropy representation)
    - integer (int)

    In the case of raw entropy and bytes,
    entropy is never padded to satisfy the bit-size requirement;
    instead,
    integer entropy is front-padded with zeros digits
    as much as necessary to satisfy the bit-size requirement.

    In all cases more bits than the largest allowed are refused: the
    leftmost ones of an integer, which has no leading zeros, would be
    biased towards a leading 1.

    electrum passes `_bits` (128, 160, 192, 224, 256 or 512), and bip39
    its own `_ENTROPY_BITS`.
    """
    if isinstance(entr, str):
        return _bin_str_entropy_from_str(entr, bits)
    if isinstance(entr, int):
        return _bin_str_entropy_from_int(entr, bits)
    # must be bytes-like
    return _bin_str_entropy_from_bytes(entr, bits)


def _bin_str_entropy_from_bytes(bytes_entropy: Octets, bits: OneOrMoreInt) -> BinStr:
    """Return raw entropy from the input Octets entropy.

    Input entropy can be expressed as hex-string or bytes; it is never
    padded to satisfy the bit-size requirement.

    More bits than the largest allowed are refused.
    """
    bytes_entropy = bytes_from_octets(bytes_entropy)

    # if a single int, make it a tuple
    if isinstance(bits, int):
        bits = (bits,)
    # ascending unique sorting of allowed bits
    bits = sorted(set(bits))

    n_bits = len(bytes_entropy) * 8
    if n_bits not in bits:
        err_msg = f"invalid number of bits: {n_bits} instead of {bits}"
        raise BTClibMnemonicsValueError(err_msg)

    int_entropy = int.from_bytes(bytes_entropy, byteorder="big", signed=False)
    return _bin_str_entropy_from_int(int_entropy, n_bits)


def _bytes_entropy_from_str(bin_str_entropy: BinStr) -> bytes:
    """Return the binary-string entropy as bytes, left-padded to whole ones."""
    int_entropy = _int_from_bin_str(bin_str_entropy)
    nbytes = (len(bin_str_entropy) + 7) // 8
    return int_entropy.to_bytes(nbytes, byteorder="big", signed=False)


def _bin_str_entropy_from_int(int_entropy: int, bits: OneOrMoreInt) -> BinStr:
    """Return raw entropy from the input integer entropy.

    It is front-padded with zeros digits as much as necessary to
    satisfy the bit-size requirement. More bits than the largest
    allowed are refused.
    """
    if int_entropy < 0:
        raise BTClibMnemonicsValueError("negative entropy")

    # if a single int, make it a tuple
    if isinstance(bits, int):
        bits = (bits,)
    # ascending unique sorting of allowed bits
    bits = sorted(set(bits))

    # convert to binary string
    bin_str = f"{int_entropy:b}"
    n_bits = len(bin_str)
    if n_bits > bits[-1]:
        err_msg = f"invalid number of bits: {n_bits} instead of at most {bits[-1]}"
        raise BTClibMnemonicsValueError(err_msg)

    # pad up to the next allowed bit length
    n_bits = next(v for v in bits if v >= n_bits)
    return bin_str.zfill(n_bits)


def _bin_str_entropy_from_str(str_entropy: str, bits: OneOrMoreInt) -> BinStr:
    """Return raw entropy from the input raw entropy.

    Input entropy must be expressed as raw entropy; it is never padded
    to satisfy the bit-size requirement.

    More bits than the largest allowed are refused.
    """
    _int_from_bin_str(str_entropy)

    # if a single int, make it a tuple
    if isinstance(bits, int):
        bits = (bits,)
    # ascending unique sorting of allowed bits
    bits = sorted(set(bits))

    n_bits = len(str_entropy)
    if n_bits not in bits:
        err_msg = f"invalid number of bits: {n_bits} instead of {bits}"
        raise BTClibMnemonicsValueError(err_msg)
    return str_entropy


def collect_rolls(bits: int, lang: str = "en") -> tuple[int, list[int]]:
    """Prompt for dice rolls until they carry `bits` of entropy.

    Interactive on purpose, input() and print() being its interface:
    the caller gets (dice sides, the rolls that count). Rolls beyond
    a power of two are discarded and asked again, carrying no whole
    bits, and so is an answer that is not one to three ASCII decimal
    digits once ASCII whitespace is stripped.

    The prompts are in `lang`, a key of `mnemonic.BIP39_LANGUAGE_FILES`:
    pass the language the mnemonic is to be written in, as
    `bip39.mnemonic_from_entropy` takes it. Any other language is
    refused. The terminal must be able to show that language's script.
    Only the texts differ between languages: `_rolls_prompts.py` says
    what is accepted in all of them.
    The translations were made and checked with AI.

    Enter alone asks for a D6 rolled by hand, so that the default
    collects entropy from dice. Automated rolls, asked for with 'a', come
    from `secrets`, and must: a reproducible source of rolls is what the
    entropy of a seed that does not exist yet must never be.
    """
    assert_type(lang, str, "lang")
    if lang not in ROLLS_PROMPTS:
        raise BTClibMnemonicsValueError(
            f"no prompts in language {lang!r}: one of {sorted(ROLLS_PROMPTS)}"
        )
    prompts = ROLLS_PROMPTS[lang]

    automate = False
    dice_sides = 0
    valid_dice_sides = (4, 6, 8, 12, 20, 24, 30, 48, 60, 120)
    while dice_sides not in valid_dice_sides:
        dice_sides_str = input(
            prompts.dice_sides.format(choices=", ".join(map(str, valid_dice_sides)))
        )
        dice_sides_str = dice_sides_str.lower()
        if dice_sides_str in {"", "a"}:
            dice_sides_str += "6"
        automate = dice_sides_str.startswith("a")
        if automate:
            dice_sides_str = dice_sides_str[1:]
        dice_sides_str = dice_sides_str.strip(string.whitespace)
        dice_sides = _small_int(dice_sides_str, 3)

    bits_per_roll = _bits_per_digit(dice_sides)
    base = 2**bits_per_roll
    if not automate:
        print(prompts.usable.format(base=base))

    rolls: list[int] = []
    min_roll_number = math.ceil(bits / bits_per_roll)
    for i in range(min_roll_number):
        roll = 0
        while not 0 < roll <= base:
            if automate:
                roll_str = str(1 + secrets.randbelow(dice_sides))
            else:
                roll_str = input(prompts.roll.format(n=i + 1, total=min_roll_number))
                roll_str = roll_str.strip(string.whitespace)
            roll = _small_int(roll_str, 3)
        rolls.append(roll)
    print(prompts.collected.format(total=min_roll_number, sides=dice_sides))

    return dice_sides, rolls


def _assert_rolls(rolls: object) -> None:
    """Refuse anything but a sequence of integer rolls.

    A sequence is what holds every roll in the order rolled: a set would
    have dropped the repeated ones before reaching here.
    """
    if not isinstance(rolls, Sequence):
        raise BTClibMnemonicsTypeError(f"invalid rolls type: {type(rolls).__name__}")
    for roll in rolls:
        if not is_integer(roll):
            raise BTClibMnemonicsTypeError(f"invalid roll type: {type(roll).__name__}")


def bin_str_entropy_from_rolls(
    bits: int, dice_sides: int, rolls: Sequence[int]
) -> BinStr:
    """Return raw entropy from the input dice rolls.

    Dice rolls are represented by integers in the [1-dice_sides] range;
    there must be enough rolls to satisfy the bit-size requirement. The
    rolls are a sequence, a list or a tuple, read in the order rolled, so
    the same rolls always give the same entropy.

    Only rolls having value in the [1-base] range are used, with base
    being the highest power of 2 that is lower than the dice_sides (e.g.
    for a traditional D6 dice, only rolls having value in [1-4] are
    used; for a D20 dice, only rolls having value in [1-16] are used;
    etc.). Each used roll is the digit roll - 1 in that base.

    If more bits than required are provided, the leftmost ones of the
    rolls' own width, leading zeros included, are retained.
    """
    if not is_integer(bits):
        raise BTClibMnemonicsTypeError(f"invalid bits type: {type(bits).__name__}")
    # `_bits_per_digit` below takes `base.bit_length()`, which a float
    # has no method named, so a caller passing 6.0 would hear a bare
    # AttributeError rather than this module's own message
    if not is_integer(dice_sides):
        err_msg = f"invalid dice base type: {type(dice_sides).__name__}"
        raise BTClibMnemonicsTypeError(err_msg)
    _assert_rolls(rolls)
    if dice_sides < 2:
        raise BTClibMnemonicsValueError(
            f"invalid dice base: {dice_sides}, must be >= 2"
        )
    bits_per_roll = _bits_per_digit(dice_sides)
    # used base
    base = 2**bits_per_roll

    min_roll_number = math.ceil(bits / bits_per_roll)
    n_used = 0
    i = 0
    for roll in rolls:
        # reject invalid rolls not in [1-dice_sides], naming the bound and
        # not the roll, which with the wrong `dice_sides` is a real one
        if not 0 < roll <= dice_sides:
            raise BTClibMnemonicsValueError(f"invalid roll: not in [1-{dice_sides}]")

        # collect only usable rolls in [1-base]
        if 0 < roll <= base:
            i *= base
            i += roll - 1
            n_used += 1
            min_roll_number -= 1
    if min_roll_number > 0:
        msg = f"too few rolls in the usable [1-{base}] range"
        msg += f", missing {min_roll_number} rolls"
        raise BTClibMnemonicsValueError(msg)

    # the leftmost bits of what was rolled, not of the number it spells:
    # that has no leading zeros, and its first bit would be a 1 far more
    # often than not
    return f"{i:0{n_used * bits_per_roll}b}"[:bits]


def bin_str_entropy_from_random(bits: int) -> BinStr:
    """Return `bits` of raw entropy drawn from the system CSPRNG, `secrets`."""
    if not is_integer(bits):
        raise BTClibMnemonicsTypeError(f"invalid bits type: {type(bits).__name__}")
    if bits < 1:
        raise BTClibMnemonicsValueError(f"invalid number of bits: {bits}, must be >= 1")
    # at its own width: the number drawn has no leading zeros
    return f"{secrets.randbits(bits):0{bits}b}"
