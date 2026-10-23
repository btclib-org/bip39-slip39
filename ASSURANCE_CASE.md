# Assurance case

[SECURITY](./SECURITY.md) states what a user can and cannot expect of
bip39-slip39 in terms of security. This page argues why those
expectations hold: the threat model, the trust boundaries, how secure
design principles are applied, and how common implementation weaknesses
are countered. Each argument below names the file, the test or the
workflow that supports it; where SECURITY.md already states a fact, this
page points at it instead of repeating it.

## What is claimed

- **A sentence, a seed and a set of shares agree with the reference each
  is defined by.** BIP39 against the reference implementation's vectors
  and the Japanese ones BIP39 cites, SLIP-0039 against SatoshiLabs'
  vectors, and Electrum's mnemonics against vectors produced by running
  Electrum itself. `tests/_data/README.md` says where each file came
  from, pins every vendored one to the upstream commit it was copied
  from, and says whether the two still match, which its *Re-checking a
  pin* procedure re-checks by hand. `.github/workflows/vendored-vectors.yml`
  runs weekly: it holds each vendored file to the `ours` or `blob`
  recorded there and `blob` to upstream's at the pinned commit, and
  reports a pin that is no longer upstream's tip.
- **Malformed input is refused the way the package says it is.** A
  public function handed an argument it cannot use raises
  `Bip39Slip39TypeError` or `Bip39Slip39ValueError`
  (`tests/input_validation_test.py`, `tests/integer_policy_test.py`,
  `tests/bool_parameter_test.py`, `tests/refusals_test.py`), and a decoder
  handed a hostile sentence, lone surrogates included, raises one of the
  two and nothing else (`tests/fuzz_test.py`).
- **Randomness is the operating system's.** SECURITY.md states it, and
  *Common implementation weaknesses* below says what keeps it so.
- **A published distribution is what this tree built.** SECURITY.md's
  *Supported versions* states how that is verified.

## Threat model

bip39-slip39 is a library in its caller's process, and the command
`python -m bip39_slip39` runs in its own and reads and writes its
terminal. Neither opens a socket, runs a subprocess or writes a file;
the one read of a path a caller chose is *Files* below.
`tests/imports_test.py` holds every module to the standard library,
both as imported and as written.

**What is defended.**

- Entropy, mnemonics, seeds, SLIP-0039 master secrets and shares, and
  the passphrases that stretch them, against recovery from what this
  package returns.
- The correctness of every answer: a sentence, the entropy it encodes,
  the seed or master secret it stretches to, a split and its recombination,
  and the scheme a sentence is recognized as.
- The caller's process, against a sentence or a share built to make a
  decoder raise an exception this package does not document.

**The adversaries.**

- A party handing this package a sentence or a share built to exploit a
  decoder rather than to be restored.
- A party holding fewer shares than a SLIP-0039 threshold, trying to
  learn the master secret from them.
- A party tampering with a distribution between this tree and the user.

**What is not defended**, each stated in SECURITY.md's *Limitations, not
vulnerabilities*:

- side channels: nothing here is constant-time
- memory disclosure: secret material in a Python object is not zeroized
- whatever the terminal keeps of the interactive `entropy.collect_rolls`
  and `python -m bip39_slip39`
- the PBKDF2 work a SLIP-0039 share's iteration exponent asks for, up to
  the `max_iteration_exponent` a caller passes; a share longer than a
  512-bit secret needs is refused, so its length adds no work
- the operating system and the interpreter

## Trust boundaries

**The caller and the public API.** Arguments cross from the caller into
bip39-slip39 at every public function, and each is validated there.
CONTRIBUTING.md's *The public surface* states the rule and names the
tests that drive it.

**Sentences and shares from outside.** A mnemonic is typed, scanned or
read back by a user, and every decoder that takes one —
`bip39.entropy_from_mnemonic`, `electrum.version_from_mnemonic`,
`slip39.share_from_mnemonic` and the rest `tests/fuzz_test.py` lists —
is driven by Hypothesis there and by `fuzz/fuzz_mnemonics.py` under
ClusterFuzzLite (`.github/workflows/fuzz.yml`);
`tests/fuzz_corpus_test.py` checks that the harness calls each of them
and that every seed of its corpus is still read.

