# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""SLIP-0039 share / master secret / seed functions.

https://github.com/satoshilabs/slips/blob/master/slip-0039.md.

Shamir backup, the scheme every Trezor since 2019 offers. A master
secret is split into *shares*, of which a threshold number is required
to put it back together; fewer than that leak nothing about it. The
master secret is the BIP32 seed itself, not entropy to be stretched
into one, so what ``master_secret_from_mnemonics`` returns is the seed a
BIP32 root key is derived from.

The split is two-level. The master secret is encrypted under the
passphrase, the result split ``GT``-of-``G`` into *group* shares, and
each group share split ``T``-of-``N`` into the *member* shares people
actually hold. A plain ``T``-of-``N`` backup is the degenerate case:
one group, split at the member level.

Four pieces underneath, none of them shared with BIP39:

* Shamir's scheme over GF(256), applied byte by byte, with the secret
  at ``f(255)`` and a digest of it at ``f(254)`` so that a wrong set of
  shares is caught rather than silently reconstructing rubbish
* an RS1024 checksum over the 10-bit word indexes, three words long
* a two-level group/member threshold structure, four bits per index and
  per threshold, which is what caps both at 16
* a four-round Feistel network with PBKDF2-HMAC-SHA256 as the round
  function, encrypting the master secret under the passphrase

The word-list is SLIP-0039's own 1024 words, ten bits each; it is not
BIP39's, and no localization exists.

+----------+---------------------------+---------------------+
| Security | Padded share value length | Total share length  |
+==========+===========================+=====================+
| 128 bits | 130 bits                  | 200 bits = 20 words |
+----------+---------------------------+---------------------+
| 256 bits | 260 bits                  | 330 bits = 33 words |
+----------+---------------------------+---------------------+

Both recovery and generation are here. Recovery alone is what a wallet
needs and what several implementations stop at; a library is asked the
other question too -- and generation is also what lets the round trip
be tested against something other than itself.

