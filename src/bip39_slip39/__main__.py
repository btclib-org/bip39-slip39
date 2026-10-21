# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""`python -m bip39_slip39`: dice to a mnemonic with a recomputable seed.

The README's *Dice to a mnemonic* says what the command does and how
to recompute its seed with `hashlib` alone. A BIP39 mnemonic is shown
whole because splitting its words splits nothing: half of 12 words
leaves about 62 bits to search. SLIP-0039 is the way to split a secret.
"""

from __future__ import annotations

import argparse
import getpass
import re
import secrets
import string
import sys
from collections.abc import Sequence
from hashlib import sha256

from bip39_slip39 import bip39, slip39
from bip39_slip39.entropy import _small_int
from bip39_slip39.exceptions import (
    Bip39Slip39TypeError,
    Bip39Slip39ValueError,
)
from bip39_slip39.mnemonic import BIP39_LANGUAGE_FILES

__all__: list[str] = []

_RANDOM_BYTES = 32

# a roll is one byte, so a die has at most 255 faces
_MAX_SIDES = 255

_BIP39_BITS = (128, 160, 192, 224, 256)
# SLIP-0039 takes multiples of 16 bits from 128; sha256 gives 256 at most
_SLIP39_BITS = tuple(range(128, 257, 16))

# move home, clear the screen, then clear the scrollback: a terminal that
# pushes the cleared screen into the scrollback has it erased there too
_CLEAR = "\033[H\033[2J\033[3J"

_ASCII_WHITESPACE = re.compile(f"[{re.escape(string.whitespace)}]+")
_GROUP = re.compile(r"([0-9]+)-of-([0-9]+)")


def _entropy(bits: int, rolls: Sequence[Sequence[int]], random: bytes) -> bytes:
    """Return the entropy the README's *Dice to a mnemonic* defines."""
    data = b"".join(bytes(contributor) for contributor in rolls) + random
    return sha256(data).digest()[: bits // 8]


def _rolls_needed(bits: int, sides: int) -> int:
    """Return the fewest rolls of a die of `sides` faces with 2**bits outcomes.

    Every face counts, so a D6 gives log2(6) bits a roll: 100 rolls for
    256 bits.
    """
    outcomes = 2**bits
    rolls = 0
    while sides**rolls < outcomes:
        rolls += 1
    return rolls


def _read_rolls(
    contributor: int, contributors: int, count: int, sides: int
) -> list[int]:
    """Read one contributor's rolls without echo, refusing a bad line whole.

    A line holds rolls separated by ASCII whitespace. A line with a roll
    that is not at most three ASCII digits from 1 to `sides`, or with more
    rolls than are still missing, is refused without being shown and is
    typed again.
    """
    rolls: list[int] = []
    while len(rolls) < count:
        prompt = f"contributor {contributor} of {contributors}, "
        prompt += f"{len(rolls)} of {count} rolls typed: "
        tokens = [t for t in _ASCII_WHITESPACE.split(getpass.getpass(prompt)) if t]
        line = [_small_int(t, len(str(_MAX_SIDES))) for t in tokens]
        if all(1 <= roll <= sides for roll in line) and len(rolls) + len(line) <= count:
            rolls += line
        else:
            print(
                f"line refused: rolls from 1 to {sides}, "
                f"at most {count - len(rolls)} more; type it again"
            )
    return rolls


def _group(text: str) -> tuple[int, int]:
    """Parse a SLIP-0039 group given as `<threshold>-of-<count>`."""
    match = _GROUP.fullmatch(text)
    if match is None:
        raise argparse.ArgumentTypeError(f"not <threshold>-of-<count>: {text!r}")
    return int(match[1]), int(match[2])


def _parser() -> argparse.ArgumentParser:
    """Return the command's argument parser."""
    parser = argparse.ArgumentParser(
        prog="python -m bip39_slip39",
        description="Dice to a mnemonic whose seed can be recomputed offline.",
    )
    schemes = parser.add_subparsers(dest="scheme", required=True)
    for name, bits in (("bip39", _BIP39_BITS), ("slip39", _SLIP39_BITS)):
        scheme = schemes.add_parser(name)
        scheme.add_argument(
            "--bits",
            type=int,
            choices=bits,
            default=bits[-1],
            help=f"entropy bits (default: {bits[-1]})",
        )
        scheme.add_argument(
            "--contributors",
            type=int,
            default=1,
            help="how many people roll, each the whole count (default: 1)",
        )
        scheme.add_argument(
            "--sides", type=int, default=6, help="faces of the die (default: 6)"
        )
        if name == "bip39":
            scheme.add_argument(
                "--lang", choices=sorted(BIP39_LANGUAGE_FILES), default="en"
            )
        else:
            scheme.add_argument(
                "--groups",
                type=_group,
                nargs="+",
                default=[(1, 1)],
                metavar="T-of-N",
                help="one per group (default: 1-of-1)",
            )
            scheme.add_argument("--group-threshold", type=int, default=1)
    return parser


def _mnemonics(args: argparse.Namespace, entropy: bytes) -> list[str]:
    """Return what is shown on its own screen: one share, or the mnemonic."""
    if args.scheme == "bip39":
        return [bip39.mnemonic_from_entropy(entropy, args.lang)]
    groups = slip39.mnemonics_from_master_secret(
        entropy, args.groups, args.group_threshold
    )
    return [share for group in groups for share in group]


def _show(mnemonics: list[str]) -> None:
    """Show each mnemonic on a cleared screen, cleared once written down."""
    for i, mnemonic in enumerate(mnemonics, 1):
        input(f"press Enter to show {i} of {len(mnemonics)} ")
        print(_CLEAR, end="", flush=True)
        print(f"{i} of {len(mnemonics)}:\n\n{mnemonic}\n")
        input("press Enter once it is written down ")
        print(_CLEAR, end="", flush=True)


def _main(argv: Sequence[str]) -> int:
    """Run the command on `argv`, the arguments after the program name."""
    parser = _parser()
    args = parser.parse_args(argv)
    if args.contributors < 1:
        parser.error("--contributors: at least 1")
    if not 2 <= args.sides <= _MAX_SIDES:
        parser.error(f"--sides: from 2 to {_MAX_SIDES}")
    # the shares' layout is refused here, before anybody rolls: a dry run
    # over a zero secret, which nothing shows
    try:
        _mnemonics(args, bytes(args.bits // 8))
    except (Bip39Slip39TypeError, Bip39Slip39ValueError) as err:
        parser.error(str(err))

    try:
        _run(args)
    except (EOFError, KeyboardInterrupt):
        # a share may be on the screen
        print(f"{_CLEAR}interrupted")
        return 1
    return 0


def _run(args: argparse.Namespace) -> None:
    """Commit to R, collect the rolls, reveal R and show the mnemonics."""
    count = _rolls_needed(args.bits, args.sides)
    random = secrets.token_bytes(_RANDOM_BYTES)
    print(f"commitment, sha256(R): {sha256(random).hexdigest()}")
    input("write it down, then press Enter ")
    print(f"each contributor types {count} rolls of a D{args.sides}, unseen")
    rolls = [
        _read_rolls(c, args.contributors, count, args.sides)
        for c in range(1, args.contributors + 1)
    ]
    print(f"R: {random.hex()}")
    print("check that sha256(R) is the commitment, and write R down:")
    print("R and every contributor's rolls recompute the seed")
    _show(_mnemonics(args, _entropy(args.bits, rolls, random)))


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
