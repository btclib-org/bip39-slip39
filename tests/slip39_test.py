# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""Tests for the `btclib_mnemonics.slip39` module.

SLIP-0039's vector file carries a BIP32 root extended private key beside
each master secret, being upstream's file byte for byte. The master
secret is where this package stops, so it is what is asserted and the
key is left unread.
"""

import inspect
from collections.abc import Callable

import pytest

from btclib_mnemonics import slip39
from btclib_mnemonics.exceptions import (
    BTClibMnemonicsTypeError,
    BTClibMnemonicsValueError,
)
from btclib_mnemonics.mnemonic import WORDLISTS
from tests import load, vector_id
from tests.secret_free import assert_secret_free

# the passphrase SLIP-0039 uses for every valid set of mnemonics in its
# own vectors, and the one value that makes those 15 answers
# reproducible. noqa because a passphrase a standard publishes is a
# fixture and not a credential; the name says which it is, so renaming
# it past the S105 heuristic would hide the fact rather than the finding
PASSPHRASE = "TREZOR"  # noqa: S105

_VECTORS = load("_data", "vectors.json")

VECTORS = [
    pytest.param(*vector[1:3], id=vector_id(index, vector[0]))
    for index, vector in enumerate(_VECTORS)
]

# the valid vectors that are a single 1-of-1 share: those are the only
# ones generation can be checked against, a share of any larger scheme
# depending on randomness the vector does not record
SINGLE_SHARE_VECTORS = [
    pytest.param(vector[1][0], vector[2], id=vector_id(index, vector[0]))
    for index, vector in enumerate(_VECTORS)
    if vector[2] and len(vector[1]) == 1
]


def fixed_identifier(identifier: int) -> Callable[[int], bytes]:
    """Return an entropy source spelling one identifier and nothing else.

    A 1-of-1 backup draws no other random byte, so this is the whole of
    what generating one needs to be deterministic.
    """
    return lambda _: identifier.to_bytes(2, byteorder="big")


class CountingSource:
    """A deterministic stand-in for os.urandom, distinct on every call.

    Not `random.Random(seed).randbytes`, which would tie the expected
    shares to the mersenne twister's stream and so to a CPython
    implementation detail; the round trip only needs bytes that differ
    between the free coefficients of one polynomial.
    """

    def __init__(self) -> None:
        self.calls = 0

    def __call__(self, n_bytes: int) -> bytes:
        """Return n_bytes bytes, distinct on every call."""
        self.calls += 1
        return bytes((self.calls * 31 + i) % 256 for i in range(n_bytes))


# an encrypted master secret made with no PBKDF2, for the split refusals
_EMS = slip39.EncryptedMasterSecret(0x1234, True, 0, bytes(range(16)))


def _splits(**kwargs: object) -> list[Callable[[], object]]:
    """Return both splits, of a master secret and of an encrypted one."""
    return [
        lambda: slip39.mnemonics_from_master_secret(bytes(16), **kwargs),  # type: ignore[arg-type]
        lambda: slip39.mnemonics_from_encrypted_master_secret(_EMS, **kwargs),  # type: ignore[arg-type]
    ]


def test_wordlist() -> None:
    """Verify the word-list satisfies SLIP-0039's own criteria."""
    assert WORDLISTS.language_length("slip39") == 1024
    wordlist = WORDLISTS.wordlist("slip39")
    assert wordlist[0] == "academic"
    assert wordlist[1023] == "zero"
    # SLIP-0039's own criteria: 4 to 8 letters, and a unique four-letter
    # prefix, which is what lets a share be entered by its first four
    assert all(4 <= len(word) <= 8 for word in wordlist)
    assert len({word[:4] for word in wordlist}) == 1024
    # not BIP39's list, and the two must not be confused for one another
    assert set(wordlist) != set(WORDLISTS.wordlist("en"))


@pytest.mark.parametrize("mnemonics, master_secret", VECTORS)
def test_vectors(mnemonics: list[str], master_secret: str) -> None:
    """SLIP-0039 test vectors.

    https://github.com/trezor/python-shamir-mnemonic/blob/master/vectors.json

    The file SLIP-0039 names as its own; tests/_data/README.md pins the
    revision. An empty master secret means combining the mnemonics must
    fail, and the 30 vectors that ask for a failure are as much of the
    specification as the 15 that ask for an answer -- between them they
    cover every check the combining step is required to make.
    """
    if not master_secret:
        with pytest.raises(BTClibMnemonicsValueError):
            slip39.master_secret_from_mnemonics(mnemonics, PASSPHRASE)
        return

    assert slip39.master_secret_from_mnemonics(mnemonics, PASSPHRASE) == bytes.fromhex(
        master_secret
    )
    # every valid mnemonic re-encodes to itself, which is the half of
    # the format the vectors do not check on their own
    for mnemonic in mnemonics:
        share = slip39.share_from_mnemonic(mnemonic)
        assert slip39.mnemonic_from_share(share) == mnemonic


@pytest.mark.parametrize("mnemonic, master_secret", SINGLE_SHARE_VECTORS)
def test_generation_vectors(mnemonic: str, master_secret: str) -> None:
    """Regenerate the 1-of-1 vectors, mnemonic for mnemonic.

    A 1-of-1 share is the encrypted master secret itself, so the answer
    is fixed by the master secret, the passphrase, the iteration
    exponent, the extendable backup flag and the identifier -- all of
    them read back out of the vector. This is generation checked against
    SLIP-0039 rather than against this package's own recovery.
    """
    share = slip39.share_from_mnemonic(mnemonic)
    assert (share.group_index, share.group_threshold, share.group_count) == (0, 1, 1)
    assert (share.member_index, share.member_threshold) == (0, 1)

    mnemonics = slip39.mnemonics_from_master_secret(
        master_secret,
        passphrase=PASSPHRASE,
        iteration_exponent=share.iteration_exponent,
        extendable=share.extendable,
        entropy_source=fixed_identifier(share.identifier),
    )
    assert mnemonics == [[mnemonic]]


