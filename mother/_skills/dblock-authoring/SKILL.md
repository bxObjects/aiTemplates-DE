---
name: dblock-authoring
description: Use when working with org-mode dynamic blocks in Python/`.cs`/`.pcs` source — writing or updating any `####+BEGIN: b:...` block (particulars, classHead, csuListProc, method/args, framework/imports, framework/main), authoring an inline dblock-based unit test that captures a command's expected output, or troubleshooting why a dblock expansion looks wrong. Also covers the `csuListProc` elisp-block pattern in csxu files.
---

# Poly-Dblock Authoring for bisos-pip Source

Org-mode dynamic blocks (dblocks) are used heavily throughout BISOS Python
source. They insert language-specific and org-mode content into source files
via a shared `####+BEGIN: <signature> [:key value ...]` / `####+END:` marker
convention. The `blee/poly-dblock` package extends org-mode's native dblock
machinery to Python, Bash, LaTeX, and HTML.

## The one rule

**Never hand-edit content between `####+BEGIN:` and `####+END:`.** That content
is regenerated. Author only:

1. The `####+BEGIN:` header line (signature + `:key value` pairs)
2. The body *after* `####+END:`

If a dblock body looks wrong, update the header or regenerate — don't patch
the generated content.

## Regenerating dblocks

- **Inside Blee/Emacs**: `M-x org-dblock-update` (or the panel's "Update Buf
  Dblocks" link).
- **Outside Blee**: use `py-dblock.cs updateDblocks <file>` from the
  `bisos.pyDblock` package. This is the pure-Python fallback used by
  `aiActivity.cs initiate` for the `b:ai:file/particulars` dblock in
  copied AI files.

**`py-dblock.cs` expands only the signatures registered with it** (today
`b:ai:file/particulars`). For any other dblock it still prints
"DBLOCK-UPDATED: <file>" and leaves the block exactly as it was --- check with
`git diff`, do not trust the message. *Blee-only* in practice (verified
2026-10-26): `b:py3:cs:cmnd/classHead`, `b:py3:cs:framework/csuListProc` /
`csuListImportPlus`, and `setup.py`'s `b:py3:pypi:setup/*`. `bx-dblock -i
dblockUpdateFiles <file>` (what `pypiProc.sh` calls for `setup.py`) needs a
running Emacs server and fails without one. Loading
`/bisos/git/bxRepos/blee/env3/dblocks/dblock-comeega-python.el` in `emacs --batch -Q`
does not work either (it needs much more of Blee). So without Blee: author the
dblock *header* or the spec it reads (e.g. the elisp `csuList`), leave the body,
and ask the developer to regenerate. *With* the user's running Blee, Claude can
regenerate them itself, with the user's agreement, through `bx-dblock` and the
Emacs server: see the `bs-blee-emacs-server` skill (socket, `G_emacsServerPid`,
the global dblock regexp, side effects).

## Dblock definitions and where they live

All dblock definitions are elisp under `/bisos/blee/env3/dblocks/`. Read
them when you need to know what parameters a specific dblock accepts.

Common signatures encountered in bisos-pip code:

| Signature                                     | Purpose                                              |
|-----------------------------------------------|------------------------------------------------------|
| `b:prog:file/proclamations`                   | AGPL / BISOS proclamation block                      |
| `b:prog:file/particulars`                     | File-level authors, version                          |
| `b:py3:file/particulars-csInfo`               | Python `csInfo` dict for a CS unit                   |
| `b:py3:cs:file/dblockControls`                | File-level dblock classification (cs-mu, cs-u, etc.) |
| `b:py3:cs:framework/imports`                  | Standard imports for a CS file                       |
| `b:py3:cs:framework/csuListProc`              | csxu-only: parse elisp `b:py:cs:csuList` (see below) |
| `b:py3:cs:framework/main`                     | The `if __name__ '__main__':` block               |
| `b:py3:cs:framework/endOfFile`                | End-of-editable-text marker + emacs locals           |
| `b:py3:cs:cmnd/classHead`                     | Generate a `cs.Cmnd` subclass header                 |
| `b:py3:cs:method/args`                        | Generate a `cmndArgsSpec()` method body              |
| `b:py3:cs:orgItem/section`                    | Formatted section header                             |
| `blee:bxPanel:foldingSection`                 | Panel folding section header                         |
| `blee:panel:icm:py:cmnd`                      | Panel-invocable CS command button                    |
| `blee:bxPanel:runResult`                      | Panel-embedded command with captured output          |
| `b:ai:file/particulars`                       | AI-collaboration working-context block               |

To learn what a specific dblock does, `grep` for its signature in
`/bisos/blee/env3/dblocks/`.

## The `csuListProc` dblock — csxu-only, and NOT self-contained

In a *csxu* (a top-level `.cs` script — the executable, not a `_csu.py`
module), the `####+BEGIN: b:py3:cs:framework/csuListProc` dblock is
**not self-contained**. It reads the elisp variable `b:py:cs:csuList` set
by a `#+BEGIN_SRC emacs-lisp` block that must appear **immediately above** it:

```python
""" #+begin_org
*  ...  ~csuList emacs-list Specifications~  ...  [[elisp:(blee:org:code-block/above-run)][ /Eval Below/ ]]
#+BEGIN_SRC emacs-lisp
(setq  b:py:cs:csuList
  (list
   "bisos.b.userConfig_csu"
   "bisos.aiActivity.someOther_csu"
 ))
#+END_SRC
#+RESULTS:
| bisos.b.userConfig_csu | bisos.aiActivity.someOther_csu |
#+end_org """

####+BEGIN: b:py3:cs:framework/csuListProc :pyImports t :csuImports t :csuParams t :csxuParams nil
""" #+begin_org
*  ...  ~Process CSU List~  with /2/ in csuList ...
#+end_org """

from bisos.b import userConfig_csu
from bisos.aiActivity import someOther_csu

csuList = [ 'bisos.b.userConfig_csu', 'bisos.aiActivity.someOther_csu', ]

g_importedCmndsModules = cs.csuList_importedModules(csuList)

def g_extraParams():
    csParams = cs.param.CmndParamDict()
    cs.csuList_commonParamsSpecify(csuList, csParams)
    cs.argsparseBasedOnCsParams(csParams)

####+END:
```

**Author only the elisp list.** When the dblock is updated in Blee, it evaluates
the elisp, reads `b:py:cs:csuList`, and regenerates all the Python wiring —
the `from ... import ...` statements, `csuList = [...]`, and the
`g_extraParams()` body.

**Do NOT hand-edit the generated Python inside the dblock.** To add a new CSU,
add it to the elisp list and regenerate.

Also note: the generated `g_extraParams` calls only
`cs.csuList_commonParamsSpecify(csuList, csParams)` — it does *NOT* call the
csxu's own `commonParamsSpecify()`. The csxu's own params are wired
separately by the framework via the file-level `commonParamsSpecify()`
function.

This pattern applies to **csxu files only**. CSU files (`_csu.py`) do not
have a `csuListProc` dblock.

Seed csxus (e.g. `containerProc-seed.cs`, `ftoBranch-seed.cs`) use the same
mechanism under the name `b:py3:cs:framework/csuListImportPlus`. Two things to
know:
- **The generated imports matter, not just the list.** PyCS looks for commands
  only in `csuList` modules the program has imported; the regenerated block
  writes `from <pkg> import <module>` for each entry. A module added to the list
  by hand, without its import, contributes no commands.
- **Pick the right seed.** A leaf-side module (e.g. `bisos.fileObj.ftoLeaf_csu`)
  belongs in the *leaf* seed's list, never the branch seed's
  (`ftoBranch-seed.cs`): two `csuList` modules defining the same command names ---
  the later one wins.

## The `classHead` dblock — see `writing-cs-commands`

The `b:py3:cs:cmnd/classHead` dblock generates the `cs.Cmnd` subclass header
and the `cmnd()` method signature. Its parameters (`:cmndName`, `:parsMand`,
`:parsOpt`, `:argsMin`, `:argsMax`, `:ro`, etc.) are covered in detail in
the `writing-cs-commands` skill. Read that when authoring or modifying a CS
command.

## Dblock-based inline unit tests

BISOS has no separate unit-test framework. For some PyCS commands,
verification is done via a dblock that runs the command as a bash
sub-process and captures its output *inline in the source file*. That
captured output is the test — if regenerating the dblock produces
different output, the command's behavior changed.

Two mechanisms:

1. **`self.captureRunStr(...)`** inside a command's `cmnd()` body — captures
   an example invocation's expected output. The result gets pasted into the
   file when the surrounding dblock is regenerated.

2. **Panel-embedded `runResult` dblocks** — inside a Blee panel (`*.org`),
   `####+BEGIN: blee:bxPanel:runResult :command "..." :results "stdout"` runs
   the command and captures stdout into the block body. Great for
   documenting "here is what this command produces" as living documentation.

## The `b:ai:file/particulars` dblock

Special case — this is the AI-collaboration working-context block at the
top of `AI-DevStatus.org` and `AI-WorkPlan.org`. Its handler is registered
by `bisos.pyDblock.dblock_particulars` and is invoked by
`aiActivity.cs initiate` at install time (pure Python — no Emacs
required). Its body records `Working Directory`, `File`, `Activity`, and
`Companion Docs`.

## Common pitfalls

- **`####+END:` vs `###+END:`** — bisos uses 4 `#` marks in both `BEGIN` and
  `END` (`####+BEGIN:` / `####+END:`). Some upstream elisp uses 3. The
  `bisos.pyDblock` engine accepts either.
- **Trailing whitespace on the `BEGIN:` line** — some editors trim it and
  break signature parsing. Keep the header line exactly as generated.
- **`.cs` file needs `chmod +x`** after creation — the csxu is executed
  directly. If a fresh `.cs` file gives "permission denied", `chmod +x` it.
- **Hand-written lines inside a block are lost on regeneration.** E.g. an extra
  `from bisos.fileObj import ftoBranch_seedInfo` once added inside
  `ftoBranch-seed.cs`'s `csuListImportPlus` body vanished at the next
  regeneration, and the seed's examples then raised `NameError`. Put such lines
  *after* `####+END:`.
- **Formatting tools that rewrite tables touch dblock bodies too.** Running
  `org-table-align` over a whole `README.org` also realigns the generated
  `topControls` table. Skip tables inside `#+BEGIN:` / `#+END:` (or restore them
  from git and check with `git diff`).
- **Adding a new dblock signature** — write the handler as a Python function
  and register it via
  `bisos.pyDblock.updateDblock.registerHandler(sig, fn)`. See
  `bisos.pyDblock.dblock_particulars` for a working example.

## What NOT to do

- Do NOT hand-edit content between `####+BEGIN:` and `####+END:` — regenerate.
- Do NOT add a new CSU to a csxu's Python `csuList` directly — add it to the
  elisp `b:py:cs:csuList` above the `csuListProc` dblock and regenerate.
- Do NOT copy a dblock header from one file to another without checking that
  the target file's dblock classification (`b:py3:cs:file/dblockControls`)
  matches (`cs-mu`, `cs-u`, `cs-lib`, `bpf-lib`, `pyLibPure` — different
  files get different dblock sets).

## References

- Poly-dblock overview: `/bisos/git/bxRepos/blee/poly-dblock/README.org`
- Dblock elisp source: `/bisos/blee/env3/dblocks/`
- Pure-Python dblock engine: `bisos.pyDblock` (source under
  `/bisos/git/bxRepos/bisos-pip/pyDblock/`)
- Example handler: `bisos.pyDblock.dblock_particulars`
- COMEEGA (the surrounding authorship model): `/bisos/git/bxRepos/blee/comeega/README.org`
