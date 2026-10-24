# Changelog

<!-- markdownlint-configure-file
  {
    // MD024/no-duplicate-heading - every release repeats the same few
    // headings, which is what keeps the page readable scrolling down it;
    // only a duplicate under the same release heading would be the
    // accident this rule looks for
    "MD024": { "siblings_only": true }
  }
-->

The release's own pull request writes its section here, from the squash
subjects since the previous tag; a pull request adds no entry
(`CONTRIBUTING.md`'s *Pull requests*, section 9 of [the organization
standard][std]). [RELEASE_NOTES.md](./RELEASE_NOTES.md) has the release
notes, which say what a user has to act on; this file is the record
behind them.

[std]: https://github.com/btclib-org/.github

## v2026.10.23

### The package is `bip39-slip39`, imported as `bip39_slip39`

The distribution, the import package and the repository URLs drop the btclib
name (issue #106).

### The exceptions are named after the package

`Bip39Slip39Exception`, `Bip39Slip39TypeError` and `Bip39Slip39ValueError`
replace the `BTClibMnemonics` ones (closes #148).

### A release is verified by repository id

`SECURITY.md` and `RELEASING.md` check `sourceRepositoryIdentifier` against the
repository's id, which a rename keeps, in place of `--repo` (closes #158).

### `AGENTS.md` replaces `CLAUDE.md`

`ARCHITECTURE.md` names the package layers, and `CONTRIBUTING.md` has the
worktree procedure (issue btclib-org/.github#1808).

### `python -m bip39_slip39` turns dice into a recomputable mnemonic

The README recomputes the entropy with `hashlib`. The rolls and random draws
lose `shuffle`, `entropy` and `to_be_hashed`; `collect_rolls` reads Enter alone
as a hand-rolled D6 and bounds an answer at three digits (closes #95).

### `entropy.collect_rolls` prompts in every word-list language

A new `lang` parameter selects the language of its texts (closes #94).

### SLIP-0039 recovers share by share and bounds its cost

`EncryptedMasterSecret`, `Recovery` and `max_iteration_exponent` are new, and a
repeated index is refused (closes #109, closes #111, closes #112, closes #115,
closes #117, closes #131, closes #132).

### Electrum refuses a sentence longer than it can write

`entropy_from_mnemonic` refuses it before decoding it, and
`_normalize` and `_is_cjk` are faster (closes #116, closes #110).

### `bip39.is_valid_mnemonic` is public

It answers whether a sentence is a BIP39 mnemonic without an `except`
(closes #133).

### `WordLists.words_with_prefix` completes a word

The words of a list that begin with a prefix are answered in list order
(closes #130).

### A language's words and index are one record

A thread converting while another loads a language no longer pairs two
loads, and a language already loaded skips the lock (closes #124, closes #114).

### `__version__` is read on first access

Importing the package no longer imports `importlib.metadata` (closes #113).

### `_bin_str_entropy_from_int` takes only an `int`

The string branch no caller reached is removed (closes #108).

### The lock-free read test joins the threads it starts

The test no longer leaves them running (closes #138).

### The refusal tests take the shared `secret_free` helper

The helper checks the grouped secret (issue btclib-org/.github#1697).

### `CONTRIBUTING.md` says most wrong values are true

`0`, `None` and `""` are wrong values that read as `False` (closes #107).

### `CONTRIBUTING.md` takes the organization's shared half

The tree's docs drop the bypass (issue btclib-org/.github#1740).

### `SECURITY.md` says to fix a defect easy to rediscover as soon as possible

(issue btclib-org/.github#1771).

### The pyroma hook builds no dependency from source

(issue btclib-org/.github#1763).

### `claude-review.yml` declines zizmor's `dangerous-triggers` on `issue_comment`

(issue btclib-org/.github#1813).

### `dependabot.yml` names the `uv.lock` exception

Its comment on the `uv` ecosystem points to the exception that section 1 of
btclib-org/.github's `README.md` names (issue btclib-org/.github#1818).

### The publish jobs take v1.14.3 and uv is at least 0.13.4

`gh-action-pypi-publish` v1.14.3 fixes GHSA-5xjx-3w67-w9x9, `required-version`
refuses a uv that trusts the emSign root (GHSA-hq85-5cpj-mr62), and virtualenv
21.14.13 fixes GHSA-cx6f-vjhg-g3cc (issue btclib-org/.github#1844).

### The pinned versions move

aiohttp, `certifi`, virtualenv, GitPython, setuptools, filelock, `setup-uv` and
the hook revisions move (closes #142, issue btclib-org/.github#1824, issue
btclib-org/.github#1835, issue btclib-org/.github#1849, #144, #145, #151).

### Open 2026.11 after v2026.10.17

The declared version is the month alone between releases (#105).

## v2026.10.17

### The refusal tests check that no refusal prints the secret

`tests/refusals_test.py` passes each refusal fed a secret to the shared
`assert_secret_free`, with the secret's spellings (issue
btclib-org/.github#1697, closes #87).

### The runtime import check sees a package `uv run --with` layers

`tests/imports_test.py` counts a file under a `site-packages` or
`dist-packages` directory as installed (closes #78).

### `api-break.yml` labels a pull request that breaks the public API

It gates nothing, and a merged pull request's closed run queues behind the
walk in flight instead of cancelling it (issue btclib-org/.github#1674,
issue btclib-org/.github#1744).

### `verified-signatures.yml` checks the signatures on `main`

On each push to `main` it fails unless every new commit is verified on the
forge. It stands in for the `required_signatures` rule, removed from `main`
so that outside contributors need not sign (issue btclib-org/.github#1738).

### The workflow linter is the actionlint fork

The workflows are linted by the `actionlint-shellcheck` hook of kjanat's
fork, and `claude-review.yml`'s review call sets `cache-mode: none` (issue
btclib-org/.github#1698, closes #88).

### The maintainer's bypass is everyday practice

`CONTRIBUTING.md` and `REVIEWING.md` take btclib-org/.github's shared
halves, and `REPOSITORY.md` records `strict` off on `main` (issue
btclib-org/.github#1695, issue btclib-org/.github#1712).

### `RELEASING.md` runs the dependents' suites and reads the tag back

Each dependent's suite runs with the release pull request's head before the
merge, and the tag's signature is read back from the API after the push
(issue btclib-org/.github#1647, issue btclib-org/.github#1660).

### `REPOSITORY.md` says what the tag-integrity ruleset does not check

It accepts an unsigned or lightweight `v*` tag on a commit already on `main`
(issue btclib-org/.github#1635).

### An owner commits the uv export on a Dependabot `uv` pull request

`CONTRIBUTING.md` says so, since Dependabot rewrites `uv.lock` alone and the
`uv-export` hook then fails. `.clusterfuzzlite/requirements.txt` is
regenerated with that hook (closes #79, closes #80).

### The pinned versions move

The development dependencies, the artifact actions, the fuzz base image and
the hook revisions are bumped (#74, #75, #85, #91, #92, #93), and pydantic
to 2.14.0 so that the pyroma hook builds nothing (issue btclib-org/btclib#2685).

### Open 2026.11 after v2026.10.8

The declared version is the month alone again between releases (#73).

## v2026.10.8

### The shared halves of `CONTRIBUTING.md` and `REVIEWING.md` are `.github`'s

The author resolves an answered thread; the reviewer reopens one only while
it blocks (issue btclib-org/.github#1620, issue btclib-org/.github#1634).

### `CONTRIBUTING.md` says the maintainer self-merges while the bot review is off

*The review* says no ack of record exists while `claude-review.yml` is off,
and that a local review of a named sha, by a reviewer other than the author,
stands in (issue btclib-org/.github#1527).

### `SECURITY.md` says where randomness comes from

`SECURITY.md` names `os.urandom` beside `secrets`, and says a weak
`entropy_source` a caller passes to `slip39.mnemonics_from_master_secret`
is the caller's (issue #24).

### `claude-review.yml`'s header says what the tree handles

The header says the tree handles a caller's entropy, mnemonics and seeds
(closes #24).

### Open 2026.11: the declared version has no day

The declared version is the month alone while a cycle is in progress (#47).

### `CONTRIBUTING.md` lists the jobs that do not pass `--locked`

`CONTRIBUTING.md` lists the jobs that install without `--locked`, and the
comments that said every job passes it no longer do
(btclib-org/btclib#2440, issue #25).

### The verification command pins the tag for every signer

SECURITY.md and RELEASING.md said a `reusable-attest.yml` release took no
`--source-ref`; it takes the tag (issue #25, btclib-org/btclib#2447).

### The weekly vendored-vectors check compares the vendored bytes

`check_vendored_vectors.py` holds each vendored file to the ledger's `ours`,
or `blob` where there is none, and `blob` to upstream's at the pinned commit;
a mismatch fails the run (btclib-org/btclib#2439, issue #25).

### The release publishes the files the build job built

The publish jobs, `github-release` and `test.yml`'s `dist` job on a release
stop where the `dist` they download differs from the digests
`reusable-build.yml` outputs (issue #25, btclib-org/btclib#2449).

### `dependabot.yml` does not say that every workflow passes `--locked`

`.github/dependabot.yml` says the workflows install from `uv.lock` with
`--locked`, bar the exceptions `CONTRIBUTING.md` lists (issue
btclib-org/.github#1538).

### `.gitattributes` marks where the shared copy ends

The `-text` lines for the vendored files sit below a `## This repository in
particular` heading, so they are not compared with the organization's copy
(closes btclib-org/.github#1543).

### `REPOSITORY.md` reads back the web sign-off setting

`REPOSITORY.md` reads `web_commit_signoff_required` back, the organization
setting section 11 of the standard states (issue btclib-org/.github#1540).

### The `Sign-off` check is required

`CONTRIBUTING.md`'s shared half says a pull request whose commits lack the
`Signed-off-by:` trailer cannot merge, and `REPOSITORY.md` lists
`lint / Sign-off` among the required checks (issue btclib-org/.github#1550).

### `CONTRIBUTING.md` says the bot's review is the ack of record

*The review* says the maintainer lands their own pull requests through the
bypass, and that the ack of record is a bot's, so the OpenSSF criterion
`two_person_review` is unmet (issue btclib-org/.github#452).

### The maintainer's bypass is for emergencies only

`CONTRIBUTING.md`, `RELEASING.md`, `REPOSITORY.md` and `REVIEWING.md` say every
pull request lands with an approving review from somebody other than its
author; the bypass is for emergencies (issue btclib-org/.github#1362).

### Earlier entries on how a pull request lands

Entries above that have the maintainer landing without another person's
approval describe the rule before issue btclib-org/.github#1362 (issue
btclib-org/.github#1569).

### Forms set a type, `merge=union` goes, bestpractices.dev is reviewed

The issue forms set `type:` and no kind label (issue btclib-org/.github#1584),
the history files lose `merge=union` (issue btclib-org/.github#1582), and
RELEASING.md reviews bestpractices.dev (issue btclib-org/.github#1589).

### The post-release install refreshes the index

RELEASING.md installs the release with `--refresh-package btclib-mnemonics`,
because uv can answer from a cached index and miss a version just published
(issue btclib-org/.github#1595).

### `--admin` waits for no required check

`CONTRIBUTING.md`'s emergency paragraph says `--admin` skips the
required checks too, and `REVIEWING.md`'s "hold the merge" excepts it
(issue btclib-org/.github#1597).

### The attestation bundle's name is in the release notes

RELEASE_NOTES.md gives the bundle's name, `v<version>.intoto.jsonl`.
RELEASING.md asks that a change to a release's assets or their verification
be named there (issue btclib-org/.github#1596).

### `check-changelog` refuses an entry added to an older release

A `###` heading under a release older than the newest, absent at the merge
base with `origin/main`, is refused (issue btclib-org/.github#1614).

### The pinned versions move

The pre-commit hook revisions (btclib-org/.github, ruff, pydoclint, uv) and
the `oss-fuzz-base/base-builder-python` image are bumped (#51, #55, #66).

### `CONTRIBUTING.md` and `REVIEWING.md` follow the changelog at release time

A pull request adds no `CHANGELOG.md` or `RELEASE_NOTES.md` entry; the
release's own pull request writes the section. The forms, the template and
`RELEASING.md` follow (issue btclib-org/.github#1623, closes #68).

### `utf8_bytes` raises its refusal outside the `except` block

A mnemonic or passphrase refused for a lone surrogate is no longer kept in
the refusal's `__context__` (GHSA-qjpp-8mp6-7744, #70).

## v2026.10.2

### `REPOSITORY.md` records what each read-back answers

Each read-back carries what it answered on 2026-09-29, and *Read the
Docs* reads back the imported project, the site it serves and the
release `stable` points at (issue btclib-org/btclib-wallet#30).

### `RELEASING.md`'s bundle verification names the signer workflow

The `--bundle` form of *Verify the provenance of an asset* passes
`--signer-workflow "$signer"`, without which `gh attestation verify` refuses
a good release (closes btclib-org/.github#1446).

### `.clusterfuzzlite/.python-version` pins the fuzz image's interpreter

`.clusterfuzzlite/.python-version` names `3.11`, the fuzz image's interpreter,
so that the Dependency Graph's pip job there reads it rather than a root pin
Dependabot does not support yet (issue btclib-org/.github#1436).

### `RELEASING.md`'s griffe step searches `src`

`griffe check` takes `-s . -s src`, the pair `release.yml`'s `public-api`
job passes, where it answered `ModuleNotFoundError` for the previous
release (issue btclib-org/.github#1447).

### `pypi-install.yml` installs the version the release published

The install names `btclib-mnemonics==<version>` from the tag `release.yml` passes,
where a bare name let a lagging index serve the release before it
(issue btclib-org/.github#1456).

### `pypi-install.yml` retries the install of the version the release published

Each install cell retries `pip install btclib-mnemonics==<version>` until a
deadline, while the index does not serve it, where a cell whose edge held the
previous page failed after the wait (issue btclib-org/.github#1458).

### The OpenSSF Baseline badge

`README.md`'s badge row ends with the OpenSSF Baseline badge, beside the
Best Practices badge, section 2 of the organization standard admitting it
on the same property (issue btclib-org/.github#1460).

### `pypi-install.yml` runs its install through `install_published_release.py`

The retry the entry `pypi-install.yml` retries the install of the version the
release published describes now runs as btclib-org/.github's
`install_published_release.py` (issue btclib-org/.github#1458).

### The release's attestation bundle is attached as `*.intoto.jsonl`

`RELEASING.md`'s verification and recovery commands name the bundle
`<tag>.intoto.jsonl`, the name `reusable-github-release.yml` attaches it under
(issue btclib-org/.github#1468).

### `codeql.yml`'s aggregate runs `check_run_jobs.py`

The aggregate's step runs `check_run_jobs.py`, which reads the run's jobs
listing again up to a deadline while a row of `analyze` is unfinished
(issue btclib-org/.github#1463).

### `generate_sbom.py` carries a not-affected list into the bill of materials

`generate_sbom.py` reads `.github/vex.toml`, where the tree lists the
vulnerabilities its release is not affected by, into the document's
`vulnerabilities`; no list, no key (issue btclib-org/.github#1469).

### `SECURITY.md` promises a response time

`SECURITY.md` says a report is acknowledged within 7 days, and a fix or a
published advisory within 90 (issue btclib-org/.github#1460).

### `WordLists.load_lang` honours a replacement file

Given a file for a registered language, `load_lang` loads that file and
records it, where it silently kept the registered word-list (closes #21).

### `release.yml` audits the lock before it publishes

The `audit` job calls btclib-org/.github's `reusable-audit.yml`, which runs
`uv audit` over what the wheel declares, and both publish jobs wait for its
success (issue btclib-org/.github#1466).

### `generate_sbom.py` is btclib-org/.github's

The `dist` job writes the bill of materials with btclib-org/.github's
`generate_sbom.py`, served from `main`, and the tree keeps no copy of it
(issue btclib-org/.github#1478).

### `CLAUDE.md` carries the shared primary-checkout section

The shared section *The primary checkout is the maintainer's* replaces this
tree's, *Model* names only the model, and the draft-pull-request bullet names
`codeql: every job passed` too (issue btclib-org/.github#1494).

### `Dependency review` is a required check

- **`REPOSITORY.md` reads `lint / Dependency review` back with the other
  required checks** (issue btclib-org/.github#1465).

### `[tool.uv] required-version` is `>=0.12.18`

- **`required-version` reads `>=0.12.18`, not `>=0.12.19`** (issue
  btclib-org/.github#1482): the Dependabot service refused `0.12.19` with
  `tool_version_not_supported`.

### `SECURITY.md` names the latest security review

`SECURITY.md` gives the date of the latest security review and links the issue
that records it (issue btclib-org/.github#1362).

### BIP39 refuses 512-bit entropy and 48-word mnemonics

A 512-bit entropy or a 48-word mnemonic is refused, which breaks callers
that pass either (closes #16). A word count outside 12, 15, 18, 21 and 24
is refused before any word is decoded (closes #20).

### Entropy longer than the largest size is refused, not truncated

This holds in every scheme, Electrum's included, which breaks callers that
pass more (closes #15). Dice rolls and the CSPRNG keep the leftmost bits
at their own width, leading zeros included, so their first bit is unbiased.

### SLIP-0039 secrets are 16 to 64 bytes and mnemonics 20 to 59 words

Longer ones are refused, before any word is decoded for a mnemonic, which
breaks callers that pass them (closes #19).

### Every refusal is one of the two exceptions, and none quotes an unknown name

A lone surrogate, an unreadable word-list file and a bad `WordLists` or
`wordlists` argument are refused as the two exceptions. No refusal quotes an
unknown `lang` or `mnemonic_type` (closes #17, closes #18, closes #22).

### The fuzz harness calls every decoder `tests/fuzz_test.py` lists

`fuzz/fuzz_mnemonics.py` calls each decoder in `DECODERS`, a test holds the
two together, and recombination is driven with valid shares (closes #23).

### A `Signed-off-by:` trailer on every commit of a pull request

*Pull requests* says every commit of a pull request carries a
`Signed-off-by:` trailer, and how to add it (issue
btclib-org/.github#1467).

### The primary-checkout section uses one form for the checkout

- **The section writes the checkout as `"${checkout:?}"` throughout, says
  what `<scratchpad>` is and names the pull** (issue
  btclib-org/.github#1500).

### The `python` inventory has a copy kept in the tree

`docs/source/_inventories/python.inv` is read when `docs.python.org` fails,
so an outage of that site no longer fails the `-n -W` docs build (issue
btclib-org/.github#1508).

### The release's attestation is signed by `reusable-build.yml`, at SLSA Build L3

`release.yml` calls `reusable-build.yml`, which signs the files before the
publish jobs wait for approval (issue btclib-org/.github#1506).

## v2026.9.29

### The repository opens

BIP39, SLIP-0039 and Electrum mnemonics, their entropy and the dispatch
telling them apart, moved out of `btclib-wallet` onto the standard
library alone (issue btclib-org/btclib-wallet#30).

### Mnemonic refusals name the parameter and quote no secret

Carried from btclib-org/btclib-wallet#134 to btclib-org/btclib-wallet#137:
a wrong type is a `BTClibMnemonicsTypeError` naming its parameter, and an
unknown word, index, checksum or padding is refused without its content.