@pytest.mark.parametrize("extendable", [True, False])
def test_round_trip(extendable: bool) -> None:
    """Two groups, 2-of-3 and 3-of-5, both thresholds exercised."""
    master_secret = bytes(range(32))
    mnemonics = slip39.mnemonics_from_master_secret(
        master_secret,
        groups=[(2, 3), (3, 5)],
        group_threshold=2,
        passphrase=PASSPHRASE,
        iteration_exponent=0,
        extendable=extendable,
        entropy_source=CountingSource(),
    )
    assert [len(group) for group in mnemonics] == [3, 5]
    assert all(len(m.split()) == 33 for group in mnemonics for m in group)

    # a threshold of each group, and not the first shares of either
    shares = [mnemonics[0][0], mnemonics[0][2]]
    shares += [mnemonics[1][1], mnemonics[1][3], mnemonics[1][4]]
    assert slip39.master_secret_from_mnemonics(shares, PASSPHRASE) == master_secret

    # one group is not enough, however many of its shares are offered
    err_msg = "1 groups, group threshold is 2"
    with pytest.raises(BTClibMnemonicsValueError, match=err_msg):
        slip39.master_secret_from_mnemonics(mnemonics[0][:2], PASSPHRASE)


def test_default_entropy_source_draws_afresh() -> None:
    """Back one secret up repeatedly, and get different shares each time.

    No entropy source is passed, so the draws are the default's; a
    constant one would repeat the identifier and every share value.
    """
    backups = [
        slip39.mnemonics_from_master_secret(bytes(16), groups=[(2, 3)])[0]
        for _ in range(4)
    ]
    shares = [slip39.share_from_mnemonic(m) for group in backups for m in group]
    # the identifier is fifteen bits, so two backups draw the same one
    # with probability 2**-15: what is asserted is that four do not all
    assert len({share.identifier for share in shares}) > 1
    values = [share.value for share in shares]
    assert len(set(values)) == len(values)


def test_wrong_passphrase() -> None:
    """A wrong passphrase is a different secret, never an error.

    SLIP-0039 has no way to tell a right passphrase from a wrong one,
    deliberately: that is what lets a decoy wallet be plausible.
    """
    mnemonics, master_secret, _ = _VECTORS[0][1:]
    assert slip39.master_secret_from_mnemonics(
        mnemonics, "not TREZOR"
    ) != bytes.fromhex(master_secret)


def test_extendable_flag_changes_the_secret() -> None:
    """The flag is in the salt, so it is in the answer.

    Two backups of the same master secret differing only in the flag
    produce different shares, and a share of one kind fails the other's
    checksum -- which is why both states have to be supported rather
    than assumed.
    """
    master_secret = bytes.fromhex("bb54aac4b89dc868ba37d9cc21b2cece")

    def backup(extendable: bool) -> list[list[str]]:
        return slip39.mnemonics_from_master_secret(
            master_secret,
            passphrase=PASSPHRASE,
            iteration_exponent=0,
            extendable=extendable,
            entropy_source=fixed_identifier(0x1234),
        )

    extended, legacy = backup(extendable=True), backup(extendable=False)
    assert extended != legacy
    assert slip39.share_from_mnemonic(extended[0][0]).extendable
    assert not slip39.share_from_mnemonic(legacy[0][0]).extendable
    for mnemonics in (extended, legacy):
        recovered = slip39.master_secret_from_mnemonics(mnemonics[0], PASSPHRASE)
        assert recovered == master_secret

    # same identifier, same everything else: only the flag differs, and
    # the share value already does
    assert (
        slip39.share_from_mnemonic(extended[0][0]).value
        != slip39.share_from_mnemonic(legacy[0][0]).value
    )


def test_unknown_word() -> None:
    """Refuse a word outside the SLIP-0039 word-list by its position.

    Never by the word: a share is one typo away from the words that
    recover it (issue #135).
    """
    mnemonic = _VECTORS[0][1][0].replace("duckling", "abandon", 1)
    position = mnemonic.split().index("abandon") + 1
    err_msg = rf"not in the SLIP-0039 word-list: words at positions \[{position}\]$"
    with pytest.raises(BTClibMnemonicsValueError, match=err_msg) as excinfo:
        slip39.share_from_mnemonic(mnemonic)
    assert "abandon" not in str(excinfo.value)


def test_invalid_checksum() -> None:
    """Refuse a bad checksum, reporting the word count, never the share.

    A mistyped mnemonic is one guess away from the share it was meant to
    be (issue btclib-org/btclib-wallet#38).
    """
    mnemonic = _VECTORS[0][1][0]
    words = mnemonic.split()
    wordlist = WORDLISTS.wordlist("slip39")
    words[-1] = next(word for word in wordlist if word != words[-1])
    typo = " ".join(words)

    err_msg = f"invalid checksum: {len(words)} words"
    with pytest.raises(BTClibMnemonicsValueError, match=err_msg) as excinfo:
        slip39.share_from_mnemonic(typo)
    assert typo not in str(excinfo.value)


