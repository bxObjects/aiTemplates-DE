---
name: libreoffice-draw-authoring
description: Use when reading, reviewing, editing or creating a LibreOffice Draw figure — an `.odg` file (or a kept starting point `.orig_odg`) in an lcnt-libreoffice figures directory such as `images/LibreOffice/` or an LCNT document's `figures/`, with its `figProc.sh`, `.title`, `.caption`, `.style`, `.tex` and `_pres.tex` files — or when asked "can you view / edit this .odg", to redraw or extend a hand-made figure (boxes, bands, columns, arrows, a red 16x9 presentation frame), to regenerate its `.png`/`.pdf`/`.ps` with `figProc.sh -i odgConvert`, or when a headless LibreOffice conversion produces nothing. Covers the `.odg` zip and its content.xml, looking at the figure before and after every change, editing in place versus generating from a base with tools/odgKit.py, styles, fonts and arrow markers, rendering, and the rule never to overwrite the user's own Draw edits.
---

# Authoring LibreOffice Draw (.odg) Figures

Load the lcnt-libreoffice `AI-Activity.org` first if you are not in such a directory already: it
gives the files of a figure, `figProc.sh`, and the conventions (16x9 page, red frame). This skill is
how to do the work.

```
look (render, read the PNG) ─► say what the figure communicates ─► agree the change
      ▲                                                                   │
      └──── read the PNG ◄── figProc.sh -i odgToPng ◄── edit or generate ◄┘
                                                        (then -i odgConvert: png, pdf, ps)
```

## 1. Look before you touch

- Render and read the image: Claude reads PNGs directly (the Read tool on `X.png`).
  ```bash
  ./figProc.sh -i odgToPng X.odg        # or: libreoffice --headless --convert-to png X.odg
  ```
- List what is in it, with positions, to talk about it precisely:
  ```bash
  python3 -I <skill>/tools/odgKit.py page X.odg     # page size, fonts declared, arrow markers
  python3 -I <skill>/tools/odgKit.py list X.odg     # kind, x,y w x h (cm), style, text
  ```
- Before proposing anything, say in a few sentences what the figure is meant to communicate:
  its rows and columns, what the colours group, what each arrow means. A user's hand-made figure
  usually encodes decisions (which layer pairs with which, what is repeated and why); the change
  has to keep them.

## 2. What an .odg is

A zip (ODF):

| Member                 | Holds                                                                      |
|------------------------+----------------------------------------------------------------------------|
| `mimetype`             | first, *stored* (not compressed), else LibreOffice rejects the file        |
| `content.xml`          | the font declarations, the automatic styles, and the page with its shapes |
| `styles.xml`           | named styles, the page layout (size), markers (`Arrow`), dash styles       |
| `settings.xml`, `meta.xml` | view settings, metadata: copy unchanged                                |
| `Thumbnails/thumbnail.png` | a preview: drop it when rewriting (it would be stale), and its manifest entry |
| `META-INF/manifest.xml`| the list of members                                                        |

Shapes in `content.xml`, inside `<draw:page>`, in z-order (later on top):

- `draw:custom-shape` with `draw:enhanced-geometry draw:type="rectangle"`: a box with its own text.
- `draw:frame` with `draw:text-box`: free text.
- `draw:line` (`svg:x1 y1 x2 y2`): a line; arrowheads by `draw:marker-start` / `draw:marker-end`
  in its graphic style, naming a marker defined in `styles.xml` (usually `Arrow`).
- `draw:connector`: a line glued to shapes (moves with them in Draw); `draw:g`: a group.
- Geometry is in `cm` (`svg:x`, `svg:y`, `svg:width`, `svg:height`), from the page's top left.

Text is `<text:p>` paragraphs with `<text:span>`, styled by automatic styles: `gr*` (graphic: fill,
stroke, text area), `P*` (paragraph: alignment), `T*` (text: font, size, colour, weight). A font must
be declared in `office:font-face-decls`, or LibreOffice substitutes another.

## 3. Two ways to change a figure

| Way                 | When                                                                 |
|---------------------+----------------------------------------------------------------------|
| Edit in place       | a few changes: a label, a colour, a moved or added shape            |
| Generate from base  | a redraw: new layout, many shapes, a figure rebuilt from an original |

