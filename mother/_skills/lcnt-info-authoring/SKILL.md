---
name: lcnt-info-authoring
description: Use when creating or modifying an LCNT (Libre CoNtenT) document's `LCNT-INFO/` metadata — editing document file-variables (title, author, lcntNu, docSrcForms, docSrcLangs, articleForm), adding or changing a build spec under `LCNT-INFO/Builds/`, wiring `enabledList`, setting the `curBuild`/`curExport` symlinks, or adding an export destination under `LCNT-INFO/Exports/`. Pairs with lcnt-build-and-release (which consumes this metadata) and lcnt-new-document (which generates the initial LCNT-INFO).
---

# LCNT-INFO Authoring

`LCNT-INFO/` is the metadata control directory that drives all of `lcntProc.sh`. It uses the
**file-variable** convention: each setting is its own file whose *contents* are the value (one value
per file), not key=value lines. To change a setting, write the file.

## Layout

```
LCNT-INFO/
├── <document file-vars>        # type, lcntNu, mainTitle, docSrcForms, docSrcLangs, articleForm, ...
├── Builds/
│   ├── enabledList             # whitespace/line list of specs that target "all" expands to
│   └── <spec>/                 # one dir per build; file-vars: buildName, buildDocClass, docSrc, ...
├── Exports/
│   ├── enabledList
│   └── <spec>/                 # exportMethod, buildSpecs, gitRemoteUri, ...
├── Releases/<ver>/             # relTag, versionNu
└── templates/                  # starting-point copies of the source files
```

At the document root, two symlinks select the active specs:
`curBuild -> ./LCNT-INFO/Builds/<spec>` and `curExport -> ./LCNT-INFO/Exports/<spec>`.

## Document-level file-variables

Common ones (write the value as the file body):

| File | Meaning / values |
|------|------------------|
| `type` | e.g. `PLPC` |
| `lcntNu` | the LCNT number (permanent=assigned; record/draft/private=date-based) |
| `lcntName` | short machine name |
| `mainTitle` / `shortTitle` / `subTitle` / `subSubTitle` | titles |
| `author1`, `author2`, … | authors |
| `contentOrigin` | owner: `neda` / `fpf` / `mohsen` / … |
| `contentSrcFormat` | `ttytex` / `odp` |
| `docSrcForms` | `art` / `pres` / `pres+art` / … |
| `docSrcLangs` | `en` / `fa` / `en+fa` / `fa+en` |
| `articleForm` | `article` / `book` / `artBook` / `memo` / `mailing` |
| `docSrcList` | source basenames (e.g. `presentationEnFa`, `articleEnFa`) |
| `pubFormats` | e.g. `pdf+html` |
| `pubCategory` | `Permanent` / `Records` / `Draft` / `Private` |

## A build spec (`LCNT-INFO/Builds/<spec>/`)

Per-build file-vars:

| File | Meaning / values |
|------|------------------|
| `buildName` | used in result filenames (e.g. `art-8.5x11`, `presPdf`, `pres-reveal`) |
| `buildDocClass` | `memo` / `art` / `book` / `bookcover` / `presArt` / `pres` — how the shared source is built |
| `docSrc` | the `.ttytex` source (e.g. `articleEnFa.ttytex`) |
| `paperSize` | `8.5x11` / `a4` / `6x9` / `17.4x23.5` |
| `results` | formats to produce, e.g. `pdf` / `pdf+html` / `odt` / `markdown` |
| `sides` | `1` / `2` (one- or two-sided) |

Book builds add print-SKU vars: `isbn13Nu`, `medium`, `paperGsm`, `printColor`, `printAgent`
(`kdp`/`ing`/`loc`), `cover`, and generated `pdfNuOfPages`.

## Wiring it up

1. **Add a build**: create `LCNT-INFO/Builds/<spec>/` and write its file-vars. The cleanest way is
   to copy an existing sibling spec and edit it, so you don't miss a required var.
2. **Enable it**: add `<spec>` to `LCNT-INFO/Builds/enabledList` so `-i lcntBuild all` includes it.
3. **Make it active** (optional): repoint `curBuild` so `-i lcntBuild cur` uses it —
   `lcntProc.sh -i lcntBuildSetCur ./LCNT-INFO/Builds/<spec>`.
4. **Add an export**: create `LCNT-INFO/Exports/<spec>/` (`exportMethod` = `git`/`web`/`plone`,
   plus method-specific vars), add it to `Exports/enabledList`, repoint `curExport` if desired.

## Gotchas

- Values are **file contents**, not `name=value`. Beware trailing newlines where an exact match
  matters; mirror the style of existing file-vars in the same dir.
- `enabledList` is the single source of truth for what `all` builds — adding a `Builds/<spec>/`
  dir does nothing until it's listed there.
- `buildDocClass` is what lets one source be built as an article *and* a book (parts become
  chapters when `book`); don't fork the source to change class — add a build spec.
- Prefer letting `lcnLcntGens.sh` generate skeletons for a brand-new base (see
  `lcnt-new-document`); hand-author incremental changes to an existing `LCNT-INFO`.

## References

- File-variable definitions: `/bisos/panels/bisos-apps/lcnt/lcntModel/_nodeBase_/fullUsagePanel-en.org`.
- Generators: `/bisos/core/lcnt/bin/lcnLcntGens.sh`, `lcnLcntBuildLib.sh`, `lcnLcntExportLib.sh`.
- Consumers of this metadata: the `lcnt-build-and-release` skill.
