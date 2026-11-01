---
name: icm-to-pycs-conversion
description: Use when converting a Bash-ICM library (a `*_lib.sh` file under /bisos/core/bsip/bin/, built from `vis_*` functions, `G_funcEntry`, `EH_assert`, `FN_*` helpers, sourced via the seedActions.bash dispatch) into PyCS `cs.Cmnd` classes in a `_csu.py` module. Covers the idiom mapping table, how to pick the right target csu module (don't default to the first module you find — check which one is actually loaded by the relevant `.cs` binary's csuList), the copy-vs-move rule when a related pip package already has overlapping code, and common pitfalls. Load `writing-cs-commands` first for the `cs.Cmnd` class shape itself.
---

# Bash-ICM to PyCS Conversion

BISOS carries a large body of legacy Bash-ICM ("Interactively Callable
Module") libraries under `/bisos/core/bsip/bin/*_lib.sh` (55+ files, using
the `vis_*` function-naming convention). As BISOS capabilities move to
PyCS, these get converted function-by-function into `cs.Cmnd` subclasses
in a package's `_csu.py` module. This is a recurring task, not a one-off —
this skill captures the mapping and the judgment calls involved.

## Recognizing a Bash-ICM library

Signs a `.sh` file is a Bash-ICM library meant for conversion:

- Function names prefixed `vis_` (Interactively Invokable Functions).
- `G_funcEntry` / `describeF { G_funcEntryShow; ... }` boilerplate at the
  top of each function (ICM's self-documenting entry/describe pattern).
- `EH_assert [[ ... ]]` for argument-count/precondition checks.
- `FN_*` helper calls, most commonly:
  - `FN_absolutePathGet ~someAcctId` — resolve a BXO/account id to its home
    directory path.
  - `FN_fileSymlinkUpdate <target> <symlinkPath>` — create-or-replace a
    symlink.
  - `FN_dirCreatePathIfNotThere <path>` — mkdir -p equivalent.
- `lpDo <cmd>` wrapping most side-effecting calls (ICM's logged/dry-run
  wrapper).
- A `bx:dblock:bash:end-of-file` dblock closing the file.

None of this is Python-visible machinery — it's the Bash-ICM analog of
COMEEGA/dblock structure, and none of it should be preserved verbatim in
the PyCS conversion. See the `comeega-authorship` skill for the Python-side
equivalent conventions the converted code must follow instead.

## Idiom mapping table

| Bash-ICM                                           | PyCS equivalent                                                                | Notes                                                                                                                                                                                                                |
|----------------------------------------------------|--------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `function vis_fooBar { ... }`                      | `class fooBar(cs.Cmnd): ...`                                                   | Drop the `vis_` prefix; the Cmnd name is the bare concept name.                                                                                                                                                      |
| `G_funcEntry` / `describeF`                        | `self.cmndDocStr(""" ... """)`                                                 | The docstring block plus the generated `classHead` dblock together replace both entry-tracking and self-description.                                                                                                 |
| `EH_assert [[ $# -eq N ]]`                         | `cmndArgsLen = {'Min': N, 'Max': N,}` + `cmndArgsSpec()`                       | Argument-count checking is declarative, not an inline assert.                                                                                                                                                        |
| `EH_assert <expr>` (general)                       | early-return via `failed = b_io.eh.badOutcome; ... return failed(cmndOutcome)` |                                                                                                                                                                                                                      |
| `FN_absolutePathGet ~acctId`                       | `bpo.bpoBaseDir_obtain(bpoId)` (`from bisos.bpo import bpo`)                   | Handles path / homeDir / acctId id-forms; do not hand-roll `os.path.expanduser`.                                                                                                                                     |
| `FN_fileSymlinkUpdate <target> <link>`             | `pathPlus.symlink_update(target, link)` (`from bisos.basics import pathPlus`)  | Validates target exists, removes any existing symlink, re-links. Argument order is `(target, symlinkPath)`, same as the Bash form.                                                                                   |
| `FN_dirCreatePathIfNotThere <dir>`                 | `Path(dir).mkdir(parents=True, exist_ok=True)`                                 | Plain `pathlib`, no wrapper needed.                                                                                                                                                                                  |
| `lpDo <cmd>`                                       | Just call the Python function/Cmnd directly                                    | PyCS's `cs.track` decorator + `b.subProc.Op(...).bash(...)` (for actual shell calls) already provide logging; there is no separate "do" wrapper.                                                                     |
| `echo <value>` (function "return" via stdout)      | `return cmndOutcome.set(opResults=<value>)`                                    | PyCS Cmnds return structured outcomes, not stdout text.                                                                                                                                                              |
| function calling another `vis_*` function directly | `OtherCmnd().pyCmnd(argsList=[...])`                                           | Cross-Cmnd calls go through `pyCmnd`, not a bare Python call, so argument validation/outcome plumbing still runs. See the `siteBase` → `siteBisosSelect` delegation in `bisos.sites.sites_csu` for a worked example. |
| Bash positional args (`$1`, `$2`)                  | `self.cmndArgsGet("0", cmndArgsSpecDict, argsList)`                            | Positions are declared via `cmndArgsSpecDict.argsDictAdd(argPosition=..., argName=..., ...)`.                                                                                                                        |

## Picking the target `_csu.py` module

Do **not** assume the first plausible-looking file (e.g. a stub module
that merely imports the right things) is the right target. Verify by
tracing which module is actually wired into the relevant `.cs` binary's
`csuList`:

```python
csuList = [ 'bisos.b.cs.ro', 'bisos.csPlayer.bleep', 'bisos.sites.sites_csu', ]
```

Only Cmnds in modules on this list are reachable via `binaryName.cs -i
<cmndName>`. A module that merely has the right imports staged but isn't
on any `.cs`'s csuList is a dead end for this purpose.

## Copy vs. move when another pip package has overlapping code

BISOS pip packages sometimes have pre-existing, overlapping site/platform/
etc. logic (e.g. `bisos.platform`'s `platformBases_csu.py` had a `siteBase`
Cmnd overlapping with `bisos.sites`'s territory). When asked to separate
concerns between packages:

- **Copy, don't move**, unless explicitly told to delete the original.
  Moving risks breaking the other package's own csuList/examples wiring,
  and the other repo is usually out of scope for the current task.
- If the original has a known incompleteness (e.g. a `TODO NOTYET`
  comment), the *copy* is the right place to actually complete it — leave
  the original as-is, and note in the copy's docstring why it now diverges.
- Cross-reference the divergence in a comment/docstring so a future reader
  (human or AI) understands the duplication is intentional, not drift.

## Don't-run-Cmnds discipline

When the task says "don't run any of the Cmnds" (common for symlink/base
management work that could damage a live `/bisos/site` or similar), that
applies to *executing* the new Cmnds via a `.cs` binary or `pyCmnd()` call
during the conversion session — not to static checks. Always still:

- `python3 -c "import ast; ast.parse(open('<file>').read())"` to confirm
  syntactic validity.
- Wire the new Cmnds into `examples_csu()` so they're discoverable once the
  user does choose to run them.

## Worked example

See `bisos.sites.sites_csu`'s `siteBisosBase`/`siteBase`/`siteBisosAdd`/
`siteBisosSelect`, converted from `/bisos/core/bsip/bin/site_lib.sh`'s
`vis_siteBisosBase`/`vis_siteBisosAdd`/`vis_siteBisosSelect`, with the
`siteBase` Cmnd copied (not moved) from `bisos.platform.platformBases_csu`
and its previously-incomplete `update` action resolved via delegation to
`siteBisosSelect`.