**Edit in place**: read `content.xml`, change the elements (Python `zipfile` + string or
`xml.etree` edits), and repack with `odgKit.repack(zin, out, {'content.xml': data})`, which keeps
`mimetype` first and stored and drops the stale thumbnail. Reuse existing styles where a shape should
look like its neighbours; add a new automatic style only for a new look.

**Generate from a base** with `tools/odgKit.py`'s `Figure`: it keeps the base's page size, styles,
fonts, settings and metadata, and writes a new page from your shapes.

```python
import sys; sys.path.insert(0, '<skill>/tools')
from odgKit import Figure, L
f = Figure('X.orig_odg')                      # the base: page, styles, fonts, settings
f.frame()                                     # red 16x9 frame, 1 cm inset
f.box(7.4, 14.6, 31.5, 2.8, '#9fc5f8', '#3d85c6',
      [L('bisos.aiActivity', 16, bold=True), L('aiActivity.cs — initiate, refresh', 11)])
f.text(23.4, 17.45, 11, 0.6, [L('built from', 10, italic=True, color='#444444')], align='left')
f.line(23.15, 18.1, 23.15, 17.4, start=False)  # one-headed: from 18.1 up to 17.4
f.write('X.odg')
```

Keep the generating script in your scratchpad while iterating. Once the user has the figure, the
`.odg` is the source: the user may open it in Draw and change it, and a script run again would
throw those changes away. Do not commit a generator next to the figure unless the user asks for one.

## 4. Layout that works

- Work on a grid: decide the rows (y, height) and columns (x, width) first, as a small table in the
  script, then place shapes by them. Leave 0.3–0.6 cm between bands; arrows need that gap.
- Boxes do not grow (`auto-grow-height="false"`): text that does not fit is clipped or overflows
  invisibly. Size the box for its text (about 0.5 cm of height per line at 11–14 pt, plus padding),
  then check in the PNG.
- Row labels in a left column, column headings at the top of tall dashed bands: a figure with uses
  across and layers up reads as a matrix.
- Colour by family, one hue per family with a darker stroke; a lighter fill for things inside a box.
- Arrows end on box edges: compute endpoints from the boxes' y and height, not by eye. A label sits
  beside the arrow, italic, about 10 pt.
- A narrow box on top of another (0.6 cm) reads as "the interface to it".

## 5. Render, check, hand over

```bash
./figProc.sh -i odgToPng X.odg            # iterate: PNG only, then read it
./figProc.sh -i odgConvert X.odg          # hand over: png, pdf, ps
```

- Read the PNG after every change. Check: text fits its boxes, nothing crosses the red frame,
  arrows touch the boxes they connect, labels do not sit on lines.
- `figProc.sh -i build` runs the full LCNT build and needs that environment (`frameMakerHost`);
  outside it, `-i odgConvert` is the path.
- If `libreoffice --headless --convert-to` writes nothing, a running LibreOffice of the same user may
  have taken the request: close it, or convert with a separate profile,
  `libreoffice -env:UserInstallation=file:///tmp/lo-convert --headless --convert-to png X.odg`.
- Then the prose: the README paragraph that describes the figure is part of the change.

## 6. Do not overwrite the user's edits

- Before writing `X.odg`, compare it with the last file you produced (`cmp X.odg <your copy>`). If
  they differ, the user edited it in Draw: start from their file (edit in place), not from your script.
- Keep a starting point the user gave you (`X.orig_odg`); never delete it unasked.
- The user may move or rename the figure directory: find the figure again before writing.

## References

- Orientation: the lcnt-libreoffice `AI-Activity.org` (installed in the activity's directory).
- `figProc.sh` verbs: `/bisos/core/lcnt/bin/seedFigProc.sh` (`odgConvert`, `odgToPng`, `odgToPdf`,
  `genStartFigInfoFiles`, `genFigTex`).
- A worked example: `blee/vscode-claude/images/LibreOffice/` — `blee-aiActivity-layers.orig_odg` (the
  user's starting point) and `blee-aiActivity-layers.odg` (generated from it with the method of
  section 3, then extended).
- Generated figures instead of hand-composed ones: the `graphviz-authoring` skill.
