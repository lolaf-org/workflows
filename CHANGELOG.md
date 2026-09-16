# Changelog

All notable changes to these workflows are recorded here, in the format of
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Tags follow
[Semantic Versioning](https://semver.org/spec/v2.0.0.html). For a workflow, a breaking change is a removed or
renamed input or secret, or a changed check name.

## [1.0.0] - 2026-09-16

First version, factored out of the copies ringos, betty and staffix each carried.

- `maven-build.yml`, `maven-release.yml` and `dependabot-auto-merge.yml`, as reusable workflows.
- `maven-release.yml` derives the project name and SCM URL from the calling repository, and refuses to run
  without both versions instead of letting maven-release-plugin guess the next snapshot.
- `dependabot-auto-merge.yml` leaves bumps of this repository for a human.
- `templates/dependabot-common.yml` and a weekly drift check against every consumer.

[1.0.0]: https://github.com/lolaf-org/workflows/releases/tag/v1.0.0
