---
name: lcnt-build-and-release
description: Use when building, previewing, releasing, or exporting (publishing) an LCNT (Libre CoNtenT) document — any task that runs `lcntProc.sh` to turn `.ttytex`/`.tex` sources into PDF/HTML/Reveal/ODT/Markdown. Covers the verb/param/target grammar (`-i lcntBuild`, `-p extent=`, `cur`/`all`/`dev`), choosing the active build via `curBuild`, reading `LCNT-INFO/Builds/enabledList`, where outputs land (`Results/` → `Release/`), and exporting to configured destinations. Pairs with lcnt-info-authoring (to add/modify build specs) and lcnt-ttytex-authoring (to edit the sources).
---

# LCNT Build and Release

LCNT builds are driven by a per-directory `lcntProc.sh`, a thin stub that re-execs the shared seed
`/bisos/core/lcnt/bin/seedLcntProc.sh`. You invoke the stub; the seed and `lcnLcnt*Lib.sh`
libraries do the work. The low-level XeLaTeX/HeVeA engine is `lcnLcntInputProc.sh`.

## Before you build — read the state

```bash
cat _objectType_                       # e.g. bxt.lcnt.latex.pres+art.en+fa
ls LCNT-INFO/Builds                    # available build specs
cat LCNT-INFO/Builds/enabledList       # what "all" expands to
ls -l curBuild curExport               # the active build / export spec
```

`curBuild` is a symlink → `./LCNT-INFO/Builds/<spec>`; the target `cur` means "this spec".
`curExport` is a symlink → `./LCNT-INFO/Exports/<spec>`.

## Invocation grammar

```
lcntProc.sh [-h -v -n showRun] -p <par>=<val> ... -i <verb> <target>
```

- `-h -v -n showRun` — verbose + echo each sub-command (recommended while iterating).
- `-i <verb>` — the action (see below).
- `-p extent=<...>` — composable with `+`: `build`, `view`, `release`
  (e.g. `build`, `build+view`, `build+view+release`).
- `-p pre="clean"` — full clean before building.
- `<target>` — `cur` | `all` | `dev` | an explicit `./LCNT-INFO/Builds/<spec>`.
  - `cur` follows the `curBuild` symlink.
  - `all` iterates `LCNT-INFO/Builds/enabledList`.
  - `dev` builds **without** the dblock metadata pass (fast inner loop; metadata may be stale).

## The verbs you will use

| Verb | What it does |
|------|--------------|
| `lcntBuild` | Build the given target (the main verb). |
| `lcntExport` | Publish built results to the enabled `Exports/` destinations. |
| `dblockUpdateFile <file>` | Re-run only the dblock metadata injection into one source. |
| `fullBuild` / `fullClean` / `fullRefresh` | Build-all / clean-all / refresh generated files. |
| `resultsRelease` / `buildResultsRelease` | Copy/version outputs into `Release/`. |
| `dirsRecurse <verb>` | Run `<verb>` across a tree of LCNT dirs. |
| `mmUniteStart` | Enter the multimedia (audio/video) flow — see `lcnt-multimedia`. |

## Canonical commands

```bash
# Build the active spec, run the dblock pass, and open the viewer:
lcntProc.sh -h -v -n showRun -p pre="clean" -p extent="build+view" -i lcntBuild cur

# Build everything in enabledList:
lcntProc.sh -h -v -n showRun -p extent="build+view" -i lcntBuild all

# Build one explicit spec by name:
lcntProc.sh -p extent="build" -i lcntBuild ./LCNT-INFO/Builds/presPdf

# Fast inner loop, skip dblock injection:
lcntProc.sh -p extent="build+view" -i lcntBuild dev

# Metadata changed but source text didn't — re-inject only:
lcntProc.sh -i dblockUpdateFile presentationEnFa.ttytex

# Build + stage into a versioned release:
lcntProc.sh -p extent="build+release" -i lcntBuild cur

# Publish to the configured Exports (git/web/plone):
lcntProc.sh -i lcntExport all
```

## Where outputs go

- `Results/` — intermediate build outputs (`c-<lcntNu>-<buildName>.{pdf,html,...}`).
- `Release/<ver>/` — versioned, publishable artifacts
  (`c-<lcntNu>-<ver>-<name>-<buildName>.pdf`, access pages, `.bib`). `Release/cur` symlinks the
  active version.
- HeVeA HTML builds produce a `heveaHtml-*` directory; Reveal builds a reveal HTML tree.

## Switching the active build

Point `curBuild` at a different spec, then `lcntBuild cur`:

```bash
lcntProc.sh -v -n showRun -i lcntBuildSetCur ./LCNT-INFO/Builds/pres-reveal
```

## Gotchas

- A build with `extent` including `build` (and target not `dev`) runs the **dblock pass** first,
  which rewrites generated regions of the `.ttytex` from `LCNT-INFO`. Don't be surprised by source
  churn — it's expected. Use `dev` to skip it.
- If `figures` is missing, the stub's `buildPre`/`vis_lcnLcntInputPre` hook symlinks a shared
  `.../common/figures`. A broken figures symlink is a common first-build failure.
- `enabledList` — if `all` builds too much/too little, edit `LCNT-INFO/Builds/enabledList`
  (see `lcnt-info-authoring`).
- Do **not** hand-edit the seeded dblock regions of `lcntProc.sh`; only its per-project hook
  functions (`buildPre`, `buildPost`, `cleanPost`, `vis_lcnLcntInputPre`) are editable.

## References

- Seed + libraries: `/bisos/core/lcnt/bin/` (`seedLcntProc.sh`, `lcnLcntBuildLib.sh`,
  `lcnLcntInputProc.sh`).
- Documentation of record: `/bisos/panels/bisos-apps/lcnt/lcntProc/_nodeBase_/fullUsagePanel-en.org`.
- The per-directory `Panel.org` has clickable Blee equivalents of every command above.
