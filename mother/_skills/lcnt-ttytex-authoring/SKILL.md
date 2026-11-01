---
name: lcnt-ttytex-authoring
description: Use when editing LCNT (Libre CoNtenT) source — `.ttytex` wrapper files or the shared `body*.tex` bodies. Covers the ttytex format (LaTeX with embedded org-mode + dblock regions), the bilingual/edition comment-conditionals (`\includecomment{whenDocDirectionLtr}`, `whenIsBook`, `whenUsEdition`, `whenHeveaIgnore`), the shared-body convention across presentation/article/book forms, and what is safe to hand-edit versus dblock-generated. Builds on dblock-authoring and comeega-authorship; for building the result see lcnt-build-and-release.
---

# LCNT ttytex Authoring

LCNT sources are LaTeX processed through XeLaTeX (PDF) and HeVeA (HTML). A `.ttytex` is a
LaTeX file that also carries **embedded org-mode** (the COMEEGA model) and **dblock** regions
that inject metadata from `LCNT-INFO`. The bulk prose lives in shared `body*.tex` files that
several `.ttytex` wrappers include.

## Read these first

This skill assumes two general skills:
- `comeega-authorship` — the cross-language "org-mode surrounded program" model and the universal
  *never hand-edit inside dblock bodies* rule, which applies to `.ttytex`/`.tex` too.
- `dblock-authoring` — `####+BEGIN:` / `####+END:` mechanics and regeneration.

## File roles

- `presentationEnFa.ttytex` — presentation wrapper (beamer; also → Reveal.js).
- `articleEnFa.ttytex` — article/book wrapper (`\documentclass{article}` or `[twoside]{book}`).
- `presArtEnFa.ttytex` — combined presentation+article wrapper.
- `body*EnFa.tex` (e.g. `bodyPresArtEnFa.tex`, `bodyArticleEnFa.tex`) — the **shared content**
  the wrappers `\input`. Edit prose here so every form stays in sync.
- `bookCover.ttytex` / `frontCover.ttytex` / `backCover.ttytex` — book front/back matter.
- `common/chap_*.tex`, `common/app_*.tex` — book chapters/appendices under a shared `common/` tree.

## What is safe to edit

- **Author freely**: body prose in `body*.tex` / `common/*.tex`, and content *after* a `####+END:`.
- **Do NOT touch**: anything between `####+BEGIN:` and `####+END:` — document-class, packages,
  commands, i18n preambles are dblock-generated. To change them, edit the `####+BEGIN:` header or
  the governing `LCNT-INFO` var and regenerate (`lcntProc.sh -i dblockUpdateFile <file>`), per
  `dblock-authoring`.

## Conditionals — bilingual, edition, and output-target switching

LCNT uses the LaTeX `comment` package. Each toggle is an `\includecomment{...}` /
`\excludecomment{...}` pair; content inside a `\begin{<name>}...\end{<name>}` is kept or dropped:

| Toggle | Keeps content for… |
|--------|--------------------|
| `whenDocDirectionLtr` / `whenDocDirectionRtl` | left-to-right (English) / right-to-left (Farsi) |
| `whenIsBook` / `whenIsArticle` | book (with chapters) / article (no chapters) |
| `whenUsEdition` / `whenIntEdition` | US / International edition |
| `whenHeveaIgnore` | content excluded from the HeVeA/HTML build |
| `whenOrg` (`\begin{whenOrg}...`) | org-mode-only control regions |

Rules:
- Keep one shared body; **switch per variant with these comments**, don't fork files.
- The actual `\include/\excludecomment` decisions are usually set by the dblock preamble from
  `LCNT-INFO` (`docSrcLangs`, `articleForm`, build `buildDocClass`) — so prefer changing the
  *metadata* over hardcoding a toggle. Hardcode only genuinely content-specific splits.

## Typical loop

```bash
# edit body*.tex / common/*.tex
lcntProc.sh -p extent="build+view" -i lcntBuild dev    # fast: skip dblock injection
# when metadata (titles, class, langs) changed:
lcntProc.sh -i dblockUpdateFile articleEnFa.ttytex
lcntProc.sh -p extent="build+view" -i lcntBuild cur
```

## Gotchas

- XeLaTeX (not pdflatex) — Unicode/Farsi fonts rely on it; don't introduce pdflatex-only idioms.
- HeVeA is stricter/narrower than XeLaTeX — wrap PDF-only constructs in `whenHeveaIgnore` so the
  HTML build still succeeds.
- A missing `figures` symlink breaks `\includegraphics`; the stub's build hook normally recreates
  it (see `lcnt-build-and-release`).
- Editing generated preamble by hand is the most common mistake — it silently reverts on the next
  dblock pass. Change the header or the `LCNT-INFO` var instead.

## References

- `comeega-authorship` and `dblock-authoring` skills (prerequisites).
- Build/preview: `lcnt-build-and-release`. Metadata that drives the preamble: `lcnt-info-authoring`.
- Real examples: an EmacsConf presentation and the `polyexistentials/usEditionEnFa` book under
  `/lcnt/lgpc/`.