**Files.** `mnemonic.WordLists` takes a caller's path for a language, in
its `language_files` constructor argument and its `load_lang` method.
Every other read under `src/` is this package's own `_data/`, and
nothing under `src/` writes a file.

## Secure design principles

Saltzer and Schroeder's principles apply across the layers described in
[ARCHITECTURE.md](./ARCHITECTURE.md).

- **Economy of mechanism.** Three schemes over one word-list machinery
  (`mnemonic`), BIP39 and Electrum also over one entropy module
  (`entropy`), and none of the three imports another.
- **Fail-safe defaults.** `bip39.seed_from_mnemonic` checks the checksum
  unless told not to, and a flag whose wrong value would compute another
  answer refuses a non-bool (`tests/bool_parameter_test.py`).
- **Complete mediation.** Every public function validates its inputs;
  a private twin trusts its inputs because its callers checked them.
- **Open design.** The code, the vendored vectors and the fuzzing corpus
  are published, and SECURITY.md states what is not defended.
- **Least privilege.** The standard library alone, and within it no
  network, no subprocess and no write.
- **Psychological acceptability.** A refusal is one of the package's two
  exception classes, each beside the built-in of its name, so a caller
  catching `ValueError` or `TypeError` catches it too.

## Common implementation weaknesses

Weaknesses from MITRE's CWE list that a package of this kind is exposed
to, and what counters each.

- **Improper input validation (CWE-20).** The trust boundaries above, and
  `tests/integer_policy_test.py`, which refuses a `bool` where an
  integer field — a word index, a dice roll, a SLIP-0039 threshold — is
  expected.
- **Uncaught exceptions on hostile input (CWE-248, CWE-755).**
  `tests/fuzz_test.py`'s contract, driven by Hypothesis and by
  ClusterFuzzLite.
- **Race conditions on shared state (CWE-362).** The module-level
  `WORDLISTS` is reachable from any thread, and `WordLists`' lock keeps
  a second thread arriving mid-load from reading an empty list;
  `tests/mnemonic_test.py`'s `test_load_lang_is_not_a_race` forces that
  interleaving.
- **Weak randomness (CWE-330, CWE-338).** Randomness comes from
  `secrets` and `os.urandom`, and ruff's flake8-bandit rules, selected
  with the rest in `pyproject.toml` and waived for S311 under `tests/`
  alone, flag a `random` call under `src/`.
- **Exposure of sensitive information (CWE-209).** No refusal quotes
  what the secret holds: an unknown word is named by its position, a
  word-list index out of range by its position, and a checksum, a
  padding or an Electrum version by what it is, never by its bits or its
  hash (`tests/refusals_test.py`). An unknown language or Electrum
  version is not quoted, so an entropy or a sentence passed in its place
  is not repeated.
  The rule is section 7's *A refusal carries no secret* in the
  [btclib-org standard](https://github.com/btclib-org/.github#a-refusal-carries-no-secret).
  Its helper, `assert_secret_free` in `tests/secret_free/__init__.py`, is
  called by each test of `tests/refusals_test.py` that feeds a secret, with
  the spellings its refusal could print. It reads each exception the
  refusal chains.
- **Type confusion (CWE-843).** mypy runs with `strict = true` over the
  package and the suite, as a hook of the lint gate.
- **Code that is wrong and still passes.** Line and branch coverage is
  held at 100% by `fail_under` in `pyproject.toml`, and mutation testing,
  profiled per scheme under `.github/mutation/` and run by
  `.github/workflows/mutation.yml`, asks whether the suite notices a
  wrong line.
- **Supply chain.** SECURITY.md's *Supported versions* describes the
  attestations and the bill of materials. The runtime has no dependency;
  `uv.lock` pins the tools and the test oracles, and every third-party
  action is pinned to a commit sha.
