# lolaf-org/workflows

The CI and release machinery shared by the lolaf-org Maven repositories:
[ringos](https://github.com/lolaf-org/ringos), [betty](https://github.com/lolaf-org/betty) and
[staffix](https://github.com/lolaf-org/staffix). Each of them calls these workflows rather than carrying its own
copy.

| workflow | what it does |
|---|---|
| [`maven-build.yml`](.github/workflows/maven-build.yml) | `mvn clean install` on push and pull request; surefire reports on failure |
| [`maven-release.yml`](.github/workflows/maven-release.yml) | `release:prepare` + `release:perform` to the Central Portal, signed, then a GitHub Release from `CHANGELOG.md` |
| [`dependabot-auto-merge.yml`](.github/workflows/dependabot-auto-merge.yml) | auto-merge for Dependabot's patch and minor updates, once the build passes |

The callers to copy are in [`examples/`](examples). Each is a few lines apart from `release.yml`'s dispatch
inputs, which GitHub gives no way to share.

## Using them

```yaml
jobs:
  build:
    uses: lolaf-org/workflows/.github/workflows/maven-build.yml@v1.0.0
```

**Pin an exact tag.** A floating `@v1` or `@main` would change a repository's release job without leaving any
trace in that repository. Dependabot's `github-actions` ecosystem bumps these references like any action's.

**Bumps of this repository are never auto-merged.** A bump pull request runs the new build workflow, but nothing on
a pull request runs the new release workflow. So a human dispatches the consumer's `release` workflow with
`dryRun` on the bump's branch, then merges.

**Tags are never moved.** A fix is a new patch version.

### The check name changes

A job that calls a reusable workflow reports its check as `<caller job> / <called job>`. A caller whose job is
`build` reports **`build / build`**, and that is the name branch protection must require. Switching a repository
over means changing its required check in the same step as the merge. Otherwise every later pull request,
Dependabot's included, waits forever on a `build` check that no longer reports.

## Inputs

### `maven-build.yml`

| input | default | |
|---|---|---|
| `java-version` | `21` | the JDK Maven runs on |
| `toolchain-jdks` | *empty* | extra JDKs for `maven-toolchains`, one per line; ringos passes `11`, `21`, `25` |
| `timeout-minutes` | `20` | job ceiling |
| `maven-args` | `-B -T 1C clean install` | everything after `mvn` |

### `maven-release.yml`

| input | default | |
|---|---|---|
| `release-version` | *empty* | required unless `perform-only` |
| `development-version` | *empty* | required unless `perform-only`; never left to the plugin, which would guess `x.y.(z+1)-SNAPSHOT` |
| `dry-run` | `false` | `release:prepare -DdryRun`, no commit, tag, push or upload |
| `perform-only` | `false` | recovery: deploy an existing `tag` whose `perform` failed |
| `tag` | *empty* | with `perform-only` |
| `java-version`, `toolchain-jdks` | as above | |
| `timeout-minutes` | `45` | `prepare` and `perform` each run a full build |

Secrets, all required, passed with `secrets: inherit`:

| secret | |
|---|---|
| `CI_GITHUB_TOKEN` | a fine-grained PAT with `Contents: read/write`, owned by a repository admin. `release:prepare` pushes to a protected `main` whose required check cannot have run on the release commit, so the push only lands because the pusher is an admin and `enforce_admins` is off. A `GITHUB_TOKEN`, an App token and a deploy key are all refused. This can only be proven by a real push. |
| `GPG_PRIVATE_KEY`, `GPG_PASSPHRASE` | the signing subkey, never the certify-only primary |
| `GPG_KEYNAME` | the **primary** key id, so that gpg picks whichever signing subkey is currently valid |
| `CENTRAL_TOKEN_USERNAME`, `CENTRAL_TOKEN_PASSWORD` | the Central Portal user token |

The calling repository's poms must already carry the release setup this workflow drives: the list is at the top
of [`maven-release.yml`](.github/workflows/maven-release.yml).

### `dependabot-auto-merge.yml`

No inputs. The calling job grants `contents: write` and `pull-requests: write`, and the repository needs
*Allow auto-merge* turned on.

## `dependabot.yml`

It cannot be imported, so each repository keeps its own.
[`templates/dependabot-common.yml`](templates/dependabot-common.yml) is the part they share, and
[`dependabot drift`](.github/workflows/dependabot-drift.yml) checks weekly that every repository's file still
contains all of it. What a repository adds beyond it, such as a benchmark group or a held dependency, is its own.

To check a file locally:

```bash
python3 scripts/dependabot-drift.py --file ../ringos/.github/dependabot.yml
```

To change the shared part, **add** to the consumers first and then to the template. **Remove** from the template
first, then from the consumers.

## License

[Apache License 2.0](LICENSE.txt)
