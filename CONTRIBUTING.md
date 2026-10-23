# Contributing

What this repository holds in common with the others of the organization
— the toolchain, the lint gate, the tool tables behind it, the workflow
set and the branch rules — is stated once in the
[btclib-org repository standard](https://github.com/btclib-org/.github),
each rule with the alternative it was decided against. It binds this
repository, so a change departing from it is a divergence, and one filed
as an issue in that repository rather than here: a difference between two
repositories belongs to neither of them.

**This file is the same in every repository of the organization up to
its last section.** What is true of one tree only — the commands that
build its environment, the gates it runs, which of its workflows decide
a merge — is under that heading, and the comparison stops there.

How the organization decides, and who holds which role, is
[`GOVERNANCE.md`][governance]; what it intends to do, and what it
deliberately does not, is [`ROADMAP.md`][roadmap]. Both are the
organization's, one copy each beside the standard.

## The issue tracker

Where an issue is filed, and what an alignment finding has to name, is
[the standard's *What this repository is*][s-what]: an issue spanning
repositories, or whose subject is the standard, goes to
[btclib-org/.github](https://github.com/btclib-org/.github/issues), and
one about this tree alone stays here.

A finding noticed while doing something else goes where `REVIEWING.md`'s
*What is filed, and what is not* says, for an author as much as for a
reviewer: a pull request answering two questions cannot be accepted for
either.

An issue labelled `good first issue` is one set aside for a first
contribution: small and self-contained.
[One search][good-first] lists the open ones across the organization, so
a newcomer need not know in advance which repository to look in.

## Documentation and comments

[Section 9 of the standard][s9] is the prose style, and it governs the
prose this tree ships — comments, docstrings and markdown. It is not
restated here: a second wording is the one that goes stale, which is
that section's own *One fact in one place*.

A commit message is prose this tree ships too, though section 9 does not
say so: [the only merge method the rule accepts][s11] puts it on `main`
as the landing commit's body, so what is written in one is read there
long after the branch is gone.

## Pull requests

What `main` accepts, and what it refuses to everyone, is [section 11 of
the standard][s11]. Run the gates locally before opening anything —
the last section of this file says which they are — because CI runs
exactly them, so a red run there is a local run that was not done.

**Every commit of a pull request carries a `Signed-off-by:` trailer
naming its author**, which certifies the [Developer Certificate of
Origin][dco]. `git commit -s` adds it, and `git rebase --signoff <base>`
adds it to commits already made. The `Sign-off` check is required, so a
pull request whose commits lack the trailer cannot merge; its failure
prints the command that adds it. [The standard's *Signatures*][s-sigs]
says why a signature does not replace it, and which commits the
`Sign-off` job skips.

What a pull request's title and description have to say about the issues
it closes, and why a manual link in the Development panel is a trap
neither of them shows, is [the standard's *What a pull request says it
is*][s-title]. Read it before opening one; it is the rule most often
found broken after the fact.

**Before it is opened, the branch's own commit subjects and bodies are
read against that same rule.** The description does not exist yet to
disagree with them, and [the standard][s-title] has the command that
scans the branch's own commit text for a verb in front of a reference.

**The two spellings are named here as well as there, against [section 9's
*One fact in one place*][s9]**, the paragraph above naming the section
and not the forms, which are the half a citation is got wrong in:
`(closes #N)` cites an issue the change closes, wherever the citation
sits — the title, the commit subject where [*Merge method*][s11] makes
that the thing that lands — and `(issue #N)`
cites, in those same places, an issue the change advances and does *not*
close. One token holds one meaning whichever file it sits in, so the
pair is chosen by what is true of the change rather than by which file
is being written, and a tree's own landed subjects are not what to copy
it from: nothing already landed is rewritten, so what a repository wrote
before the rule stays where it is.

`REVIEWING.md` is the standard a review is written against, and is this
file's other half. Read before opening a pull request, it is what the
pull request will be answered against.

A pull request adds no entry to `CHANGELOG.md` or `RELEASE_NOTES.md`, a
release's own pull request excepted ([section 9][s9], [section 12][s12]).

### One subject, opened as soon as it is written

A pull request answers one question. Issues that share a subject are one
pull request, closing each of them; issues that do not are one pull
request each, however small either of them is.

It is opened the moment it is written and verified — not held for the
previous one to be reviewed or to land, and not batched with the next. A
batch arrives as one reviewing job with several subjects, which is the
shape that costs the most to read; a finished pull request held back is
review that could have started and did not.

Working this way stacks branches, which is fine and costs one rule: a
child whose base was amended is moved with the old base named,

```shell
git rebase --onto <new-base> <old-base-sha> <child>
```

because a plain rebase replays the base's old commit inside the child,
and the forge then shows the base's old text as additions with nothing
red anywhere. Read the child's diff afterwards rather than trusting the
rebase, and retarget each child onto `main` as its parent lands.

### The review

A review is given promptly and on local evidence. It does not wait for
CI, does not report a check as a finding, and does not discuss a run at
all: whether CI is green is the author's business, once, at landing time.

The exchange is anchored to a sha rather than to a branch, a branch being
free to move under a review:

- the author hands off by naming the sha pushed and the evidence run
  against it, then leaves that head alone;
- the reviewer answers with findings — where, what is wrong, how they
  know it, and whether each is blocking;
- the author accepts what is reasonable, declines the rest with a reason
  in the thread, pushes the answer without waiting for CI, and resolves
  each thread once answered;
- the reviewer reopens a thread whose finding is still blocking, and
  re-reviews the delta rather than the branch.

**What ends the loop is the ack of record**, and the author does not
supply their own. A reading that says what it found and delivers no
verdict is a review too and ends nothing; [the standard's *Review*][s-rev]
has which is which, and `REVIEWING.md` has how each is written. A
disagreement that survives a second exchange goes to the maintainer
instead of into a third round.

**The ack of record is not the approval *Landing it* asks for**: it is
a bot's review of type COMMENT ([the standard's *Review*][s-rev] says
whose).

### Landing it

CI is read once, and this is where: on the head that lands. `main` does
not ask that head to be up to date with it, and [section 11][s-branch]
says why. So a branch is rebased only where it conflicts with `main`. A
rebase that moved nothing but the base leaves the ack standing; one that
resolved a conflict does not, that resolution being a change no reviewer
has seen.

When `main`'s CI is red after a merge, its repair takes priority over
every other pull request, because until it lands `main`'s runs cannot
tell a new failure from the one already there. A pull request armed with
`--auto` (below) stays armed, and others keep landing meanwhile. Holding
every landing for a repair costs more than the break it guards against,
so the risk of landing on a red `main` is accepted
(btclib-org/.github#1777).

A pull request whose required check is red only because `main` was red
is closed and reopened once the repair lands (`gh pr close <n>`, then
`gh pr reopen <n>`). GitHub then runs its checks on a fresh merge with
the repaired `main`, where a re-run would test the old merge commit. No
push is made, so its approvals and its ack of record stand. `--auto`,
where closing dropped it, is armed again once the checks are green. The
reopen also runs the review bot again, and changes that review requests
are answered like any other review's.

Then squash, [the only method the rule accepts][s11].

**It lands once somebody other than its author has approved that
head**, through `gh pr merge` pinned to it:

```shell
gh pr merge <n> --squash --match-head-commit <the head the checks ran on>
```

With `--auto` added, GitHub runs the same merge once the approval and
the checks are in.

**Where the repository has a bypass, the maintainer may land without
that approval, through it**: [`GOVERNANCE.md`][governance]'s *How a
decision is made* says which repositories.
`--admin` turns off `gh`'s own refusal, and GitHub applies
the bypass to the merge. `enforce_admins` is off, so it waits for no
required check either:

```shell
gh pr merge <n> --squash --admin \
  --match-head-commit <the head the checks ran on>
```

Without `--admin`, `gh pr merge` refuses a head with no approval, saying
it `is not mergeable: the base branch policy prohibits the merge`.

**The pin is not optional**, in either command. Reading the ack and
merging are two calls, and the head is free to move between them — the
push that would move it comes out of the same round the verdict does.
Unpinned, the command takes whatever sits at the head when it runs;
pinned, it refuses a head that has moved, and a round lost that way is
cheaper than a tree nobody has read reaching `main`.
*The review* above anchors the exchange to a sha and [section 11][s11]
has an ack name one: the pin is that rule reaching the call that
performs the landing.

**Verify what landed rather than trusting the answer**, the signature
[the standard asks for][s-sigs] being a valid one rather than a
particular signer's:

```shell
gh api repos/{owner}/{repo}/commits/main \
  --jq '.commit.verification | {verified, reason}'
```

**What it closed is read again here too, from the landed sha rather
than from the pull request**: [the standard's *What a pull request says
it is*][s-title] has the second read, and why the first alone does not
reach a squash subject composed after it runs.

The forge deletes the head branch itself, per the setting section 11
names. What is still yours is bringing every checkout sitting on `main`
up to date,
that being where the next session starts from and a stale one being where
a branch gets built on a base that has moved. `REPOSITORY.md` carries the
settings and why they are what they are.

[s-what]: https://github.com/btclib-org/.github#what-this-repository-is
[s11]: https://github.com/btclib-org/.github#11-github-settings
[s9]: https://github.com/btclib-org/.github#9-prose-comments-and-docstrings
[s12]: https://github.com/btclib-org/.github#12-releasing
[s-title]: https://github.com/btclib-org/.github#what-a-pull-request-says-it-is
[s-rev]: https://github.com/btclib-org/.github#review
[s-sigs]: https://github.com/btclib-org/.github#signatures
[s-branch]: https://github.com/btclib-org/.github#branch-protection-and-rulesets
[dco]: https://developercertificate.org/
[governance]: https://github.com/btclib-org/.github/blob/main/GOVERNANCE.md
[roadmap]: https://github.com/btclib-org/.github/blob/main/ROADMAP.md
[good-first]: https://github.com/search?q=org%3Abtclib-org+label%3A%22good+first+issue%22+is%3Aopen&type=issues

## Worktrees

Run `git fetch origin` in the primary checkout, then check that
`git status --porcelain` is empty and `git branch --show-current` is
`main`. Run `git pull --ff-only` only when both checks pass, then verify
`git rev-parse HEAD origin/main` prints the same sha twice. Create a separate
worktree for each task with
`git worktree add <path> origin/main -b <branch>`. After committing,
remove it with `git worktree remove <path>`. If initialized submodules
make that fail,
check for uncommitted, untracked, and ignored files in the worktree and
its initialized submodules. Preserve anything needed before retrying with
`git worktree remove --force <path>`; it can delete those files. Keep the
primary checkout clean and on `main`; do not
switch branches or stash there. Hooks can fix files in place, and the local
`main` and `refs/stash` are shared by all worktrees.

## This repository in particular

Everything above is the same file in every repository of the
organization; everything below is this one's, and the comparison stops at
this heading.

<!-- The toolchain badges are here rather than in the README because they
report no state: each names a choice, and this is the file that says how
the choice is enforced and what the command for it is. The README keeps
the badges that can turn red. --> [![calendar versioning:
yyyy.m.d](<https://img.shields.io/badge/cal_ver-yyyy.m.d-1674b1.svg?logo=calver>)](<https://calver.org/>)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![format:
ruff](https://img.shields.io/badge/format-ruff-yellowgreen.svg?logo=ruff)](https://docs.astral.sh/ruff/formatter/)
[![lint:
ruff](https://img.shields.io/badge/lint-ruff-yellowgreen.svg?logo=ruff)](https://docs.astral.sh/ruff/)
[![docstrings:
ruff](https://img.shields.io/badge/docstrings-ruff-yellowgreen.svg?logo=ruff)](https://docs.astral.sh/ruff/rules/#pydocstyle-d)
[![type check:
mypy](https://img.shields.io/badge/type_check-mypy-yellowgreen.svg?logo=mypy)](https://mypy-lang.org/)
[![lint:
markdownlint-cli2](https://img.shields.io/badge/lint-markdownlint--cli2-yellowgreen.svg?logo=markdown)](https://github.com/DavidAnson/markdownlint-cli2)
[![pre-commit
enabled](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)
[![GitHub repository:
btclib-org/bip39-slip39](https://img.shields.io/badge/GitHub-btclib--org%2Fbip39--slip39-181717?logo=github)](https://github.com/btclib-org/bip39-slip39/)

To get an overview of the project, read the [README](./README.md).

### The public surface

**Every module and every package declares `__all__`**, at every depth of
the tree. A name is public here because a list says so, not because it
happens to lack a leading underscore. An empty list is a legitimate
answer, for a module with nothing public of its own; declaring nothing is
not. For a package the list is what the `__init__` publishes, submodules
included; for a module it is what the module itself defines, a name it
imported belonging to the module that defines it.
`bip39_slip39.__all__` is the root of that tree, written out rather
than discovered, so that a new module is published by somebody deciding
to. `tests/all_test.py` checks all of this and finds the modules rather
than listing them: a public name kept out of a list is recorded in its
`UNEXPORTED` table.

**The package imports nothing outside the standard library.** A mnemonic
is words, a word list and a key-stretching function, and `hashlib`,
`hmac` and `unicodedata` carry all three. `tests/imports_test.py` imports
each module alone and refuses one that loads a module neither the
standard library's nor this package's. The coercions `_utils.py` needs
are copies of btclib's, and `tests/utils_test.py` hands the copy and the
original the same inputs, btclib being a test dependency for that reason
alone.

**Every public function validates its inputs.** Whatever it is handed — a
sentence, an entropy, octets, or a `Share` somebody built earlier — a name
a caller can reach checks it before acting on it, and a malformed
argument leaves as a `Bip39Slip39TypeError` or a
`Bip39Slip39ValueError`, each beside the built-in of its name so that
a caller catching `ValueError` still catches it.
`tests/input_validation_test.py` drives the rule over every public
function whose required parameters are all package input types, and
`tests/exceptions_test.py` holds the classes to that shape.

**A value of a type the signature does not declare is the caller's own
mistake**, a call mypy already refuses, and it leaves as a
`Bip39Slip39TypeError`; a value of a declared type that no valid
input carries is a fact about the input and leaves as a
`Bip39Slip39ValueError`. The line is the annotation, and deliberately
not which built-in a helper happens to derive from: those two coincide
only by accident (btclib-org/btclib#745).

**A `bool` parameter is a kind or a truth, and only the first is
type-checked.** A flag that decides *what is computed* refuses a
non-bool: a kind written down and read back — json, a configuration
file, a coordinator's message — arrives as whatever it was written as,
and `"false"` is true. A flag that decides only *whether a check runs* is
read for its truth: `bip39.seed_from_mnemonic`'s `verify_checksum`
either checks the checksum or skips it, and the seed is the same either
way.

**A truth's `True` has to be its conservative value**
(btclib-org/btclib#884). Most wrong values are true, and for those the
misreading is the one the flag's `True` stands for. So a flag whose
`True` is the permissive value is a kind however little it computes,
because the misreading waives the very refusal it was written to make.
`0`, `None` and `""` are wrong values that read as `False`, so on a truth
they fall on the permissive side, and the rule gives them no protection.

**Which of the two a flag is, is written down for every one of them.**
`tests/bool_parameter_test.py` is the census: two tables, a kind driven
until it refuses `"no"`, `0` and `1`, a truth driven until it accepts all
three, and a walk that fails on a `bool` parameter in neither table. So a
flag added anywhere is a decision somebody makes rather than one the
default makes for them — and `0` and `1` are in that vocabulary because
`bool` is a subclass of `int`, which is what leaves `isinstance(value,
int)` no check at all here.

**An integer field refuses a `bool` too**, for the same reason read the
other way: json's `true` would be a roll of one, an index of one or a
threshold of one. `_utils.is_integer` is that policy, and
`tests/integer_policy_test.py` is its census.

**What a function answers, its name says**, and the vocabulary is
closed: a public function that answers a `bool` carries one of the
prefixes below, and one that carries a prefix answers what the prefix
promises. `tests/name_contract_test.py` is that gate.

- `assert_*` refuses and returns `None`.
- `is_*` answers a `bool` about a value, and is total over the declared
  types.
- `verify*` answers a `bool` about a signature or a proof, on the same
  terms.
- `check_*` answers a `bool` **and refuses what cannot be an answer** --
  the one prefix that warns a caller it still needs an `except`.

A converter is named for what it returns -- `seed_from_mnemonic`,
`mnemonic_from_share` -- and a query for what it answers.

**A member that takes nothing but `self` is a `@property`**, whatever it
answers, and that is gated too: it is read off the object rather than
called. What is *not* a read is exempt by shape rather than by a list of
names: `assert_*` refuses, and a property that refuses is a trap, since
reading `share.assert_valid` evaluates the method and throws it away.

**The leading underscore means what it means anywhere in Python:
private.** `__all__` is what decides publicity, so it is a reader's hint
rather than the rule, but an unvalidating twin belongs on the private side
of that list, and calling one asserts that its caller validated.

**A private function takes no default argument either**, which is the
same absence of an outside caller read the other way: a default is
written for one the author cannot see, and there is none here. So the
value the call is made with is at the call site, where it is read —
`slip39._feistel`'s `decrypt` decides which way the network runs.
`tests/private_defaults_test.py` is the gate, and its docstring carries
what the rule does not reach.

**A keyword-only parameter stays keyword-only**, and
`tests/keyword_only_test.py` freezes which ones are.

### The environment and the gates

uv is the only tool that must be installed; it fetches interpreters,
linters and packaging tools itself. `uv sync` creates the environment.

```shell
uv sync
```

No test reaches the network. [tests/README.md](./tests/README.md) is
where the suite and its switches are described.

The gate is the suite, the hooks and the documentation build:

```shell
uv run pytest
uv run pre-commit run --all-files
uv run --locked --no-default-groups --group docs \
    sphinx-build -n -W -b html docs/source docs/build/html
```

`--cov` is in `addopts`, so the bare `pytest` above is the coverage gate
and `fail_under` is what it answers against — 100%, and coverage takes
that literally: a statement or a branch no test reaches fails it. A
selective run is reported and not gated, and `tests/conftest.py`'s
`coverage_fail_under` is what makes that difference.

The documentation build is the one to remember, because no hook reads
reStructuredText: a docstring docutils cannot parse fails it with every
hook green — a name ending in an underscore is a reference to a link
target, and the fix is double backticks around it. `-n` turns an
unresolved cross-reference into a warning for `-W` to fail on, and
`conf.py`'s `intersphinx_mapping` is what resolves a reference into the
standard library.

**Every job that installs from `uv.lock` passes `--locked`.** The jobs
that do not are deliberate:

- `deps-latest.yml` runs `uv lock --upgrade` to test the newest versions,
  and `deps-oldest.yml` calls `reusable-deps-oldest.yml`, which re-locks to
  the floors; neither commits the lock.
- `pypi-install.yml` runs `pip install` to test the published release.
- `fuzz.yml`'s ClusterFuzzLite build installs
  `.clusterfuzzlite/requirements.txt`, the lock exported with its hashes by
  the `uv-export` hook, with `pip3 install --require-hashes`.
- `test.yml`'s `dist` job smoke-tests the wheel with `uv pip install`; the
  package has no runtime dependency, so it installs the wheel alone.
- `uv build` and `uv run --no-project` install none of the project's
  dependencies.
- The `dev-version` action re-locks after writing a rehearsal's version
  suffix; `uv lock` keeps the versions already locked.
- `public-api`, in btclib-org/.github's `reusable-public-api.yml`, runs
  `uvx griffe==2.2.0`: a pinned version, with its own dependencies
  unlocked.

**Check exit codes, not filtered output.** `pre-commit run ... | grep -v
Passed` hides a failure, and `grep` finding nothing exits 1, which is not
the gate's answer to anything.

**The lint gate is not installed as a git hook.** `pre-commit install`
writes into the common git directory, which every worktree of this
repository shares: `git -C <worktree> rev-parse --git-path hooks` answers
with the primary checkout's `.git/hooks` from every one of them. So one
session installing it installs it for every other. Run the gate by hand
before committing — the `uv run pre-commit run --all-files` above.

**Prefix any `--python <version>` command with
`UV_PROJECT_ENVIRONMENT=.venv-<version>`, naming the interpreter that
command selects — `.venv-3.11` for `--python 3.11`, `.venv-pypy3.11` for
`--python pypy3.11`.** Without it, `uv run --python <version>` removes
`.venv`, builds it again on that interpreter and with that command's own
group set, and leaves it there. `uv sync` restores it.

### A Dependabot `uv` pull request

Dependabot's `uv` ecosystem rewrites `uv.lock` alone. Where a bump moves a
package that `.clusterfuzzlite/requirements.txt` pins, the `uv-export`
hook fails the lint job. An owner, as [`GOVERNANCE.md`][governance] names them,
then commits the hook's output to the pull request's branch before it
lands, signed and signed off. On a checkout of that branch:

```shell
uv run --locked --only-group lint pre-commit run uv-export --all-files
git commit -S -s -m "Export .clusterfuzzlite/requirements.txt from uv.lock" \
    .clusterfuzzlite/requirements.txt
git push origin HEAD:<branch>
```

The hook exits 1 when it rewrites the file. The push is a plain one, never
a force, so a branch that moved meanwhile refuses it.

The commit is made by hand, not by a bot: the `ci:` block of
`.pre-commit-config.yaml` says why.

The cost is that Dependabot stops rebasing a pull request once extra
commits have been pushed to it, as
[GitHub's documentation](https://docs.github.com/en/code-security/how-tos/secure-your-supply-chain/manage-your-dependency-security/manage-dependabot-prs#allowing-dependabot-to-rebase-and-force-push-over-extra-commits)
says. `@dependabot recreate` in a comment rebuilds the branch without the
commit, which is then made again.

### The editor

`.vscode/settings.json` and `.vscode/extensions.json` are tracked, and they
hold no preference: the recommended extensions are the tools
`.pre-commit-config.yaml` already runs, and the settings put the fixing ones
on save. Installing them is optional and changes nothing about what a local
run enforces.

Anything machine-local — an interpreter path, a telemetry answer, a theme —
belongs in the editor's own user settings instead, those two files being
read by every checkout of this repository.

### Reproducing what CI runs

Each command below is the one a CI job runs. Keep this section true when a
workflow changes.

`os-ubuntu.yml`, `os-macos.yml`, `os-windows.yml` and `deps-oldest.yml`,
the suite job of each — the suite, on one cell of a matrix. `--no-cov`
undoes the `--cov` addopts carries, the `coverage` job below being where
coverage is measured and gated:

```shell
uv run --locked --no-default-groups --group test pytest --no-cov
```

`test.yml`, the `coverage` job, the gate the bare `pytest` above is:

```shell
uv run --locked --no-default-groups --group test pytest
```

`test.yml`, the `dist` job — build the distribution files, check them and
install one. `release.yml`'s `test` job calls this workflow, which then
checks the files `reusable-build.yml` built and uploaded instead of
building its own. `release.yml`'s publish jobs download that `dist`
artifact, so what
the checks below judge is what an index ends up serving. `normalize_sdist.py`
is what puts the commit's own time into every member of the sdist, and
its docstring says why the backend's archive is not published as it
stands; `sha256sum` after it is the digest a rebuild from the tag is
compared against, per RELEASING.md's
[Rebuild a release from its tag](./RELEASING.md#rebuild-a-release-from-its-tag).
`generate_sbom.py` writes the CycloneDX bill of materials into `sbom/`,
which `reusable-build.yml`'s `attest` job signs beside the two files on a
release. It is
btclib-org/.github's, served from `main`, and reads this tree from the
working directory, so the commands fetch it first:

```shell
export SOURCE_DATE_EPOCH=$(git log -1 --pretty=%ct)
uv build
uv run --no-project --python 3.15 .github/scripts/normalize_sdist.py dist/
sha256sum dist/*
served=$(mktemp -d)
git clone --depth 1 --filter=blob:none --sparse \
    https://github.com/btclib-org/.github "$served"
git -C "$served" sparse-checkout set .github/scripts
uv run --no-project --python 3.15 \
    "$served"/.github/scripts/generate_sbom.py dist/ sbom/
uv run --locked --only-group check twine check --strict dist/*
uv run --locked --only-group check check-wheel-contents dist/*.whl
uv run --locked --only-group check pyroma --min 10 dist/*.tar.gz
```

The job then installs the wheel it just built from an empty directory,
reads the version back, and reads a mnemonic to its seed, which opens a
word list: an import alone would pass a wheel missing `_data/`:

```shell
tmp=$(mktemp -d)
set -- "$PWD"/dist/*.whl
cd "$tmp"
uv venv
uv pip install "$1"
.venv/bin/python -c "
from importlib.metadata import requires, version
import bip39_slip39
from bip39_slip39 import bip39

print(version('bip39-slip39'), requires('bip39-slip39'))
assert bip39_slip39.__version__ == version('bip39-slip39')
mnemonic = bip39.mnemonic_from_entropy(bytes(16))
assert mnemonic.split()[-1] == 'about'
assert bip39.seed_from_mnemonic(mnemonic, 'TREZOR').hex().startswith('c55257c3')
"
```

Last, it unpacks the sdist outside the checkout and runs the suite
there, under the coverage job's floor; from the checkout's root:

```shell
tmp=$(mktemp -d)
tar -xzf dist/*.tar.gz -C "$tmp" --strip-components=1
cd "$tmp"
uv run --locked --python 3.15 --no-default-groups --group test pytest
```

`lint.yml`, the `lint` job — this file *is* the lint gate, so there is no
second list of tools anywhere:

```shell
uv run --locked --only-group lint \
    pre-commit run --all-files --show-diff-on-failure
```

`docs.yml`, the `docs` job — the build, and then a read of the pages it
wrote:

```shell
uv run --locked --no-default-groups --group docs \
    sphinx-build -n -W -b html docs/source docs/build/html
if grep -rn 'href="#\.\.\?/' docs/build/html --include='*.html'; then
    echo "::error::the links above resolve to no page (unresolved relative path)"
    exit 1
fi
```

What myst renders for a destination it cannot resolve is an anchor to an
id no page has. `-W` reports it because `docs/source/conf.py` resolves the
links the included root files carry and suppresses no myst warning; the
`grep` is what still finds one the day a suppression goes back in.

`codeql.yml` has no line here: its jobs run `github/codeql-action` and no
command of this project's, so reproducing it locally means the CodeQL CLI
and a database rather than a `uv run`.

### What gates a merge, and what only reports

`lint.yml`, `test.yml` and `docs.yml` produce the required checks, and
`REPOSITORY.md` reads the rule back from the endpoint rather than
restating it. So a diff does not reach a review without having passed
them or passing them beside it on the same sha, which is the reliance
`REVIEWING.md` provides for.

| workflow | when | what it varies |
| --- | --- | --- |
| `test` | pull request, push | — |
| `lint`, `docs` | pull request, push | — |
| `claude-review` | pull request, and `@claude` in a comment | — |
| `api-break` | pull request | — |
| `verified-signatures` | push to main | — |
| `codeql` | pull request, push, and weekly | the languages |
| `os-ubuntu` | weekly, a release | images × interpreters |
| `os-macos` | weekly, a release | images × interpreters |
| `os-windows` | weekly, a release | images × interpreters |
| `deps-latest` | weekly | dependencies upgraded |
| `deps-oldest` | weekly | the floor interpreter, dependencies at their floors |
| `scorecard` | weekly, push to main | — |
| `links` | weekly | — |
| `mutation` | weekly | the `.github/mutation/` profiles |
| `fuzz` | weekly, and by hand before a release | — |
| `vendored-vectors` | weekly | the pin ledger |
| `pypi-install` | weekly, a release | what PyPI serves |
| `sdist-rebuild` | weekly | the latest release's sdist, rebuilt |
| `release` | a tag, and a rehearsal | the workflows it calls |

Which workflows that last row covers is
`grep -n 'uses: \./\.github/workflows/' .github/workflows/release.yml`,
not a list here. Which day each of the rest runs is section 10 of
[the organization standard](https://github.com/btclib-org/.github), and
not this file's to restate.

The gates run one image on one interpreter: `ubuntu-latest`, and the
version `.python-version` names. `claude-review` gates nothing: a review
that gates a merge would make a model's judgement a branch rule. Why so
little gates is the ceiling on concurrent jobs the plan puts on the whole
organization, and `REPOSITORY.md`'s *Plan-gated settings* is where that
lives.
`verified-signatures.yml` reports after each push to `main` whether every
commit pushed is `verified`; [the standard's *Signatures*][s-sigs] has the rule.

### The secrets baseline

`detect-secrets` reads `.secrets.baseline` to decide which findings have
already been reviewed, and adding a finding means regenerating it. The command
preserves the plugin selection the file already carries, which is
deliberate: the two entropy plugins are off, because in vectors made of
hex seeds and entropies a new high-entropy string is what a legitimate
addition looks like:

```shell
uvx detect-secrets scan --baseline .secrets.baseline
uv run --locked --only-group lint pre-commit run detect-secrets --all-files
```

Read the diff before committing it: a new entry is a finding somebody has
to have looked at, which is the whole point of a baseline over an
exclusion.