Each direction has a step in the middle, the ``EncryptedMasterSecret``:
``encrypted_master_secret_from_mnemonics`` recombines shares into it and
``mnemonics_from_encrypted_master_secret`` splits it into new ones, so a
backup is regrouped without the passphrase and without PBKDF2.
``Recovery`` collects shares one mnemonic at a time, as a user types them.
"""

from __future__ import annotations

import hmac
import os
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from hashlib import pbkdf2_hmac, sha256

from bip39_slip39._utils import Octets, assert_type, bytes_from_octets, is_integer
from bip39_slip39.exceptions import (
    Bip39Slip39TypeError,
    Bip39Slip39ValueError,
)
from bip39_slip39.mnemonic import (
    WORDLISTS,
    Mnemonic,
    indexes_from_mnemonic,
    mnemonic_from_indexes,
)

__all__ = [
    "EncryptedMasterSecret",
    "Recovery",
    "Share",
    "encrypted_master_secret_from_mnemonics",
    "master_secret_from_mnemonics",
    "mnemonic_from_share",
    "mnemonics_from_encrypted_master_secret",
    "mnemonics_from_master_secret",
    "share_from_mnemonic",
]

# the key of the SLIP-0039 word-list in WORDLISTS; a scheme and not a
# language code, SLIP-0039 having no localization at all
_LANG = "slip39"

_RADIX_BITS = 10

# the share layout in bits: id || ext || e || GI || Gt || g || I || t,
# then the padded share value, then the checksum
_ID_BITS = 15
_EXT_BITS = 1
_E_BITS = 4
_MAX_EXPONENT = (1 << _E_BITS) - 1
# each of the group index, group threshold, group count, member index
# and member threshold; four bits is what caps G and N at 16
_FIELD_BITS = 4
_HEADER_BITS = _ID_BITS + _EXT_BITS + _E_BITS + 5 * _FIELD_BITS
_CHECKSUM_WORDS = 3
_CHECKSUM_BITS = _CHECKSUM_WORDS * _RADIX_BITS

_MAX_SHARE_COUNT = 1 << _FIELD_BITS

# the master secret must be at least 128 bits and a multiple of 16 bits
_MIN_SECRET_BYTES = 16
# and at most 512, the largest seed BIP32 takes. The specification sets no
# maximum; without one, a share costs a decoder time quadratic in its words
_MAX_SECRET_BYTES = 64

# the shortest mnemonic: the header, the checksum, and the smallest
# share value padded up to a whole number of words -- 128 bits in 13
_MIN_VALUE_WORDS = -(-8 * _MIN_SECRET_BYTES // _RADIX_BITS)
_MIN_WORDS = (_HEADER_BITS + _CHECKSUM_BITS) // _RADIX_BITS + _MIN_VALUE_WORDS

# the longest mnemonic: the same, for the largest secret
_MAX_VALUE_WORDS = -(-8 * _MAX_SECRET_BYTES // _RADIX_BITS)
_MAX_WORDS = (_HEADER_BITS + _CHECKSUM_BITS) // _RADIX_BITS + _MAX_VALUE_WORDS

# the x coordinates SLIP-0039 reserves; 255 rather than the usual 0 so
# that no share index has to be rejected as invalid
_SECRET_X = 255
_DIGEST_X = 254
_DIGEST_BYTES = 4

_ROUNDS = 4
_BASE_ITERATIONS = 2500


def _gf256_tables() -> tuple[list[int], list[int]]:
    """Return the exp/log tables of GF(256), generator 3.

    Bytes are elements of GF(256) modulo the Rijndael polynomial, as in
    AES. A table pair is what makes multiplication and division a table
    lookup and an addition modulo 255; there is no entry for 0, which
    has no logarithm, and none is ever read -- every argument reaching
    ``_log`` here is non-zero by construction.
    """
    exp = [0] * 255
    log = [0] * 256
    poly = 1
    for i in range(255):
        exp[i] = poly
        log[poly] = i
        # multiply by the generator, x + 1, reducing modulo x**8 + x**4
        # + x**3 + x + 1 whenever the product overflows a byte
        poly = (poly << 1) ^ poly
        if poly & 0x100:
            poly ^= 0x11B
    return exp, log


_EXP, _LOG = _gf256_tables()


def _mul_tables() -> tuple[bytes, ...]:
    """Return the byte substitutions multiplying by each power of 3.

    The k-th maps every byte to its product with ``_EXP[k]``, so
    ``bytes.translate`` multiplies a whole vector by one non-zero
    constant at once. Each is the one before it multiplied by 3.
    """
    times_3 = b"\x00" + bytes(_EXP[(_LOG[a] + 1) % 255] for a in range(1, 256))
    tables = [bytes(range(256))]
    for _ in range(254):
        tables.append(tables[-1].translate(times_3))
    return tuple(tables)


_MUL_TABLES = _mul_tables()


def _interpolate(points: Sequence[tuple[int, bytes]], x: int) -> bytes:
    """Return the value-vector of the Lagrange interpolation at x.

    Shamir's scheme runs once per byte, so a point is an index and a
    whole vector of values. The Lagrange basis depends on the indexes
    alone, hence is computed once per point, as a logarithm, and the
    whole vector is multiplied by it with one table lookup.

    A repeated index is refused: it would divide by zero. x is never one
    of the indexes: it is 254 or 255, which four bits cannot hold, or --
    when generating -- an index above every one of the base points. So no
    factor of a basis is zero, and each has a logarithm.
    """
    indexes = [x_i for x_i, _ in points]
    if len(set(indexes)) != len(indexes):
        err_msg = f"invalid points: repeated index in {sorted(indexes)}"
        raise Bip39Slip39ValueError(err_msg)
    result = 0
    for x_i, y_i in points:
        log_basis = sum(
            _LOG[x ^ x_j] - _LOG[x_i ^ x_j] for x_j in indexes if x_j != x_i
        )
        product = y_i.translate(_MUL_TABLES[log_basis % 255])
        result ^= int.from_bytes(product, byteorder="big")
    return result.to_bytes(len(points[0][1]), byteorder="big")


def _digest(random_part: bytes, shared_secret: bytes) -> bytes:
    """Return the four-byte digest stored at index 254.

    Keyed on the random part rather than plain SHA256 of the secret:
    that is what stops an attacker holding the first bytes of T-1
    shares from brute-forcing the rest against the digest.
    """
    return hmac.new(random_part, shared_secret, sha256).digest()[:_DIGEST_BYTES]


# the generator of the RS1024 code, a Reed-Solomon code over GF(1024)
# whose alphabet is the 10-bit word index; the SLIP gives it as a table
_RS1024_GEN = (
    0xE0E040,
    0x1C1C080,
    0x3838100,
    0x7070200,
    0xE0E0009,
    0x1C0C2412,
    0x38086C24,
    0x3090FC48,
    0x21B1F890,
    0x3F3F120,
)


def _rs1024_table() -> tuple[int, ...]:
    """Return the XOR of the generator terms selected by each 10-bit value.

    Bit i of the value selects the i-th term, so the entries from 2**i
    to 2**(i+1) are the ones before them with that term added.
    """
    table = [0]
    for term in _RS1024_GEN:
        table += [terms ^ term for terms in table]
    return tuple(table)


# the top ten bits of the checksum are all that select the terms
_RS1024_TABLE = _rs1024_table()


def _rs1024_polymod(values: Sequence[int]) -> int:
    chk = 1
    for v in values:
        chk = ((chk & 0xFFFFF) << _RADIX_BITS ^ v) ^ _RS1024_TABLE[chk >> 20]
    return chk


def _customization_string(extendable: bool) -> list[int]:
    """Return the RS1024 customization string, as US-ASCII values.

    The extendable backup flag picks the string, so a share of one kind
    fails the checksum of the other: the two are different codes, not
    the same code over different data.
    """
    cs = "shamir_extendable" if extendable else "shamir"
    return [ord(char) for char in cs]


def _rs1024_checksum(indexes: Sequence[int], extendable: bool) -> list[int]:
    values = _customization_string(extendable) + list(indexes) + [0, 0, 0]
    polymod = _rs1024_polymod(values) ^ 1
    return [(polymod >> 10 * (2 - i)) & 1023 for i in range(_CHECKSUM_WORDS)]


def _rs1024_verify(indexes: Sequence[int], extendable: bool) -> bool:
    return _rs1024_polymod(_customization_string(extendable) + list(indexes)) == 1


def _assert_valid_length(n_bytes: int, what: str) -> None:
    if not _MIN_SECRET_BYTES <= n_bytes <= _MAX_SECRET_BYTES or n_bytes % 2:
        err_msg = f"invalid {what} length: {n_bytes} bytes; "
        err_msg += f"must be even, from {_MIN_SECRET_BYTES} to {_MAX_SECRET_BYTES}"
        raise Bip39Slip39ValueError(err_msg)


def _assert_in_ranges(*fields: tuple[str, int, int, int]) -> None:
    """Refuse each named value that is no integer from lower to upper."""
    for name, value, lower, upper in fields:
        _assert_integers((name, value))
        if not lower <= value <= upper:
            err_msg = f"invalid {name}: {value}, not in [{lower}-{upper}]"
            raise Bip39Slip39ValueError(err_msg)


@dataclass(frozen=True)
class Share:
    """A single SLIP-0039 share, i.e. one decoded mnemonic.

    The thresholds and the group count are the true values, 1 to 16,
    not the zero-based numbers the mnemonic encodes; the indexes are
    zero-based, as encoded, because they are x coordinates and nothing
    else.
    """

    identifier: int
    extendable: bool
    iteration_exponent: int
    group_index: int
    group_threshold: int
    group_count: int
    member_index: int
    member_threshold: int
    # never in repr: value is the (encrypted) master secret, and a repr
    # ends up in logs, debuggers and tracebacks the way any other
    # exception message or print does
    value: bytes = field(repr=False)

    def __post_init__(self) -> None:
        self.assert_valid()

    def assert_valid(self) -> None:
        """Raise if a field is outside what the share format can hold.

        Each field's type is asked before its value: a share can be built
        by hand, from a json record say, where `true` would pass the
        range check as 1 and a hex string the length check as a str of
        twice the bytes.
        """
        assert_type(self.extendable, bool, "extendable")
        assert_type(self.value, bytes, "share value")
        top = _MAX_SHARE_COUNT - 1
        _assert_in_ranges(
            ("identifier", self.identifier, 0, (1 << _ID_BITS) - 1),
            ("iteration exponent", self.iteration_exponent, 0, _MAX_EXPONENT),
            ("group index", self.group_index, 0, top),
            ("group threshold", self.group_threshold, 1, _MAX_SHARE_COUNT),
            ("group count", self.group_count, 1, _MAX_SHARE_COUNT),
            ("member index", self.member_index, 0, top),
            ("member threshold", self.member_threshold, 1, _MAX_SHARE_COUNT),
        )
        # a group cannot need more shares than it has, and both numbers
        # are in every share, so this is a property of one share and
        # checked here rather than when a set of them is combined
        if self.group_count < self.group_threshold:
            err_msg = f"group count {self.group_count} "
            err_msg += f"smaller than group threshold {self.group_threshold}"
            raise Bip39Slip39ValueError(err_msg)
        _assert_valid_length(len(self.value), "share value")


def _indexes_from_mnemonic(mnemonic: Mnemonic) -> list[int]:
    """Return the 10-bit word indexes of a SLIP-0039 mnemonic."""
    try:
        return indexes_from_mnemonic(mnemonic, _LANG)
    except ValueError:
        # by position and never by the word: a share is one typo away
        # from the words that recover it, and an exception message ends
        # up in logs and crash reports
        wordlist = set(WORDLISTS.wordlist(_LANG))
        positions = [
            position
            for position, word in enumerate(mnemonic.split(), 1)
            if word not in wordlist
        ]
        err_msg = f"not in the SLIP-0039 word-list: words at positions {positions}"
        raise Bip39Slip39ValueError(err_msg) from None


def share_from_mnemonic(mnemonic: Mnemonic) -> Share:
    """Return the Share the SLIP-0039 mnemonic encodes.

    The checksum is verified; the share value is not, a single share
    carrying nothing that could verify it.
    """
    assert_type(mnemonic, str, "mnemonic")
    mnemonic = " ".join(mnemonic.split())
    # before the words are decoded, which costs the square of their number
    n_words = len(mnemonic.split())
    if not _MIN_WORDS <= n_words <= _MAX_WORDS:
        err_msg = f"invalid mnemonic length: {n_words} words, "
        err_msg += f"from {_MIN_WORDS} to {_MAX_WORDS} needed"
        raise Bip39Slip39ValueError(err_msg)
    indexes = _indexes_from_mnemonic(mnemonic)

    n_bits = _RADIX_BITS * n_words
    bits = 0
    for index in indexes:
        bits = bits << _RADIX_BITS | index
    # the flag is read before the checksum is verified, being what says
    # which of the two customization strings the checksum used
    extendable = bool(bits >> (n_bits - _ID_BITS - _EXT_BITS) & 1)
    if not _rs1024_verify(indexes, extendable):
        # never the share itself: it is the (encrypted) master secret, one
        # typo away from being recoverable, and an exception message ends
        # up in logs and crash reports
        raise Bip39Slip39ValueError(f"invalid checksum: {n_words} words")

    padded_bits = n_bits - _HEADER_BITS - _CHECKSUM_BITS
    # the padded value is a whole number of words, so its length is a
    # multiple of 10 and the padding is what that leaves over 16; more
    # than a byte of it means the word count belongs to no share
    padding = padded_bits % 16
    if padding > 8:
        err_msg = f"invalid mnemonic length: {n_words} words"
        raise Bip39Slip39ValueError(err_msg)
    value_bits = padded_bits - padding
    value = bits >> _CHECKSUM_BITS & ((1 << padded_bits) - 1)
    if value >> value_bits:
        # the bits themselves are not quoted, being bits of the share
        raise Bip39Slip39ValueError("invalid padding: must be all zeros")

    # the five four-bit fields after the identifier, the flag and the
    # exponent, last first
    header = bits >> (n_bits - _HEADER_BITS)
    mask = (1 << _FIELD_BITS) - 1
    fields = [header >> (_FIELD_BITS * i) & mask for i in range(5)]
    member_threshold, member_index, group_count, group_threshold, group_index = fields
    return Share(
        identifier=header >> (_HEADER_BITS - _ID_BITS),
        extendable=extendable,
        iteration_exponent=header >> (5 * _FIELD_BITS) & _MAX_EXPONENT,
        group_index=group_index,
        group_threshold=group_threshold + 1,
        group_count=group_count + 1,
        member_index=member_index,
        member_threshold=member_threshold + 1,
        value=value.to_bytes(value_bits // 8, byteorder="big"),
    )


def mnemonic_from_share(share: Share) -> Mnemonic:
    """Return the SLIP-0039 mnemonic encoding the share."""
    assert_type(share, Share, "share")
    share.assert_valid()
    bits = share.identifier << _EXT_BITS | share.extendable
    bits = bits << _E_BITS | share.iteration_exponent
    for field_value in (
        share.group_index,
        share.group_threshold - 1,
        share.group_count - 1,
        share.member_index,
        share.member_threshold - 1,
    ):
        bits = bits << _FIELD_BITS | field_value
    # the value left-padded with zeros up to the next multiple of ten,
    # ten bits being one word
    padded_bits = -(-8 * len(share.value) // _RADIX_BITS) * _RADIX_BITS
    bits = bits << padded_bits | int.from_bytes(share.value, byteorder="big")
    n_words = (_HEADER_BITS + padded_bits) // _RADIX_BITS
    mask = (1 << _RADIX_BITS) - 1
    indexes = [bits >> (_RADIX_BITS * i) & mask for i in reversed(range(n_words))]
    indexes += _rs1024_checksum(indexes, share.extendable)
    return mnemonic_from_indexes(indexes, _LANG)


def _assert_valid_passphrase(passphrase: str) -> None:
    """Raise unless the passphrase is printable ASCII.

    SLIP-0039 restricts it to code points 32 to 126, and the
    restriction is the interoperable part: encoding anything else as
    UTF-8 and carrying on would derive a seed that another
    implementation, asked the same question, refuses to derive.
    """
    assert_type(passphrase, str, "passphrase")
    if any(not 32 <= ord(char) <= 126 for char in passphrase):
        err_msg = "invalid passphrase: only printable ASCII (32-126) is allowed"
        raise Bip39Slip39ValueError(err_msg)


def _round_function(
    i: int, passphrase: str, iteration_exponent: int, salt: bytes, right: bytes
) -> bytes:
    password = bytes([i]) + passphrase.encode()
    # 2500 per round, i.e. the 10000 iterations SLIP-0039 asks for as a
    # minimum, doubled by every step of the exponent
    iterations = _BASE_ITERATIONS << iteration_exponent
    return pbkdf2_hmac("sha256", password, salt + right, iterations, len(right))


def _feistel(
    payload: bytes,
    passphrase: str,
    iteration_exponent: int,
    identifier: int,
    extendable: bool,
    *,
    decrypt: bool,
) -> bytes:
    """Return the four-round Feistel network applied to the payload.

    Encryption and decryption differ in the order of the round indexes
    alone, which is why one function does both.

    The extendable backup flag is what the salt hangs on: with it set
    the identifier stays out, so two sets of shares with different
    identifiers decrypt to the same master secret under the same
    passphrase. That is the whole point of the flag, and it means a
    share made before the flag existed and one made after do not
    decrypt alike -- hence both states are supported here.
    """
    salt = b"" if extendable else b"shamir" + identifier.to_bytes(2, byteorder="big")
    half = len(payload) // 2
    left, right = payload[:half], payload[half:]
    rounds = reversed(range(_ROUNDS)) if decrypt else range(_ROUNDS)
    for i in rounds:
        f = _round_function(i, passphrase, iteration_exponent, salt, right)
        left, right = right, bytes(x ^ y for x, y in zip(left, f, strict=True))
    return right + left


def _assert_valid_max_exponent(max_iteration_exponent: int) -> None:
    _assert_integers(("max iteration exponent", max_iteration_exponent))
    if not 0 <= max_iteration_exponent <= _MAX_EXPONENT:
        err_msg = f"invalid max iteration exponent: {max_iteration_exponent}, "
        err_msg += f"not in [0-{_MAX_EXPONENT}]"
        raise Bip39Slip39ValueError(err_msg)


def _assert_not_above(iteration_exponent: int, max_iteration_exponent: int) -> None:
    if iteration_exponent > max_iteration_exponent:
        err_msg = f"iteration exponent {iteration_exponent} "
        err_msg += f"above the maximum {max_iteration_exponent}"
        raise Bip39Slip39ValueError(err_msg)


@dataclass(frozen=True)
class EncryptedMasterSecret:
    """A SLIP-0039 master secret encrypted under its passphrase.

    It is what a set of shares recombines to and what a new set is split
    from, so a backup is regrouped with it alone. The extendable backup
    flag decides whether the identifier salts the encryption, and the
    iteration exponent is its cost, which is why the three travel with it.
    """

    identifier: int
    extendable: bool
    iteration_exponent: int
    # never in repr, as Share's value is not: a repr ends up in logs,
    # debuggers and tracebacks
    value: bytes = field(repr=False)

    def __post_init__(self) -> None:
        self.assert_valid()

    def assert_valid(self) -> None:
        """Raise if a field is outside what the share format can hold."""
        assert_type(self.extendable, bool, "extendable")
        assert_type(self.value, bytes, "encrypted master secret value")
        _assert_in_ranges(
            ("identifier", self.identifier, 0, (1 << _ID_BITS) - 1),
            ("iteration exponent", self.iteration_exponent, 0, _MAX_EXPONENT),
        )
        _assert_valid_length(len(self.value), "encrypted master secret value")

    def master_secret(
        self, passphrase: str = "", *, max_iteration_exponent: int = _MAX_EXPONENT
    ) -> bytes:
        """Return the master secret, decrypted under the passphrase.

        A wrong passphrase is not an error: SLIP-0039 has no way to tell
        one from a right one, which is what lets a decoy wallet exist.

        Each step of the iteration exponent doubles the PBKDF2 iterations
        decrypting runs. A record above max_iteration_exponent is refused
        before PBKDF2 runs. The default, 15, is the largest exponent the
        format holds, so it refuses no record.
        """
        self.assert_valid()
        _assert_valid_passphrase(passphrase)
        _assert_valid_max_exponent(max_iteration_exponent)
        _assert_not_above(self.iteration_exponent, max_iteration_exponent)
        return _feistel(
            self.value,
            passphrase,
            self.iteration_exponent,
            self.identifier,
            self.extendable,
            decrypt=True,
        )


def _recover_secret(threshold: int, shares: Sequence[tuple[int, bytes]]) -> bytes:
    """Return the secret the shares interpolate to, digest checked."""
    if threshold == 1:
        return shares[0][1]
    secret = _interpolate(shares, _SECRET_X)
    digest_share = _interpolate(shares, _DIGEST_X)
    random_part = digest_share[_DIGEST_BYTES:]
    # `!=` and not hmac.compare_digest: a constant-time comparison matters
    # where the expected value is a secret the submitter cannot compute,
    # and here it is not. Both operands come out of the shares the caller
    # just passed in, so the caller can compute the expected digest
    # offline, for any shares, without calling this at all. A timing
    # signal can only hand back what its observer already has -- and this
    # check is an integrity test that the shares belong together, not a
    # security boundary against somebody who chooses them: such an
    # attacker forges a passing digest directly rather than searching for
    # one.
    # SLIP-0039's reference implementation compares with `!=` too.
    if digest_share[:_DIGEST_BYTES] != _digest(random_part, secret):
        raise Bip39Slip39ValueError("invalid digest: the shares do not belong together")
    return secret


def _drawn(entropy_source: Callable[[int], bytes], n_bytes: int) -> bytes:
    """Return n_bytes from the entropy source, refusing anything else.

    A bytearray is taken, as bytes: the first threshold - 2 draws are
    shares as they stand, so what the source returns is what a Share
    holds, and a Share holds bytes.
    """
    drawn: object = entropy_source(n_bytes)
    if not isinstance(drawn, bytes | bytearray):
        err_msg = f"invalid entropy source output type: {type(drawn).__name__}"
        raise Bip39Slip39TypeError(err_msg)
    if len(drawn) != n_bytes:
        err_msg = f"invalid entropy source output length: {len(drawn)} bytes "
        err_msg += f"instead of {n_bytes}"
        raise Bip39Slip39ValueError(err_msg)
    return bytes(drawn)


def _split_secret(
    threshold: int,
    share_count: int,
    secret: bytes,
    entropy_source: Callable[[int], bytes],
) -> list[bytes]:
    """Return share_count shares of the secret, threshold of them enough.

    The shares are returned in index order, the index being the x
    coordinate: the caller does not get to choose them.
    """
    if threshold == 1:
        # nothing to interpolate, and nothing to hide either: every
        # share is the secret
        return [secret] * share_count

    n = len(secret)
    # T-2 shares are free, the digest and the secret pin the rest of
    # the polynomial down
    points = [(i, _drawn(entropy_source, n)) for i in range(threshold - 2)]
    random_part = _drawn(entropy_source, n - _DIGEST_BYTES)
    points.extend(
        ((_DIGEST_X, _digest(random_part, secret) + random_part), (_SECRET_X, secret))
    )
    shares = [value for _, value in points[: threshold - 2]]
    shares += [_interpolate(points, i) for i in range(threshold - 2, share_count)]
    return shares


def _grouped(shares: Sequence[Share]) -> list[tuple[int, bytes]]:
    """Return one recovered group share per group index present."""
    groups: dict[int, list[Share]] = {}
    for share in shares:
        groups.setdefault(share.group_index, []).append(share)

    group_shares = []
    for group_index, members in groups.items():
        thresholds = {member.member_threshold for member in members}
        if len(thresholds) > 1:
            err_msg = f"mismatching member thresholds in group {group_index}: "
            err_msg += f"{sorted(thresholds)}"
            raise Bip39Slip39ValueError(err_msg)
        threshold = thresholds.pop()
        indexes = [member.member_index for member in members]
        if len(set(indexes)) != len(indexes):
            err_msg = f"duplicate member indexes in group {group_index}: "
            err_msg += f"{sorted(indexes)}"
            raise Bip39Slip39ValueError(err_msg)
        # equal, not "at least": SLIP-0039 asks for the threshold
        # number of shares and no more, so that a share which does not
        # belong is reported instead of being quietly outvoted
        if len(members) != threshold:
            err_msg = f"{len(members)} shares in group {group_index}, "
            err_msg += f"member threshold is {threshold}"
            raise Bip39Slip39ValueError(err_msg)
        points = [(member.member_index, member.value) for member in members]
        group_shares.append((group_index, _recover_secret(threshold, points)))
    return group_shares


def _common_field(shares: Sequence[Share]) -> Share:
    """Return the first share, having checked the fields all shares share."""
    first = shares[0]
    for name, values in (
        ("identifier", {share.identifier for share in shares}),
        ("extendable backup flag", {share.extendable for share in shares}),
        ("iteration exponent", {share.iteration_exponent for share in shares}),
        ("group threshold", {share.group_threshold for share in shares}),
        ("group count", {share.group_count for share in shares}),
        ("share value length", {len(share.value) for share in shares}),
    ):
        if len(values) > 1:
            err_msg = f"mismatching {name}: {sorted(values, key=str)}"
            raise Bip39Slip39ValueError(err_msg)
    return first


def _assert_mnemonic_sequence(mnemonics: object) -> None:
    """Refuse anything but a sequence of mnemonics, a lone one included.

    A mnemonic is a str, and a str is itself a sequence of str, so one
    passed where the list of shares was meant would be read one character
    at a time, each character a one-letter share: the shape
    btclib-org/btclib#1405 is about for a lone `Octets` where a
    `Sequence[Octets]` belongs.

    `not isinstance(mnemonics, Sequence)` refuses every other type the
    signature does not declare: None, which `not mnemonics` would call a
    missing mnemonic, a number, which the comprehension would answer with
    a bare TypeError, and an iterable that is no sequence, such as a set
    or a generator, which the comprehension would read.
    """
    if isinstance(mnemonics, str) or not isinstance(mnemonics, Sequence):
        err_msg = f"invalid mnemonics type: {type(mnemonics).__name__}"
        raise Bip39Slip39TypeError(err_msg)


def _assert_groups(groups: object) -> None:
    """Refuse anything but a sequence of (member threshold, member count).

    A pair is a tuple, or the list a json configuration decodes one to;
    a str or bytes of two items is no pair, however it unpacks. How many
    items a pair holds is a value, run time being unable to tell
    tuple[int] from tuple[int, int]; the bounds on each integer are
    `_assert_valid_split`'s.
    """
    if not isinstance(groups, Sequence):
        raise Bip39Slip39TypeError(f"invalid groups type: {type(groups).__name__}")
    for group in groups:
        if not isinstance(group, tuple | list):
            raise Bip39Slip39TypeError(f"invalid group type: {type(group).__name__}")
        if len(group) != 2:
            err_msg = f"invalid group: {len(group)} items, "
            err_msg += "(member threshold, member count) required"
            raise Bip39Slip39ValueError(err_msg)
        _assert_integers(("member threshold", group[0]), ("member count", group[1]))


def _assert_integers(*named: tuple[str, object]) -> None:
    """Refuse each value that is not an integer, a bool included."""
    for what, value in named:
        if not is_integer(value):
            raise Bip39Slip39TypeError(f"invalid {what} type: {type(value).__name__}")


def _ems_from_shares(shares: Sequence[Share]) -> EncryptedMasterSecret:
    """Return the encrypted master secret a non-empty set of shares holds."""
    first = _common_field(shares)
    group_shares = _grouped(shares)
    if len(group_shares) != first.group_threshold:
        err_msg = f"{len(group_shares)} groups, "
        err_msg += f"group threshold is {first.group_threshold}"
        raise Bip39Slip39ValueError(err_msg)
    return EncryptedMasterSecret(
        identifier=first.identifier,
        extendable=first.extendable,
        iteration_exponent=first.iteration_exponent,
        value=_recover_secret(first.group_threshold, group_shares),
    )


def encrypted_master_secret_from_mnemonics(
    mnemonics: Sequence[Mnemonic],
) -> EncryptedMasterSecret:
    """Return the encrypted master secret the SLIP-0039 mnemonics recombine to.

    The mnemonics must be exactly a threshold number of groups, each
    holding exactly its own member threshold of shares. No passphrase is
    needed and no PBKDF2 runs.
    """
    _assert_mnemonic_sequence(mnemonics)
    if not mnemonics:
        raise Bip39Slip39ValueError("no mnemonic")
    return _ems_from_shares([share_from_mnemonic(mnemonic) for mnemonic in mnemonics])


def master_secret_from_mnemonics(
    mnemonics: Sequence[Mnemonic],
    passphrase: str = "",
    *,
    max_iteration_exponent: int = _MAX_EXPONENT,
) -> bytes:
    """Return the master secret the SLIP-0039 mnemonics reconstruct.

    It is ``encrypted_master_secret_from_mnemonics`` and then
    ``EncryptedMasterSecret.master_secret``, whose docstrings say what
    each refuses.
    """
    _assert_valid_passphrase(passphrase)
    _assert_valid_max_exponent(max_iteration_exponent)
    ems = encrypted_master_secret_from_mnemonics(mnemonics)
    return ems.master_secret(passphrase, max_iteration_exponent=max_iteration_exponent)


def _assert_valid_split(
    groups: Sequence[tuple[int, int]], group_threshold: int, entropy_source: object
) -> None:
    """Refuse groups, a group threshold or a source no split can use."""
    _assert_groups(groups)
    _assert_integers(("group threshold", group_threshold))
    if not callable(entropy_source):
        err_msg = f"invalid entropy source type: {type(entropy_source).__name__}"
        raise Bip39Slip39TypeError(err_msg)
    for member_threshold, member_count in groups:
        # a 1-of-N group is N shares differing in an index and a
        # checksum, i.e. N copies of the same secret: SLIP-0039 forbids
        # it because someone asking for it has misunderstood the scheme
        if member_threshold == 1 and member_count > 1:
            err_msg = f"invalid 1-of-{member_count} group; "
            err_msg += "a group with threshold 1 must have a single member"
            raise Bip39Slip39ValueError(err_msg)
    for threshold, count in ((group_threshold, len(groups)), *groups):
        if not 0 < threshold <= count <= _MAX_SHARE_COUNT:
            err_msg = f"invalid threshold {threshold} of {count}; "
            err_msg += f"0 < threshold <= count <= {_MAX_SHARE_COUNT} required"
            raise Bip39Slip39ValueError(err_msg)


def mnemonics_from_encrypted_master_secret(
    encrypted_master_secret: EncryptedMasterSecret,
    groups: Sequence[tuple[int, int]] = ((1, 1),),
    group_threshold: int = 1,
    entropy_source: Callable[[int], bytes] = os.urandom,
) -> list[list[Mnemonic]]:
    """Return the SLIP-0039 shares of an encrypted master secret, grouped.

    The shares carry the record's identifier, extendable backup flag and
    iteration exponent, so they recover the same master secret under the
    same passphrase. groups, group_threshold and entropy_source are as in
    ``mnemonics_from_master_secret``, which this function's refusals
    match.
    """
    assert_type(
        encrypted_master_secret, EncryptedMasterSecret, "encrypted master secret"
    )
    encrypted_master_secret.assert_valid()
    _assert_valid_split(groups, group_threshold, entropy_source)

    ems = encrypted_master_secret
    group_values = _split_secret(
        group_threshold, len(groups), ems.value, entropy_source
    )
    mnemonics = []
    for group_index, (group_value, group) in enumerate(
        zip(group_values, groups, strict=True)
    ):
        member_threshold, member_count = group
        values = _split_secret(
            member_threshold, member_count, group_value, entropy_source
        )
        mnemonics.append(
            [
                mnemonic_from_share(
                    Share(
                        identifier=ems.identifier,
                        extendable=ems.extendable,
                        iteration_exponent=ems.iteration_exponent,
                        group_index=group_index,
                        group_threshold=group_threshold,
                        group_count=len(groups),
                        member_index=member_index,
                        member_threshold=member_threshold,
                        value=value,
                    )
                )
                for member_index, value in enumerate(values)
            ]
        )
    return mnemonics


def mnemonics_from_master_secret(
    master_secret: Octets,
    groups: Sequence[tuple[int, int]] = ((1, 1),),
    group_threshold: int = 1,
    passphrase: str = "",
    iteration_exponent: int = 1,
    extendable: bool = True,
    entropy_source: Callable[[int], bytes] = os.urandom,
) -> list[list[Mnemonic]]:
    """Return the SLIP-0039 shares of a master secret, grouped.

    groups is one (member threshold, member count) pair per group, and
    group_threshold is how many groups are needed; the default is the
    single 1-of-1 share a wallet starts with. The master secret is the
    BIP32 seed to back up, 128 to 512 bits and a multiple of 16.

    entropy_source is where every random byte comes from -- the
    identifier, the free coefficients of each polynomial and the
    digest padding -- and it is a parameter so that a caller can hand
    in a deterministic source and get a reproducible answer: nothing
    else in this scheme is testable against a fixed expectation, the
    shares of a 2-of-3 backup being random by construction. The default
    is os.urandom, the CSPRNG SLIP-0039 requires (secrets.token_bytes
    is the same bytes through another name); anything weaker substituted
    here is a secret an attacker can reproduce.

    The master secret is encrypted into an ``EncryptedMasterSecret``,
    which ``mnemonics_from_encrypted_master_secret`` splits.
    """
    _assert_valid_split(groups, group_threshold, entropy_source)
    _assert_integers(("iteration exponent", iteration_exponent))
    assert_type(extendable, bool, "extendable")
    _assert_valid_passphrase(passphrase)
    secret = bytes_from_octets(master_secret)
    _assert_valid_length(len(secret), "master secret")
    if not 0 <= iteration_exponent <= _MAX_EXPONENT:
        err_msg = f"invalid iteration exponent: {iteration_exponent}, "
        err_msg += f"not in [0-{_MAX_EXPONENT}]"
        raise Bip39Slip39ValueError(err_msg)

    # the low fifteen bits of the first two bytes drawn, rather than the
    # high fifteen: both are uniform, and this way a two-byte source
    # spells the identifier it produces
    identifier = int.from_bytes(_drawn(entropy_source, 2), byteorder="big")
    identifier &= (1 << _ID_BITS) - 1
    ems = EncryptedMasterSecret(
        identifier=identifier,
        extendable=extendable,
        iteration_exponent=iteration_exponent,
        value=_feistel(
            secret,
            passphrase,
            iteration_exponent,
            identifier,
            extendable,
            decrypt=False,
        ),
    )
    return mnemonics_from_encrypted_master_secret(
        ems, groups, group_threshold, entropy_source
    )


class Recovery:
    """A set of SLIP-0039 shares collected one mnemonic at a time.

    A complete set has the shape ``master_secret_from_mnemonics`` takes,
    so it refuses a share that shape could not hold: one whose common
    parameters differ from the first share's or whose member threshold
    differs from its group's, one already in, one for a group already
    complete, and one starting a group beyond the group threshold. A share
    above max_iteration_exponent is refused too, so that a set nobody can
    afford to decrypt is refused at its first share.
    """

    def __init__(self, *, max_iteration_exponent: int = _MAX_EXPONENT) -> None:
        _assert_valid_max_exponent(max_iteration_exponent)
        self._max_iteration_exponent = max_iteration_exponent
        self._shares: list[Share] = []

    @property
    def shares(self) -> tuple[Share, ...]:
        """The shares added so far, in the order they were added."""
        return tuple(self._shares)

    @property
    def groups(self) -> dict[int, tuple[int, int]]:
        """Map each group with a share in to (shares in, member threshold)."""
        status: dict[int, tuple[int, int]] = {}
        for share in self._shares:
            count, _ = status.get(share.group_index, (0, 0))
            status[share.group_index] = (count + 1, share.member_threshold)
        return status

    @property
    def is_complete(self) -> bool:
        """Whether the set has the shape a master secret is recovered from.

        The digest is not checked here: ``master_secret`` checks it.
        """
        groups = self.groups.values()
        if not self._shares or len(groups) < self._shares[0].group_threshold:
            return False
        return all(count == threshold for count, threshold in groups)

    def add_mnemonic(self, mnemonic: Mnemonic) -> Share:
        """Add the share the SLIP-0039 mnemonic encodes, and return it."""
        share = share_from_mnemonic(mnemonic)
        self._assert_fits(share)
        self._shares.append(share)
        return share

    def _assert_fits(self, share: Share) -> None:
        """Refuse a share the set cannot hold, quoting none of its words."""
        if not self._shares:
            _assert_not_above(share.iteration_exponent, self._max_iteration_exponent)
        else:
            first = self._shares[0]
            for name, theirs, ours in (
                ("identifier", share.identifier, first.identifier),
                ("extendable backup flag", share.extendable, first.extendable),
                (
                    "iteration exponent",
                    share.iteration_exponent,
                    first.iteration_exponent,
                ),
                ("group threshold", share.group_threshold, first.group_threshold),
                ("group count", share.group_count, first.group_count),
                ("share value length", len(share.value), len(first.value)),
            ):
                if theirs != ours:
                    err_msg = f"not a share of this set: mismatching {name}"
                    raise Bip39Slip39ValueError(err_msg)

        group_index = share.group_index
        members = [s for s in self._shares if s.group_index == group_index]
        if not members:
            started = len({s.group_index for s in self._shares})
            if started == share.group_threshold:
                err_msg = f"group {group_index} is beyond the group threshold: "
                err_msg += f"{started} groups already started"
                raise Bip39Slip39ValueError(err_msg)
            return
        if share.member_threshold != members[0].member_threshold:
            err_msg = "not a share of this set: "
            err_msg += f"mismatching member threshold in group {group_index}"
            raise Bip39Slip39ValueError(err_msg)
        if any(s.member_index == share.member_index for s in members):
            err_msg = f"member {share.member_index} of group {group_index} already in"
            raise Bip39Slip39ValueError(err_msg)
        if len(members) == share.member_threshold:
            err_msg = f"group {group_index} already complete"
            raise Bip39Slip39ValueError(err_msg)

    def master_secret(self, passphrase: str = "") -> bytes:
        """Return the master secret, once the set is complete.

        Shares that do not belong together are refused on their digest.

        The shares are recombined into an ``EncryptedMasterSecret``, which
        is decrypted under the passphrase and the maximum iteration
        exponent this recovery was made with.
        """
        _assert_valid_passphrase(passphrase)
        if not self.is_complete:
            raise Bip39Slip39ValueError("incomplete set of shares")
        return _ems_from_shares(self._shares).master_secret(
            passphrase, max_iteration_exponent=self._max_iteration_exponent
        )
