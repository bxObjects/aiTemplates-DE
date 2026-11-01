---
name: lcnt-new-document
description: Use when bootstrapping a brand-new LCNT (Libre CoNtenT) document base from scratch — generating the initial `LCNT-INFO/` metadata, source skeletons, build and export specs via `lcnLcntGens.sh ... -i baseFullStart`, setting the first `curBuild`, and running the first build. Also covers the one-time host/BPO foundation setup. For incremental edits to an existing base use lcnt-info-authoring; for building use lcnt-build-and-release.
---

# Starting a New LCNT Document

A new LCNT base is *generated*, not hand-assembled. The generator is
`/bisos/core/lcnt/bin/lcnLcntGens.sh`; it lays down `LCNT-INFO/`, the source skeletons (from
`LCNT-INFO/templates/`), the `lcntProc.sh` stub, and the build/export scaffolding.

## Prerequisite — foundation is set up

Creating content assumes the host already has the LCNT bases wired (one-time, usually already done
by sysProvision). If `lcnt` paths are missing, the setup sequence is documented in
`/bisos/panels/bisos-apps/lcnt/lcntFoundations/_nodeBase_/fullUsagePanel-en.org`:

```bash
bisosLcntSetup.sh -i bisosLcntBinsPrep          # (not needed on recent provisioning)
bisosLcntSetup.sh -i lcntBasesBpoActivate
bpoLcntManage.sh  -i lcntBposAvailable | bpoActivate.sh -i bpoActivate
bisosLcntSetup.sh -p uid=root -h -v -n showRun -i lcntBasesSetup
usgBpos.sh        -i usgBpos_lcntBases_bpoId
bisosLcntSetup.sh -i usgBposLcntBasesSetup
```

Creating a new *published* BPO/repo for the content is a separate workflow (`bxieProvision.sh`,
`bpoLcntManage.sh ... -i repoBaseCreate_lcnt`) — see the `lcntBPOs` panel. **Gotcha documented
there:** run BPO creation from `/de/sys/lcnt/lgpc/`, *not* from `/bxo/.../pip_lcnt_*`, or it fails.

## Generate the base

From the target (empty) content directory:

```bash
cd <target-dir>

# Generate base + both forms, bilingual. Omit lcntNu to auto-assign; pass it for a permanent number.
lcnLcntGens.sh -n showRun -p cntntRawHome=. -p srcForms="pres+art" -p srcLangs="en+fa" \
  -i baseFullStart
# (permanent-numbered variant)
lcnLcntGens.sh -n showRun -p cntntRawHome=. -p srcForms="pres+art" -p lcntNu=00000 \
  -p srcLangs="en+fa" -i baseFullStart

# Generate build + export scaffolding:
lcnLcntGens.sh -n showRun -p cntntRawHome=. -i lcntBuildInfoGens
lcnLcntGens.sh -n showRun -p cntntRawHome=. -i lcntExportInfoGens
```

`srcForms` ∈ {`art`, `pres`, `pres+art`, `memo`, …}; `srcLangs` ∈ {`en`, `fa`, `en+fa`, …}.

## Set the active build and do the first build

```bash
lcntProc.sh -v -n showRun -i lcntBuildSetCur ./LCNT-INFO/Builds/presPdf
# Define what "all" means:
#   edit LCNT-INFO/Builds/enabledList, e.g.:  presPdf pres-reveal presArt-8.5x11 presArt-html
lcntProc.sh -h -v -n showRun -i fullClean
lcntProc.sh -h -v -n showRun -p extent="build+view" -i lcntBuild cur
```

## After generation

- Fill in document file-vars (titles, author, etc.) — see `lcnt-info-authoring`.
- Write content in the generated `body*.tex` — see `lcnt-ttytex-authoring`.
- Confirm markers exist: `_objectType_`, `_tree_` (`leaf`), `_treeProc_` (`lcntProc.sh`).

## Gotchas

- Always pass `-p cntntRawHome=.` and run from inside the target dir.
- Use `-n showRun` first to preview what the generator will do.
- If a number assignment half-fails, the registries to reconcile are
  `/de/sys/lcnt/lgpc/bystar/SOURCE-INFO/permanent.reg` and `/lcnt/outputs/all/lists/nuBaseDir`
  (per the `lcntBPOs` panel).

## References

- Generator: `/bisos/core/lcnt/bin/lcnLcntGens.sh`.
- Panels: `.../lcnt/lcntFoundations/`, `.../lcnt/lcntBPOs/`, `.../lcnt/lcntArtTypes/` under
  `/bisos/panels/bisos-apps/`.
- Follow-ups: `lcnt-info-authoring`, `lcnt-ttytex-authoring`, `lcnt-build-and-release`.
