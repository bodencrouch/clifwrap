# Release process

Releases go through GitHub Actions. This doc is for maintainers.

## CI on every push and PR

Tests run on Python 3.11, 3.12, 3.13, and 3.14:

```bash
python -m nox -s tests-3.11
python -m nox -s tests-3.12
python -m nox -s tests-3.13
python -m nox -s tests-3.14
python -m nox -s lint compile build
```

CI uses the same Nox sessions as `noxfile.py` so local and hosted runs stay aligned. Release verification also checks that generated docs (`docs/cli-reference.md`, `docs/provider-catalog.md`) are up to date.

Release Please PRs get an extra **Release PR Validation** workflow. GitHub sometimes skips ordinary PR workflows when a bot token updates the release branch, so a narrow `pull_request_target` job validates same-repo `github-actions[bot]` release-please branches. The Release Please workflow also dispatches validation against the current release-PR head SHA after it updates an existing PR. Both paths check out the target SHA with `persist-credentials: false`, run the full Python matrix, and keep write permissions out of the job.

The Pages workflow builds an HTML pytest report, JUnit XML, rendered docs, schema files, and `release-summary.json`. Public repos deploy to [th3w1zard1.github.io/clifwrap](https://th3w1zard1.github.io/clifwrap/). Private repos upload `site/` as an Actions artifact instead.

CodeQL runs on pushes, PRs, weekly schedule, and manual dispatch when code scanning is enabled. Private repos without GitHub Advanced Security skip the scan rather than failing every push.

Dependency Review runs on PRs and blocks newly introduced high-severity vulnerabilities when the feature is available. Private repos without it skip the job.

Dependabot opens grouped weekly PRs for Python and GitHub Actions.

## Local validation

```bash
python -m pip install -e ".[dev,release]"
python scripts/verify_release.py
```

Or through Nox:

```bash
python -m pip install -e ".[dev]"
nox
nox -s release-verify -- --require-actionlint
```

Install [actionlint](https://github.com/rhysd/actionlint) locally and pass `--require-actionlint` to fail when semantic workflow linting cannot run. CI downloads and runs actionlint automatically.

The local verifier writes and validates `dist/SHA256SUMS` and `dist/RELEASE-MANIFEST.json` before cleanup. The manifest schema is in `docs/schemas/release-manifest.v1.json` and is published at [release-manifest.v1.json](https://th3w1zard1.github.io/clifwrap/schemas/release-manifest.v1.json).

Pass `--summary-json <path>` for a JSON proof summary after all checks pass (timestamps, platform, completed check names, artifact names).

The verifier also enforces workflow contracts that are easy to break by accident: CI and release validation must cover Python 3.11–3.14; release validation must serialize per tag; binary assets must cover Linux, macOS, and Windows on amd64 and arm64; a release is marked stable only after validation, packages, binaries, and checksums all finish.

## Release Please

[release-please](https://github.com/googleapis/release-please) owns version bumps, changelog updates, tags, and GitHub release creation from conventional commits.

When release-please creates a GitHub release, the workflow gates it before users should treat it as stable:

1. Mark the release `prerelease`.
2. Dispatch `release.yml` with the created tag.
3. Run tests, build Python distributions, build platform binaries, publish checksums and `RELEASE-MANIFEST.json`.
4. Clear `prerelease` only after every required job succeeds.

The explicit dispatch matters because releases created by a workflow token should not rely on follow-on release events to trigger another workflow.

Config files:

- `release-please-config.json`
- `.release-please-manifest.json`

## Binary artifacts

Release validation builds PyInstaller one-file binaries for:

- Linux amd64 and arm64
- macOS amd64 (`macos-15-intel`) and arm64 (`macos-15`)
- Windows amd64 and arm64

Entrypoint: `packaging/pyinstaller/entrypoint.py`.

After Python distributions and platform archives upload, the release workflow downloads the `clifwrap-*` assets, writes `SHA256SUMS` and `RELEASE-MANIFEST.json` (name, size, SHA-256 per artifact), uploads both to the release, then clears the prerelease flag.

## Manual releases

Manual GitHub releases are forced to `prerelease` at validation start. The release workflow runs the full Python matrix, builds artifacts, and marks the release stable only after validation and upload succeed.

Release validation uses a per-tag concurrency group with `cancel-in-progress: false`, so a second dispatch for the same tag queues behind the active run instead of racing or canceling a partial upload.
