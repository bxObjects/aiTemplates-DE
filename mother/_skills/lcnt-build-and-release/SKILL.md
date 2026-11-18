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

# Land a released document on the astro sites of this system (the localWeb export):
lcntProc.sh -p extent="build+release" -i lcntBuild all
lcntProc.sh -i lcntExport ./LCNT-INFO/Exports/localWeb
```

The `localWeb` export lands only what `build+release` staged (it prints "not released" otherwise),
into `<siteBase>/var/lcnt/<class>/<nu>/<rel>/` with a `meta.pyl`; a presentation exports its pdf
only, for now. Run it by name: it is not in `Exports/enabledList`. The site then regenerates its
Library pages (`astroSite.cs -i libraryGenerate`; see `astro-site-authorship`).

## Where outputs go

- `Results/` — intermediate build outputs (`c-<lcntNu>-<buildName>.{pdf,html,...}`).
- `Release/<ver>/` — versioned, publishable artifacts
  (`c-<lcntNu>-<ver>-<name>-<buildName>.pdf`, access pages, `.bib`). `Release/cur` symlinks the
  active version.
- HeVeA HTML builds produce a `heveaHtml-*` directory; Reveal builds a reveal HTML tree.

## The Reveal build (`pres-reveal`, results `html`, or `disposition+html`)

`lcnLcntBuildLib.sh` generates `pres-reveal` with `results` = `html`: it does not make the frame
images. Then run `lcntProc.sh -i beamerDerivedFullBuild` first (after `fullClean ForGit`, a fresh
clone, or edited frames), or set `results` to `disposition+html` (EmacsConf25 does); else the deck
shows broken images. A build type that does both is proposed in AI-Outputs.org (2026-11-18).

1. `disposition`: the Beamer PDF, then the per-frame images in `disposition.gened/` (see
   `lcnt-multimedia`; a few minutes).
2. `html`: HeVeA HTML, then `elispFilterHtml.sh` (from PATH, `/bisos/blee/bin`, with
   `exec=mainRevealHevea`) makes `heveaHtml-<doc>/revealSlides.html`, copied to `revealJsBase/`.
3. `revealJsBase/<doc>.html` is copied from the start file and filled by `bx-dblock`
   (`org-dblock-update-file-bx` in the user's Emacs) with `revealJsHead.html`,
   `./revealSlides.html` and `revealJsTail.html` (`/bisos/apps/defaults/web/revealJs/bxDblock/`).
   reveal.js and its plugins are loaded from `revealJsBase/node_modules` ->
   `/usr/local/lib/node_modules` (installed by `revealJs-sbom.pcs`, bisos.lcnt).

Check after a build: `revealJsBase/<doc>.html` is tens of KB, not the ~480-byte start file, and
`ls disposition.gened/*/slide-1.png | wc -l` matches the frames.

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
- Reveal: the fill (step 3 above) needs the user's Emacs, so build from Blee. It is **refused** when
  an Emacs buffer of `revealJsBase/<doc>.html` is open and out of date with the file, and the build
  carries on silently with the unfilled start file. Close or revert that buffer before rebuilding;
  never leave one open after filling by hand (`emacsclient --eval (org-dblock-update-file-bx ...)`
  kills only buffers it opened itself).
- Do **not** hand-edit the seeded dblock regions of `lcntProc.sh`; only its per-project hook
  functions (`buildPre`, `buildPost`, `cleanPost`, `vis_lcnLcntInputPre`) are editable.

## References

- Seed + libraries: `/bisos/core/lcnt/bin/` (`seedLcntProc.sh`, `lcnLcntBuildLib.sh`,
  `lcnLcntInputProc.sh`).
- Documentation of record: `/bisos/panels/bisos-apps/lcnt/lcntProc/_nodeBase_/fullUsagePanel-en.org`.
- The per-directory `Panel.org` has clickable Blee equivalents of every command above.