def test_share_repr_masks_value() -> None:
    """`repr(share)` never prints `value`, the (encrypted) master secret.

    `BIP32KeyData.__repr__` masks its key material for the same reason
    (issue btclib-org/btclib-wallet#39).
    """
    share = slip39.share_from_mnemonic(_VECTORS[0][1][0])
    assert share.value.hex() not in repr(share)
    assert repr(share.value) not in repr(share)
    # the non-secret fields remain readable
    assert f"identifier={share.identifier}" in repr(share)


def test_whitespace_is_collapsed() -> None:
    """Verify extra whitespace decodes to the same share."""
    mnemonic = _VECTORS[0][1][0]
    # not an f-string with the escapes inside the braces: a backslash in
    # a replacement field is python 3.12, and this package supports 3.11
    noisy = "  " + mnemonic.replace(" ", "  \n\t") + "  "
    assert slip39.share_from_mnemonic(noisy) == slip39.share_from_mnemonic(mnemonic)


def test_no_mnemonic() -> None:
    """Refuse an empty list of mnemonics."""
    with pytest.raises(BTClibMnemonicsValueError, match="no mnemonic"):
        slip39.master_secret_from_mnemonics([], PASSPHRASE)


@pytest.mark.parametrize("passphrase", ["\x1f", "\x7f", "è"])
def test_invalid_passphrase(passphrase: str) -> None:
    """Refuse a passphrase outside printable ASCII, both directions."""
    err_msg = "invalid passphrase: only printable ASCII"
    with pytest.raises(BTClibMnemonicsValueError, match=err_msg):
        slip39.master_secret_from_mnemonics(_VECTORS[0][1], passphrase)
    with pytest.raises(BTClibMnemonicsValueError, match=err_msg):
        slip39.mnemonics_from_master_secret(bytes(16), passphrase=passphrase)


@pytest.mark.parametrize(
    "field, value",
    [
        ("identifier", -1),
        ("identifier", 1 << 15),
        ("iteration_exponent", 16),
        ("group_index", 16),
        ("group_threshold", 0),
        ("group_count", 17),
        ("member_index", 16),
        ("member_threshold", 0),
    ],
)
def test_invalid_share_field(field: str, value: int) -> None:
    """Refuse each out-of-range Share field, one at a time."""
    fields = {
        "identifier": 1,
        "extendable": True,
        "iteration_exponent": 0,
        "group_index": 0,
        "group_threshold": 1,
        "group_count": 1,
        "member_index": 0,
        "member_threshold": 1,
        "value": bytes(16),
    }
    fields[field] = value
    with pytest.raises(BTClibMnemonicsValueError, match="invalid "):
        slip39.Share(**fields)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "field, value, err_msg",
    [
        ("identifier", "1", "invalid identifier type: str"),
        ("identifier", 1.5, "invalid identifier type: float"),
        ("iteration_exponent", None, "invalid iteration exponent type: NoneType"),
        ("member_index", 1.0, "invalid member index type: float"),
        ("extendable", 1, "invalid extendable type: int"),
        # the hex spelling of 16 bytes is 32 characters, a valid length
        ("value", "00" * 16, "invalid share value type: str"),
        ("value", [0] * 16, "invalid share value type: list"),
        ("value", bytearray(16), "invalid share value type: bytearray"),
    ],
)
def test_share_field_of_another_type(field: str, value: object, err_msg: str) -> None:
    """Refuse each Share field of a type the class does not declare."""
    fields: dict[str, object] = {
        "identifier": 1,
        "extendable": True,
        "iteration_exponent": 0,
        "group_index": 0,
        "group_threshold": 1,
        "group_count": 1,
        "member_index": 0,
        "member_threshold": 1,
        "value": bytes(16),
    }
    fields[field] = value
    with pytest.raises(BTClibMnemonicsTypeError, match=err_msg):
        slip39.Share(**fields)  # type: ignore[arg-type]


def test_mnemonic_from_share_refuses_what_is_no_share() -> None:
    """Refuse a value that is not a Share before asking it anything."""
    with pytest.raises(BTClibMnemonicsTypeError, match="invalid share type: NoneType"):
        slip39.mnemonic_from_share(None)  # type: ignore[arg-type]
    mnemonic: str = _VECTORS[0][1][0]
    with pytest.raises(BTClibMnemonicsTypeError, match="invalid share type: str"):
        slip39.mnemonic_from_share(mnemonic)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "groups, group_threshold",
    [
        # a threshold of 3 or more is what makes a draw a share as it stands
        ([(3, 5)], 1),
        ([(1, 1)] * 3, 3),
        ([(2, 3)], 1),
    ],
)
def test_a_bytearray_entropy_source_is_read_as_bytes(
    groups: list[tuple[int, int]], group_threshold: int
) -> None:
    """A bytearray source's draws become bytes before any Share holds them."""
    counting = CountingSource()

    def source(n_bytes: int) -> bytes:
        return bytearray(counting(n_bytes))  # type: ignore[return-value]

    secret = bytes(range(16))
    mnemonics = slip39.mnemonics_from_master_secret(
        secret, groups, group_threshold, entropy_source=source
    )
    member_threshold = groups[0][0]
    shares = [
        group[i]
        for group in mnemonics[:group_threshold]
        for i in range(member_threshold)
    ]
    assert slip39.master_secret_from_mnemonics(shares) == secret


