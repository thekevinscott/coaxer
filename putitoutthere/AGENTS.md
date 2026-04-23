# Release signaling for Put It Out There

When you finish a unit of work and are preparing a PR or commit, add a git
trailer to the commit message body to signal a release:

    release: <patch|minor|major|skip>

Rules:
- Omit the trailer for docs-only, CI-only, or internal-only changes.
- `patch` for bug fixes or internal refactors that don't change public API.
- `minor` for new features that are backwards-compatible.
- `major` for breaking changes.
- `skip` to suppress release when path filters would otherwise cascade.

The trailer on the merge commit determines the release. If merging via
"Squash and merge," include the trailer in the PR description so it ends up
in the squashed commit body.

## Scoping a release to specific packages

To release a subset of packages in a polyglot repo, append a bracketed list:

    release: minor [dirsql-rust, dirsql-python]

Packages named in the list are bumped with the specified version. Other
packages cascaded by path filters still get a `patch`. Packages in the
list that *aren't* cascaded are force-included.
