---
name: bisos-pip-release
description: Use when preparing a bisos-pip package for release to PyPI — bumping the version, running the release-time linters (pyflakes, flake8, pylint, pycodestyle, mypy), building the sdist/wheel via `pypiProc.sh` (which handles README.org → README.rst regeneration automatically), and uploading. Also covers the pipx install verification step and the Test-PyPI trial-upload workflow.
---

# bisos-pip Release Preparation

Each bisos-pip repo follows the same packaging structure and release
workflow driven by `py3/setup.py` and `py3/pypiProc.sh`. This skill covers
the end-to-end release checklist for a command-only PyCS package.

## Prerequisites

- `~/.pypirc` configured with credentials for both PyPI and Test-PyPI
- The repo's `AI-WorkPlan.org` and `AI-DevStatus.org` are up to date and
  reflect a stable release candidate
- All commits merged to the working branch; `git status` is clean

## Release-time linters

Linting is done **at release time**, not continuously. The linters live in
`/bisos/pipx/bin/`:

| Linter          | Purpose                                            |
|-----------------|----------------------------------------------------|
| `pyflakes`      | Undefined names, unused imports, obvious errors   |
| `flake8`        | Style + pyflakes + complexity                     |
| `pycodestyle`   | PEP 8 style                                       |
| `pylint`        | Deeper static analysis                            |
| `mypy`          | Type checking (uses `.mypy_cache/` for py3.11)   |

Run each against the package's Python source:

```bash
cd py3
/bisos/pipx/bin/pyflakes bisos/<pkgname>/ bin/*.cs
/bisos/pipx/bin/flake8    bisos/<pkgname>/ bin/*.cs
/bisos/pipx/bin/pycodestyle bisos/<pkgname>/ bin/*.cs
/bisos/pipx/bin/pylint    bisos/<pkgname>/ bin/*.cs
/bisos/pipx/bin/mypy      bisos/<pkgname>/
```

Address findings before proceeding. In BISOS, we do NOT gate every commit
on lint-clean — but a PyPI release should be.

## Release checklist

**1. Update the version.** In `py3/setup.py`, bump the `version=` string.
Convention: `0.1`, `0.2`, ..., `1.0` — no patch versions unless a hotfix.
Also bump `csInfo['version']` inside the main `.cs` file (the value looks
like `'202507111200'` — set to current YYYYMMDDHHmm).

**2. Regenerate `py3/README.rst` from `README.org` via `pypiProc.sh`.**
`README.rst` is what PyPI displays. It is generated (never hand-authored):

```bash
cd py3
./pypiProc.sh -i fullPrep     # updates _description + README.rst from ../README.org
```

`fullPrep` is also invoked automatically by `fullPrepBuild forPypi` (step 6),
so an explicit call here is only needed if you want to inspect the
regenerated `README.rst` before building. See the `readme-authorship` skill
for details on the generation model.

**3. Regenerate Blee-Panel captured output.** If any `runResult` dblocks in
`py3/panels/<pkg>/_nodeBase_/fullUsagePanel-en.org` reference commands
whose behavior changed, open the panel in Blee and "Update Buf Dblocks".
See the `blee-panel-authorship` skill.

**4. Update `AI-DevStatus.org`.** Reflect the release-candidate state:
what works, what is untested, key design decisions since last release.

**5. Run linters.** Address findings. See the linter table above.

**6. Trial upload to Test-PyPI first via `pypiProc.sh`.**

`pypiProc.sh` drives the whole flow. `fullPrepBuild forPypi` calls
`fullPrep` (README.rst + _description regeneration) and then builds the
sdist/wheel:

```bash
cd py3
./pypiProc.sh -i fullPrepBuild forPypi        # regen artifacts + build
twine check dist/*                            # RST validation for PyPI display
twine upload --repository testpypi dist/*
```

Inspect `pypiProc.sh -i examples` for the full command menu (upload flags,
version bumping, artifact refresh, etc.) — the driver has many modes.

Verify on Test-PyPI:

```bash
pipx install --index-url https://test.pypi.org/simple/ \
             --pip-args="--extra-index-url https://pypi.org/simple/" \
             bisos.<pkgname>
```

Run one or two of the package's commands to smoke-test. If the Test-PyPI
package works, proceed to real PyPI.

**7. Upload to PyPI.**

```bash
cd py3
twine upload dist/*
```

**8. Verify pipx install from real PyPI.**

```bash
pipx uninstall bisos.<pkgname>    # if a Test-PyPI copy is installed
pipx install bisos.<pkgname>
<pkgname>.cs -i examples          # or another quick smoke command
```

**9. Tag the release in git.**

```bash
git tag -a v<version> -m "Release <version>"
```