@pytest.mark.parametrize(
    "output, error, err_msg",
    [
        (
            lambda n: memoryview(bytes(n)),
            BTClibMnemonicsTypeError,
            "output type: memoryview",
        ),
        (lambda n: bytes(n).hex(), BTClibMnemonicsTypeError, "output type: str"),
        (lambda n: None, BTClibMnemonicsTypeError, "output type: NoneType"),
        (
            lambda n: bytes(n - 1),
            BTClibMnemonicsValueError,
            "output length: 1 bytes instead of 2",
        ),
        (
            lambda n: bytes(n + 1),
            BTClibMnemonicsValueError,
            "output length: 3 bytes instead of 2",
        ),
    ],
)
@pytest.mark.parametrize("groups", [[(1, 1)], [(3, 5)]])
def test_entropy_source_output_of_another_type_or_length(
    output: Callable[[int], object],
    error: type[Exception],
    err_msg: str,
    groups: list[tuple[int, int]],
) -> None:
    """Refuse what the source draws, naming the source, at any threshold.

    The identifier is the first draw, two bytes, whatever the groups.
    """
    with pytest.raises(error, match=f"invalid entropy source {err_msg}"):
        slip39.mnemonics_from_master_secret(bytes(16), groups, entropy_source=output)  # type: ignore[arg-type]
    if groups != [(1, 1)]:
        # the encrypted master secret's split draws no identifier: its
        # first draw is a share, as long as the value
        with pytest.raises(error, match="invalid entropy source output"):
            slip39.mnemonics_from_encrypted_master_secret(
                _EMS,
                groups,
                entropy_source=output,  # type: ignore[arg-type]
            )


@pytest.mark.parametrize("passphrase", [0, [], b""])
def test_recovery_refuses_a_falsy_passphrase_of_another_type(
    passphrase: object,
) -> None:
    """The empty passphrase is "", and no other falsy value stands for it.

    A value of another type is refused whether or not it is empty.
    """
    shares = _VECTORS[0][1]
    assert slip39.master_secret_from_mnemonics(shares, "") == (
        slip39.master_secret_from_mnemonics(shares)
    )
    err_msg = f"invalid passphrase type: {type(passphrase).__name__}"
    with pytest.raises(BTClibMnemonicsTypeError, match=err_msg):
        slip39.master_secret_from_mnemonics(shares, passphrase)  # type: ignore[arg-type]


@pytest.mark.parametrize("n_bytes", [0, 14, 17, 65, 66, 4096])
def test_invalid_secret_length(n_bytes: int) -> None:
    """Refuse master secrets and share values of invalid length."""
    err_msg = f"invalid master secret length: {n_bytes} bytes"
    with pytest.raises(BTClibMnemonicsValueError, match=err_msg):
        slip39.mnemonics_from_master_secret(bytes(n_bytes))
    err_msg = f"invalid share value length: {n_bytes} bytes"
    with pytest.raises(BTClibMnemonicsValueError, match=err_msg):
        slip39.Share(1, True, 0, 0, 1, 1, 0, 1, bytes(n_bytes))


def test_group_count_below_threshold() -> None:
    """Refuse a group count smaller than the group threshold."""
    err_msg = "group count 1 smaller than group threshold 2"
    with pytest.raises(BTClibMnemonicsValueError, match=err_msg):
        slip39.Share(1, True, 0, 0, 2, 1, 0, 1, bytes(16))


@pytest.mark.parametrize("iteration_exponent", [-1, 16])
def test_invalid_iteration_exponent(iteration_exponent: int) -> None:
    """Refuse an iteration exponent outside 0..15."""
    err_msg = f"invalid iteration exponent: {iteration_exponent}"
    with pytest.raises(BTClibMnemonicsValueError, match=err_msg):
        slip39.mnemonics_from_master_secret(
            bytes(16), iteration_exponent=iteration_exponent
        )


def test_one_of_many_group() -> None:
    """A 1-of-N group is N copies of one secret; SLIP-0039 forbids it."""
    err_msg = "invalid 1-of-3 group"
    for split in _splits(groups=[(1, 3)]):
        with pytest.raises(BTClibMnemonicsValueError, match=err_msg):
            split()


@pytest.mark.parametrize(
    "groups, group_threshold",
    [
        ([(2, 3)], 0),  # a threshold of no group
        ([(2, 3)], 2),  # more groups needed than there are
        ([(1, 1)] * 17, 1),  # seventeen groups, four bits of index
        ([(3, 2)], 1),  # a group needing more shares than it has
        ([(2, 17)], 1),  # seventeen members, four bits of index
    ],
)
def test_invalid_threshold(groups: list[tuple[int, int]], group_threshold: int) -> None:
    """Refuse thresholds and counts outside SLIP-0039's bounds."""
    for split in _splits(groups=groups, group_threshold=group_threshold):
        with pytest.raises(BTClibMnemonicsValueError, match="invalid threshold "):
            split()


@pytest.mark.parametrize(
    "argument, value, err_msg",
    [
        ("groups", 5, "invalid groups type: int"),
        ("groups", {(1, 1)}, "invalid groups type: set"),
        ("groups", [5], "invalid group type: int"),
        ("groups", [b"\x01\x01"], "invalid group type: bytes"),
        ("groups", [("1", 1)], "invalid member threshold type: str"),
        ("groups", [(1, 1.0)], "invalid member count type: float"),
        ("groups", [(True, True)], "invalid member threshold type: bool"),
        ("group_threshold", "1", "invalid group threshold type: str"),
        ("group_threshold", True, "invalid group threshold type: bool"),
        ("iteration_exponent", "1", "invalid iteration exponent type: str"),
        ("iteration_exponent", 1.0, "invalid iteration exponent type: float"),
        ("passphrase", b"TREZOR", "invalid passphrase type: bytes"),
        ("entropy_source", None, "invalid entropy source type: NoneType"),
    ],
)
def test_generation_argument_of_another_type(
    argument: str, value: object, err_msg: str
) -> None:
    """Refuse each argument of a type the signature does not declare.

    Each carries a default, so `input_validation_test` never drives it.
    The encrypted master secret's split shares the arguments it takes.
    """
    with pytest.raises(BTClibMnemonicsTypeError, match=err_msg):
        slip39.mnemonics_from_master_secret(bytes(16), **{argument: value})  # type: ignore[arg-type]
    if argument in {"groups", "group_threshold", "entropy_source"}:
        with pytest.raises(BTClibMnemonicsTypeError, match=err_msg):
            slip39.mnemonics_from_encrypted_master_secret(_EMS, **{argument: value})  # type: ignore[arg-type]


