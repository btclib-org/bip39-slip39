# Security policy

## Reporting a vulnerability

If you have found a security vulnerability, please do not open a GitHub
issue: an issue is public from the moment it is filed, and so is the
window between filing it and a fix being released.

Report it privately instead, by
[opening a security advisory](https://github.com/btclib-org/btclib-mnemonics/security/advisories/new).
Only the maintainers can see it, the discussion stays private until an
advisory is published, and a CVE can be requested from it if the
vulnerability warrants one.

If you have no GitHub account, or would rather not use it for this,
responsible disclosure by email to *security at btclib dot org* is
equally welcome.

A report is acknowledged within 7 days, and a fix or a published advisory
follows within 90 days.

A report triaged as easy to rediscover is fixed as soon as possible, since
anyone can find it in the meantime, and its advisory is published with the
fix.

## What belongs here

Everything this package does: turning entropy into a sentence and a
sentence back into entropy, the seed or master secret a sentence
stretches to, the SLIP-0039 splitting and recombination of a secret, the
recognition of which scheme a sentence belongs to, the word lists it
ships, and the distributions published to PyPI and their provenance. A
refusal that prints a secret is a vulnerability to report here: section 7's
[*A refusal carries no secret*](https://github.com/btclib-org/.github#a-refusal-carries-no-secret)
says what a refusal may print.

A master key derived from a seed is not here: `btclib-wallet` is where
BIP32 is. Report a flaw wherever you found it, though: routing a report
is the maintainers' job, not the reporter's, and a doubt about which
project owns a flaw is not a reason to keep it to yourself.

## Security review

The latest security review is dated 2026-09-30.
[pmazzocchi](https://github.com/pmazzocchi) did it against the
[assurance case](./ASSURANCE_CASE.md), and
[issue 26](https://github.com/btclib-org/btclib-mnemonics/issues/26) records it.

## Supported versions

Only the latest release is supported. Versions are calendar-based
(`YYYY.M.D`), a fix is published as a new release, and nothing is
backported.

Wheels and sdist are published to PyPI with PEP 740 attestations, through
a workflow that no long-lived token can authenticate for (PyPI Trusted
Publishing), so a distribution can be traced back to the workflow run and
the commit it was built from.

The same files are attached to the GitHub release, and those copies carry
a build provenance attestation of their own, signed in the run that built
them:

```shell
signer=btclib-org/.github/.github/workflows/reusable-build.yml
```

```shell
gh attestation verify --repo btclib-org/btclib-mnemonics \
  --signer-workflow "${signer:?}@refs/heads/main" \
  --source-ref refs/tags/v<version> \
  <a distribution file from the release>
```

`--signer-workflow` is what makes that say which workflow signed, rather
than accepting any attestation this repository has: the signing runs in
`btclib-org/.github`'s `reusable-build.yml`, which `release.yml` calls,
and `--source-ref` is what keeps a build of a branch from passing as the
release. A release made before that was signed by `reusable-attest.yml`,
named the same way, with the same `--source-ref`.
A CycloneDX bill of materials is attached beside them, generated from the
built wheel and covered by the same attestation. Either distribution file
can also be rebuilt from its tag and compared, the build being
reproducible: RELEASING.md has that command.

## Limitations, not vulnerabilities

These are known and inherent. They are worth stating because this
package is used to teach and to prototype as much as to build:

- **Secret material lives in Python objects**, which are immutable and
    not zeroized: a mnemonic, an entropy, a seed or a share stays in the
    process memory until garbage collection, and may have been copied by
    the interpreter meanwhile.
- **Nothing here is constant-time.** The package is pure Python, and a
    word list is indexed by the secret's own digits.
- **Randomness comes from the operating system** through `secrets` and
    `os.urandom`, and nothing here seeds a generator of its own.
    `slip39.mnemonics_from_master_secret` takes an `entropy_source`, and
    a weak one a caller passes in is the caller's.
- **Combining SLIP-0039 shares at the largest iteration exponent, 15,
    runs `4 * 2500 * 2**15` PBKDF2-HMAC-SHA256 iterations**;
    `slip39.master_secret_from_mnemonics` refuses shares above the
    `max_iteration_exponent` a caller passes.
- **`entropy.collect_rolls` is interactive**, reading dice rolls with
    `input()` and reporting with `print()`: whatever the terminal keeps,
    it keeps.