Suggest the developer push the tag — do NOT push it yourself. Per BISOS
convention, all `git push` operations are done by the developer.

**10. Update `AI-WorkPlan.org`.** Close out the release TODO, add any
follow-up items surfaced by the release.

## `pypiProc.sh` — the driver script

Every bisos-pip repo has `py3/pypiProc.sh`. It is a thin wrapper that
loads `/bisos/core/bsip/bin/seedPypiProc.sh` (the shared seed) and drives
the full release pipeline. Key commands (see `./pypiProc.sh -i examples`
for the complete menu):

- **`fullPrep`** — regenerate `_description` and `README.rst` from
  `../README.org`. Idempotent; safe to run any time.
- **`fullPrepBuild forPypi`** — full path: `fullPrep` + sdist/wheel
  build, with the PyPI version increment.
- **`fullPrepBuild forLocal`** — same but for a local install version
  (does not bump PyPI version).
- **`distBuild`** — bare `python3 -m build` (no `fullPrep` — use only
  when artifacts are already current).
- **`artifactsList`** / **`artifactsUpdate`** — list / refresh the
  package's boilerplate files (setup.py template, .gitignore, etc.).
- **`readmeToDescriptionOrg ../README.org ./_description.org`** — the
  `README.org` → `_description.org` conversion step used inside `fullPrep`.

The generation of `README.rst` from `README.org` is done by `fullPrep`
via pandoc under the hood (`pandoc --from=org -s -t rst --toc README.org
-o README.rst`), but **do not invoke pandoc directly** — go through
`pypiProc.sh` so associated artifacts stay in sync.

## Common pitfalls

- **Hand-edited `README.rst`** → gets overwritten silently by `fullPrep`.
  Always edit `README.org`; run `pypiProc.sh -i fullPrep` to regenerate.
- **`README.rst` malformed** → PyPI page shows plain text. Run
  `twine check dist/*` before every upload; it validates RST. If the
  RST is bad, the fix is in `README.org` (source), not in `README.rst`
  (generated).
- **Skipped `fullPrep` before upload** → PyPI page shows a stale README
  (last-generated content). Always run `fullPrepBuild forPypi` (which
  includes `fullPrep`) rather than `distBuild` alone.
- **`long_description` missing from `setup.py`** → PyPI page is empty. Ensure
  `setup.py` reads `py3/README.rst` into `long_description` and sets
  `long_description_content_type="text/x-rst"`.
- **Version not bumped** → `twine upload` fails with "file already exists".
  PyPI does not allow re-uploading an existing version.
- **Blee-panel captured output is stale** → users see wrong examples in
  Blee. Regenerate before releasing.
- **`bisos.b` dependency version too old** — if the release requires a
  feature added to `bisos.b` recently (e.g., `parPermanence="userConfig"`),
  pin the minimum version in `setup.py`'s `install_requires`. Do NOT
  release against an unreleased `bisos.b`.
- **`.cs` file not `chmod +x`** in the source tree — the sdist preserves
  permissions; fix before packaging.

## Post-release: fresh-Debian pipx test

For confidence that the package works outside BISOS, install on a fresh
Debian machine (or vagrant VM) via `pipx install bisos.<pkgname>` and run
the smoke commands. This is Stage 9 in the workflow — track it in
`AI-WorkPlan.org` rather than blocking the PyPI release on it.

## What NOT to do

- Do NOT skip the Test-PyPI trial upload for a first release or a major
  version bump. PyPI won't let you delete or re-upload a bad version.
- Do NOT `twine upload` without running `twine check dist/*` first.
- Do NOT edit `py3/README.rst` directly — it is generated by `fullPrep`.
  Edit `README.org` instead.
- Do NOT invoke `pandoc` yourself to regenerate `README.rst` — go through
  `pypiProc.sh -i fullPrep`.
- Do NOT skip `fullPrep` (or `fullPrepBuild forPypi`) before uploading —
  otherwise PyPI shows a stale README.
- Do NOT push the git tag on the developer's behalf — suggest they push.
- Do NOT release with failing linters. Fix the findings first; if a
  specific check is intentionally suppressed, document why in the source.

## References

- bisos-pip packaging machinery panel:
  `/bisos/panels/bisos-core/PyCsFwrk/bisos-pip-packaging/_nodeBase_/fullUsagePanel-en.org`
- Comprehensive bisos-pip README:
  `/bisos/git/bxRepos/bisos-pip/_github/profile/readme.org`
- Every bisos-pip repo's `py3/pypiProc.sh` and `py3/setup.py` — read the
  target repo's own driver before running
- Complementary skills: `readme-authorship`, `blee-panel-authorship`