@pytest.mark.parametrize("group", [(1,), (2, 3, 1)])
def test_a_group_that_is_no_pair(group: tuple[int, ...]) -> None:
    """How many items a group holds is a value, and refused as one."""
    err_msg = f"invalid group: {len(group)} items"
    for split in _splits(groups=[group]):
        with pytest.raises(BTClibMnemonicsValueError, match=err_msg):
            split()


def test_a_group_may_be_a_list() -> None:
    """A json configuration decodes a pair to a list, and it is one."""
    secret = bytes(range(16))
    source = fixed_identifier(0x1234)
    groups = [[1, 1]]
    as_list = slip39.mnemonics_from_master_secret(
        secret,
        groups,  # type: ignore[arg-type]
        entropy_source=source,
    )
    assert as_list == slip39.mnemonics_from_master_secret(secret, entropy_source=source)


def test_passphrase_of_another_type_to_recover() -> None:
    """The passphrase check is shared, so recovery refuses the type too."""
    with pytest.raises(
        BTClibMnemonicsTypeError, match="invalid passphrase type: NoneType"
    ):
        slip39.master_secret_from_mnemonics(_VECTORS[0][1], None)  # type: ignore[arg-type]


def test_shares_that_are_no_sequence() -> None:
    """An iterable of shares that is not a sequence is refused, not read.

    A set and a generator hold valid shares here, so what refuses them is
    the type and not their content; a tuple of the same shares still
    recovers the secret.
    """
    secret = bytes(range(16))
    shares = slip39.mnemonics_from_master_secret(secret, groups=[(2, 3)])[0][:2]

    assert slip39.master_secret_from_mnemonics(tuple(shares)) == secret

    with pytest.raises(BTClibMnemonicsTypeError, match="invalid mnemonics type: set"):
        slip39.master_secret_from_mnemonics(set(shares))  # type: ignore[arg-type]
    generator = (share for share in shares)
    with pytest.raises(BTClibMnemonicsTypeError, match="invalid mnemonics type: gen"):
        slip39.master_secret_from_mnemonics(generator)  # type: ignore[arg-type]


def test_the_largest_secret_is_a_512_bit_seed() -> None:
    """Round-trip the longest master secret, whose share is the longest."""
    master_secret = bytes(range(64))
    ((mnemonic,),) = slip39.mnemonics_from_master_secret(
        master_secret, iteration_exponent=0
    )
    assert len(mnemonic.split()) == slip39._MAX_WORDS
    assert slip39.master_secret_from_mnemonics([mnemonic]) == master_secret


@pytest.mark.parametrize("n_words", [0, 1, 19, 60, 12_807, 100_000])
def test_a_share_of_a_length_slip39_has_no_share_for_is_refused_undecoded(
    n_words: int, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Refuse the word count before the words are looked up or decoded."""
    decoded = lambda *_: pytest.fail("decoded")  # noqa: E731

    monkeypatch.setattr("btclib_mnemonics.slip39.indexes_from_mnemonic", decoded)
    err_msg = f"invalid mnemonic length: {n_words} words"
    with pytest.raises(BTClibMnemonicsValueError, match=err_msg):
        slip39.share_from_mnemonic(" ".join(["academic"] * n_words))


# a fixed random share value: a run such as all zeros would have pieces
# in common with a clean refusal
_VALUE = bytes.fromhex("5f0c9e41d2a7b8836e14f9c02b7d5a68")


def _one_of_one(iteration_exponent: int) -> str:
    """Return a 1-of-1 share at an iteration exponent, made with no PBKDF2."""
    share = slip39.Share(1, True, iteration_exponent, 0, 1, 1, 0, 1, _VALUE)
    return slip39.mnemonic_from_share(share)


def test_shares_above_the_maximum_exponent_are_refused_before_pbkdf2(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Refuse an exponent above the caller's maximum without running PBKDF2."""
    ran = lambda *_: pytest.fail("PBKDF2 ran")  # noqa: E731
    monkeypatch.setattr("btclib_mnemonics.slip39.pbkdf2_hmac", ran)
    mnemonic = _one_of_one(6)
    err_msg = "iteration exponent 6 above the maximum 5"
    with pytest.raises(BTClibMnemonicsValueError, match=err_msg) as excinfo:
        slip39.master_secret_from_mnemonics([mnemonic], max_iteration_exponent=5)
    assert_secret_free(excinfo.value, [_VALUE, *mnemonic.split()])


def test_shares_at_the_maximum_exponent_are_combined() -> None:
    """The maximum is inclusive, and by default it is the largest exponent."""
    mnemonics = [_one_of_one(1)]
    secret = slip39.master_secret_from_mnemonics(mnemonics)
    assert (
        slip39.master_secret_from_mnemonics(mnemonics, max_iteration_exponent=1)
        == secret
    )
    sig = inspect.signature(slip39.master_secret_from_mnemonics)
    assert sig.parameters["max_iteration_exponent"].default == 15


@pytest.mark.parametrize("bound", [-1, 16])
def test_a_maximum_exponent_the_format_cannot_hold_is_refused(bound: int) -> None:
    """Refuse a maximum outside 0..15, before reading the shares."""
    err_msg = f"invalid max iteration exponent: {bound}, not in \\[0-15\\]"
    with pytest.raises(BTClibMnemonicsValueError, match=err_msg):
        slip39.master_secret_from_mnemonics(["not read"], max_iteration_exponent=bound)


@pytest.mark.parametrize("bound", ["5", 5.0, None])
def test_a_maximum_exponent_of_another_type_is_refused(bound: object) -> None:
    """Refuse a maximum of a type the signature does not declare."""
    err_msg = f"invalid max iteration exponent type: {type(bound).__name__}"
    with pytest.raises(BTClibMnemonicsTypeError, match=err_msg):
        slip39.master_secret_from_mnemonics(
            [_one_of_one(0)],
            max_iteration_exponent=bound,  # type: ignore[arg-type]
        )


def test_interpolate_refuses_a_repeated_index() -> None:
    """Two points at one index would divide by zero; refuse them instead."""
    values = [_VALUE, _VALUE[::-1], bytes(b ^ 0xA5 for b in _VALUE)]
    points = list(zip([1, 2, 1], values, strict=True))
    with pytest.raises(BTClibMnemonicsValueError, match="repeated index") as excinfo:
        slip39._interpolate(points, 255)
    assert_secret_free(excinfo.value, values)


def test_rs1024_table_is_the_bit_by_bit_definition() -> None:
    """Each entry is the XOR of the generator terms its bits select."""
    for top in range(1024):
        terms = 0
        for i in range(10):
            terms ^= slip39._RS1024_GEN[i] if (top >> i) & 1 else 0
        assert slip39._RS1024_TABLE[top] == terms


def test_mul_tables_are_the_bit_by_bit_product() -> None:
    """Each entry is the GF(256) product, shifted and reduced bit by bit."""

    def product(a: int, b: int) -> int:
        result = 0
        while b:
            if b & 1:
                result ^= a
            a <<= 1
            if a & 0x100:
                a ^= 0x11B
            b >>= 1
        return result

    assert len(slip39._MUL_TABLES) == 255
    for k, table in enumerate(slip39._MUL_TABLES):
        constant = slip39._EXP[k]
        assert table == bytes(product(a, constant) for a in range(256))


@pytest.mark.parametrize("mnemonics, master_secret", VECTORS)
def test_the_encrypted_master_secret_on_the_vectors(
    mnemonics: list[str], master_secret: str
) -> None:
    """Recover the record, decrypt it, and split it into new groups.

    The new shares recover the vector's master secret under the vector's
    passphrase, and recombine to the same record.
    """
    if not master_secret:
        with pytest.raises(BTClibMnemonicsValueError):
            slip39.encrypted_master_secret_from_mnemonics(mnemonics)
        return

    ems = slip39.encrypted_master_secret_from_mnemonics(mnemonics)
    assert ems.master_secret(PASSPHRASE) == bytes.fromhex(master_secret)
    first = slip39.share_from_mnemonic(mnemonics[0])
    assert (ems.identifier, ems.extendable, ems.iteration_exponent) == (
        first.identifier,
        first.extendable,
        first.iteration_exponent,
    )

    regrouped = slip39.mnemonics_from_encrypted_master_secret(
        ems, [(2, 3), (3, 5)], 2, CountingSource()
    )
    shares = [regrouped[0][2], regrouped[0][0], *regrouped[1][1:4]]
    assert slip39.encrypted_master_secret_from_mnemonics(shares) == ems
    recovered = slip39.master_secret_from_mnemonics(shares, PASSPHRASE)
    assert recovered == bytes.fromhex(master_secret)


def test_the_encrypted_master_secret_repr_masks_its_value() -> None:
    """`repr` never prints the value, as `Share`'s does not."""
    ems = slip39.encrypted_master_secret_from_mnemonics(_VECTORS[0][1])
    assert ems.value.hex() not in repr(ems)
    assert repr(ems.value) not in repr(ems)
    assert f"identifier={ems.identifier}" in repr(ems)


@pytest.mark.parametrize(
    "field, value, error, err_msg",
    [
        ("identifier", -1, BTClibMnemonicsValueError, "invalid identifier: -1"),
        ("identifier", 1 << 15, BTClibMnemonicsValueError, "invalid identifier: "),
        ("identifier", "1", BTClibMnemonicsTypeError, "invalid identifier type: str"),
        (
            "iteration_exponent",
            16,
            BTClibMnemonicsValueError,
            "invalid iteration exponent: 16",
        ),
        (
            "iteration_exponent",
            None,
            BTClibMnemonicsTypeError,
            "invalid iteration exponent type: NoneType",
        ),
        ("extendable", 1, BTClibMnemonicsTypeError, "invalid extendable type: int"),
        (
            "value",
            "00" * 16,
            BTClibMnemonicsTypeError,
            "invalid encrypted master secret value type: str",
        ),
        (
            "value",
            bytes(15),
            BTClibMnemonicsValueError,
            "invalid encrypted master secret value length: 15 bytes",
        ),
    ],
)
def test_an_encrypted_master_secret_field_out_of_its_domain(
    field: str, value: object, error: type[Exception], err_msg: str
) -> None:
    """Refuse each field of a value or a type the record cannot hold."""
    fields: dict[str, object] = {
        "identifier": 1,
        "extendable": True,
        "iteration_exponent": 0,
        "value": bytes(16),
    }
    fields[field] = value
    with pytest.raises(error, match=err_msg):
        slip39.EncryptedMasterSecret(**fields)  # type: ignore[arg-type]


def test_the_encrypted_split_refuses_what_is_no_record() -> None:
    """A Share is no record, though it carries the same fields and more."""
    share = slip39.share_from_mnemonic(_VECTORS[0][1][0])
    err_msg = "invalid encrypted master secret type: Share"
    with pytest.raises(BTClibMnemonicsTypeError, match=err_msg):
        slip39.mnemonics_from_encrypted_master_secret(share)  # type: ignore[arg-type]


def test_a_record_changed_after_it_was_built_is_refused() -> None:
    """A frozen dataclass can still be written to, so each use re-checks it."""
    ems = slip39.EncryptedMasterSecret(1, True, 0, _VALUE)
    object.__setattr__(ems, "iteration_exponent", 16)
    err_msg = "invalid iteration exponent: 16"
    with pytest.raises(BTClibMnemonicsValueError, match=err_msg):
        ems.master_secret()
    with pytest.raises(BTClibMnemonicsValueError, match=err_msg):
        slip39.mnemonics_from_encrypted_master_secret(ems)


def test_a_record_above_the_maximum_exponent_is_refused_before_pbkdf2(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The bound holds on the record, the one step that runs PBKDF2."""
    ran = lambda *_: pytest.fail("PBKDF2 ran")  # noqa: E731
    monkeypatch.setattr("btclib_mnemonics.slip39.pbkdf2_hmac", ran)
    ems = slip39.EncryptedMasterSecret(1, True, 6, _VALUE)
    err_msg = "iteration exponent 6 above the maximum 5"
    with pytest.raises(BTClibMnemonicsValueError, match=err_msg) as excinfo:
        ems.master_secret(max_iteration_exponent=5)
    assert_secret_free(excinfo.value, [_VALUE])
    for bound in (-1, 16):
        with pytest.raises(BTClibMnemonicsValueError, match="invalid max iteration"):
            ems.master_secret(max_iteration_exponent=bound)
    with pytest.raises(BTClibMnemonicsTypeError, match="invalid passphrase type"):
        ems.master_secret(b"")  # type: ignore[arg-type]


def test_a_record_at_the_maximum_exponent_is_decrypted() -> None:
    """The maximum is inclusive, and by default it is the largest exponent."""
    ems = slip39.EncryptedMasterSecret(1, True, 1, _VALUE)
    assert ems.master_secret(max_iteration_exponent=1) == ems.master_secret()
    sig = inspect.signature(slip39.EncryptedMasterSecret.master_secret)
    assert sig.parameters["max_iteration_exponent"].default == 15


def _backup() -> list[list[str]]:
    """Return a backup needing two groups of three: 2-of-3, 3-of-5, 2-of-2."""
    return slip39.mnemonics_from_master_secret(
        bytes(range(16)),
        groups=[(2, 3), (3, 5), (2, 2)],
        group_threshold=2,
        passphrase=PASSPHRASE,
        iteration_exponent=0,
        entropy_source=CountingSource(),
    )


@pytest.mark.parametrize("mnemonics, master_secret", VECTORS)
def test_the_recovery_on_the_vectors(mnemonics: list[str], master_secret: str) -> None:
    """Recovering one mnemonic at a time answers as the whole set does.

    A set the vector calls invalid is refused at a share, or when its
    master secret is asked for.
    """
    recovery = slip39.Recovery()
    if not master_secret:
        with pytest.raises(BTClibMnemonicsValueError):
            for mnemonic in mnemonics:
                recovery.add_mnemonic(mnemonic)
            recovery.master_secret(PASSPHRASE)
        return

    for mnemonic in mnemonics:
        assert not recovery.is_complete
        recovery.add_mnemonic(mnemonic)
    assert recovery.is_complete
    assert recovery.master_secret(PASSPHRASE) == bytes.fromhex(master_secret)


def test_the_recovery_answers_how_far_it_is() -> None:
    """Per group, the shares in and the threshold; and whether it is done."""
    backup = _backup()
    recovery = slip39.Recovery()
    assert (recovery.shares, recovery.groups, recovery.is_complete) == ((), {}, False)

    added = recovery.add_mnemonic(backup[1][4])
    assert added == slip39.share_from_mnemonic(backup[1][4])
    assert recovery.shares == (added,)
    assert recovery.groups == {1: (1, 3)}
    recovery.add_mnemonic(backup[0][1])
    recovery.add_mnemonic(backup[0][0])
    # one group complete is not a complete set: the group threshold is 2
    assert (recovery.groups, recovery.is_complete) == ({1: (1, 3), 0: (2, 2)}, False)
    with pytest.raises(BTClibMnemonicsValueError, match="^incomplete set of shares$"):
        recovery.master_secret(PASSPHRASE)
    recovery.add_mnemonic(backup[1][0])
    recovery.add_mnemonic(backup[1][2])
    assert (recovery.groups, recovery.is_complete) == ({1: (3, 3), 0: (2, 2)}, True)
    assert recovery.master_secret(PASSPHRASE) == bytes(range(16))
    assert len(recovery.shares) == 5


def _share_like(base: slip39.Share, **fields: object) -> str:
    """Return the mnemonic of a share differing from base in the fields."""
    values = {name: getattr(base, name) for name in base.__dataclass_fields__}
    return slip39.mnemonic_from_share(slip39.Share(**(values | fields)))


def _refused(recovery: slip39.Recovery, mnemonic: str, err_msg: str) -> None:
    """Refuse the mnemonic, quoting none of its words, and leave the set."""
    before = recovery.shares
    with pytest.raises(BTClibMnemonicsValueError, match=err_msg) as excinfo:
        recovery.add_mnemonic(mnemonic)
    share = slip39.share_from_mnemonic(mnemonic)
    assert_secret_free(excinfo.value, [mnemonic, *mnemonic.split(), share.value])
    assert recovery.shares == before


@pytest.mark.parametrize(
    "field, value, name",
    [
        ("identifier", 0x7ABC, "identifier"),
        ("extendable", False, "extendable backup flag"),
        ("iteration_exponent", 1, "iteration exponent"),
        ("group_threshold", 3, "group threshold"),
        ("group_count", 4, "group count"),
        ("value", bytes(range(32)), "share value length"),
        ("member_threshold", 3, "member threshold in group 0"),
    ],
)
def test_the_recovery_refuses_a_share_of_another_set(
    field: str, value: object, name: str
) -> None:
    """A common parameter differs from the first share's, or a group's."""
    backup = _backup()
    recovery = slip39.Recovery()
    first = recovery.add_mnemonic(backup[0][0])
    mnemonic = _share_like(first, member_index=1, **{field: value})
    _refused(recovery, mnemonic, f"^not a share of this set: mismatching {name}$")


def test_the_recovery_refuses_a_share_already_in() -> None:
    """The same share twice, or another one at the same member index."""
    backup = _backup()
    recovery = slip39.Recovery()
    first = recovery.add_mnemonic(backup[1][2])
    err_msg = "^member 2 of group 1 already in$"
    _refused(recovery, backup[1][2], err_msg)
    _refused(recovery, _share_like(first, value=_VALUE), err_msg)


def test_the_recovery_refuses_a_share_of_a_complete_group() -> None:
    """A share beyond a group's threshold, which the whole set refuses too."""
    backup = _backup()
    recovery = slip39.Recovery()
    recovery.add_mnemonic(backup[0][0])
    recovery.add_mnemonic(backup[0][2])
    _refused(recovery, backup[0][1], "^group 0 already complete$")
    with pytest.raises(BTClibMnemonicsValueError, match="3 shares in group 0"):
        slip39.master_secret_from_mnemonics(backup[0], PASSPHRASE)


def test_the_recovery_refuses_a_group_beyond_the_group_threshold() -> None:
    """A third group of a 2-of-3 set, which the whole set refuses too."""
    backup = _backup()
    recovery = slip39.Recovery()
    recovery.add_mnemonic(backup[0][0])
    recovery.add_mnemonic(backup[1][0])
    err_msg = "^group 2 is beyond the group threshold: 2 groups already started$"
    _refused(recovery, backup[2][0], err_msg)


def test_the_recovery_refuses_a_share_above_its_maximum_exponent() -> None:
    """At the first share, so that no other share is asked for."""
    recovery = slip39.Recovery(max_iteration_exponent=5)
    _refused(recovery, _one_of_one(6), "^iteration exponent 6 above the maximum 5$")
    recovery.add_mnemonic(_one_of_one(5))
    assert recovery.is_complete


@pytest.mark.parametrize(
    "bound, error, err_msg",
    [
        (-1, BTClibMnemonicsValueError, "invalid max iteration exponent: -1"),
        (16, BTClibMnemonicsValueError, "invalid max iteration exponent: 16"),
        ("5", BTClibMnemonicsTypeError, "invalid max iteration exponent type: str"),
    ],
)
def test_the_recovery_refuses_a_maximum_exponent_out_of_its_domain(
    bound: object, error: type[Exception], err_msg: str
) -> None:
    """The bound is checked once, when the recovery is made."""
    with pytest.raises(error, match=err_msg):
        slip39.Recovery(max_iteration_exponent=bound)  # type: ignore[arg-type]


def test_the_recovery_refuses_arguments_of_another_type() -> None:
    """A mnemonic and a passphrase are str."""
    recovery = slip39.Recovery()
    with pytest.raises(BTClibMnemonicsTypeError, match="invalid mnemonic type: list"):
        recovery.add_mnemonic(_VECTORS[0][1])
    recovery.add_mnemonic(_VECTORS[0][1][0])
    with pytest.raises(BTClibMnemonicsTypeError, match="invalid passphrase type"):
        recovery.master_secret(b"TREZOR")  # type: ignore[arg-type]


def test_a_complete_recovery_of_two_splits_is_refused_on_the_digest() -> None:
    """One identifier, two secrets: the shape is complete, the digest is not.

    Every common parameter matches, so each share is taken and the set is
    complete; what refuses it is the digest, as it refuses the whole set.
    """
    values = [bytes(16), bytes(range(16))]
    first, second = (
        slip39.mnemonics_from_encrypted_master_secret(
            slip39.EncryptedMasterSecret(0x1234, True, 0, value),
            groups=[(2, 3)],
            entropy_source=CountingSource(),
        )[0]
        for value in values
    )
    recovery = slip39.Recovery()
    recovery.add_mnemonic(first[0])
    recovery.add_mnemonic(second[1])
    assert recovery.is_complete
    mixed = [first[0], second[1]]
    secrets: list[str | bytes] = list(values)
    for mnemonic in mixed:
        secrets += [mnemonic, *mnemonic.split()]
        secrets.append(slip39.share_from_mnemonic(mnemonic).value)
    err_msg = "^invalid digest: the shares do not belong together$"
    refusals: list[Callable[[], object]] = [
        recovery.master_secret,
        lambda: slip39.master_secret_from_mnemonics(mixed),
    ]
    for refused in refusals:
        with pytest.raises(BTClibMnemonicsValueError, match=err_msg) as excinfo:
            refused()
        assert_secret_free(excinfo.value, secrets)
