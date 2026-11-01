---
name: graphviz-authoring
description: Use when authoring or modifying a `*-graphviz.pcs` (or `*-graphviz.cs`) figure — writing a new named graph, adding a graph to an existing module, choosing colours/shapes from the BISOS semantic palette, iterating on layout, or embedding a rendered figure in a README or Blee panel. Covers the render-preview loop, layered-vs-cluster idiom choice, and the `namedGraph` registration pattern.
---

# Authoring graphviz-pcs Figures

A `*-graphviz.pcs` file produces one or more named graphviz figures rendered
into an adjacent `images/` directory. This skill covers the iteration loop —
how to draft, render, revise, and embed a figure. For high-level orientation
on what graphviz-pcs is and how the pieces fit together, see the
`graphviz-pcs` activity's `AI-Activity.org`.

## Where to start

If you are authoring a *new* figure, decide first:

1. **What is the figure's job?** Read-time flow, install-time flow, static
   structure, concept map, layered architecture — each fits a different
   idiom (layered subgraphs vs clusters vs plain node-and-edge).
2. **What is the single takeaway?** A README figure should be summarisable
   in one sentence. If you can't state it, the figure isn't ready to draw.
3. **Where will it live?** A README figure needs tighter framing than a
   Blee-panel figure. A panel figure can carry more nodes because the
   viewer is already deep in the material.

If you are modifying an *existing* figure, read the surrounding prose
first — the figure's job is set by its context. Do not restructure a
figure without checking whether the prose still describes it.

## The iteration loop

The primary loop is: **draft → render → preview → revise**. Use the
`evince` format for iteration because it produces PDF *and* opens it:

```sh
./myFile-graphviz.pcs --format=evince -i ngProcess graphName
```

Evince stays open while you edit the source; re-running the command
re-renders the same file, and Evince picks up the change automatically.
This gives sub-second feedback per iteration.

For committing rendered artefacts (PNG for READMEs, SVG for panels):

```sh
./myFile-graphviz.pcs --format=png -i ngProcess graphName
./myFile-graphviz.pcs --format=svg -i ngProcess graphName
```

To batch-render every graph in every format when preparing a commit:

```sh
./myFile-graphviz.pcs --format=all -i ngProcess all
```

## Adding a new graph to an existing module

Three edits, in order:

1. **Write the function** with its surrounding COMEEGA dblocks:

   ```python
   ####+BEGIN: b:py3:cs:func/typing :funcName "myNewGraph" :funcType "Typed" :deco "track"
   """ #+begin_org
   *  ... /myNewGraph/  deco=track  ...
   #+end_org """
   @cs.track(fnLoc=True, fnEntry=True, fnExit=True)
   def myNewGraph(
   ####+END:
   ) -> graphviz.Digraph:
       d = graphviz.Digraph()
       # ... nodes, edges ...
       return d
   ```

   The region between `####+BEGIN:` and `####+END:` is dblock-generated;
   author only the body below `####+END:`. Copy the dblock header from an
   existing function and rename the `funcName` argument to match.

2. **Register in `namedGraphsList`** at the bottom of the file:

   ```python
   namedGraphsList = [
       ng("existingGraph", func=existingGraph),
       ng("myNewGraph",    func=myNewGraph),      # <-- new line
   ]
   ```

3. **Verify the examples menu picks it up:**

   ```sh
   ./myFile-graphviz.pcs
   ```

   Bare invocation produces the PyCS examples menu; the new graph should
   appear as its own block with `pdf`/`png`/`svg`/... variants.

No other registration is needed. The PyCS seed engine auto-discovers
whatever is in `namedGraphsList`.

### Manifest-at-top layout: forward reference via lambda

Some authors prefer to place `namedGraphsList` and `graphvizSeed.setup()`
*at the top* of the file (a "manifest" of what the file exports), with
function bodies below. This is a legitimate authorship style but
requires a small trick — Python resolves names at line-evaluation time,
so `ng("myGraph", func=myGraph)` at line 30 raises `NameError` when
`myGraph` isn't defined until line 60.

The fix is a nullary lambda:

```python
namedGraphsList = [
    # Forward reference: myGraph is defined below this block.
    ng("myGraph", func=lambda: myGraph()),
]
```

The seed engine calls `func()` when it needs the `Digraph`; by then
`myGraph` is bound in module globals and the lambda dereferences it.
Always add the explanatory comment — the lambda looks unusual and a
reader will otherwise wonder why not just `func=myGraph`.

The functions-first layout (natural Python order, no lambda needed) is
also fine. Pick by preference — some readers prefer the manifest at the
top like a table of contents; others prefer natural declaration order.

### Declaring title and caption for LCNT sidecars

If the figure will be included in a LaTeX document, org-mode `#+INCLUDE`,
or Blee panel with a caption, declare `title` and `caption` on the
`ng(...)` entry:

```python
namedGraphsList = [
    ng("myGraph",
       func=lambda: myGraph(),
       title="Short One-Line Title",
       caption="A longer prose caption describing what the figure "
               "shows, suitable for a figure caption in a LaTeX "
               "document or an org-mode #+CAPTION."),
]
```

Then `--format=lcnt` writes plain-text sibling files `myGraph.title`
and `myGraph.caption` alongside the rendered `.pdf` / `.png` / etc.
Consumers `\input{myGraph.title}` (LaTeX) or `#+INCLUDE:
"./myGraph.caption" export ascii` (org-mode) to embed the text in
their own figure envelope.

`--format=all` includes `lcnt`, so a routine "regenerate everything"
before commit will refresh the sidecars. Both fields are optional —
if omitted, no sidecar files are written for that graph.

## Choosing shape and colour — the semantic palette

Colours and shapes in the BISOS graphviz-pcs corpus are **semantic**, not
aesthetic. Reuse an existing meaning if one fits before introducing a new
one.

**Frequent choices for the common cases:**

- Framework / infrastructure / concept anchor → `darkseagreen3`, shape
  `rectangle` or `circle`.
- Directory / folder → `folder` shape; fill depends on whether it's a
  symlink (`lightgoldenrod1`) or a per-project directory (`mistyrose`).
- File → `note` shape; same fill convention as directories.
- Store / configuration source → `cylinder` shape; fill `lightsteelblue`
  for persistent stores, `lightyellow` for base paths.
- CLI parameter → `rectangle`, fill `lightblue`.
- Output / rendered artefact → `note` or `cylinder`, fill `darksalmon`.
- Interactive command / dispatcher → `rarrow` shape, fill `salmon` or
  `orange`.
- Consumer / external reader (e.g. Claude Code, user) → `ellipse`, fill
  `thistle`.

Full palette and shape table: see `AI-Activity.org` in the `graphviz-pcs`
activity.

**Rule of thumb**: if your figure has more than six colours, some of
them are probably decorative rather than semantic. Merge or drop.

## Layered vs cluster — which idiom

- **Layered** (`with d.subgraph() as s: s.attr(rank='same')`): use when
  the figure has a clear sequence of tiers, and the reader's eye should
  sweep top-to-bottom (or L→R with `rankdir='LR'`). Every node in one
  `rank='same'` subgraph sits on one visual band. Preferred idiom for
  pipeline, stack, and hierarchy figures.
- **Cluster** (`with d.subgraph(name='cluster_foo') as c`): use when
  nodes fall into named groups by concern rather than by sequence, and
  each group deserves a bounding box and label. The `cluster_` name
  prefix is significant — graphviz only draws a bounding box when the
  subgraph name starts with `cluster_`.
- **Mixing the two**: possible but fragile. Cluster subgraphs compete
  with `rank=` for layout authority. If you need both, use layered as
  the primary structure and clusters sparingly.

## Edge styling

- Style: `solid` (default), `dashed`, `dotted`.
- Direction: default is forward; use `dir='back'` to reverse without
  restating source/target, or `dir='both'` for bidirectional
  (persistent-store I/O, mutual references).
- Colour: any graphviz colour name; used semantically like fill colour.
- Label: `label='...'` for a text tag on the edge midpoint;
  `fontcolor=` to colour it independent of the line.
- `constraint='false'`: edge is drawn but does *not* influence rank
  assignment. Useful for cross-rank annotations that would otherwise
  distort layout (e.g. dotted "belongs-to" connectors within a single
  rank).
- Numbered edges: use `label='  1  '` (with padding) plus `color=` and
  `fontcolor=` in a distinctive colour to encode ordering (e.g. read
  sequence). Pad the label with spaces so it doesn't crowd the arrow.

## Embedding in README or panel

- **README (org-mode)**: `[[file:py3/images/graphName.png]]`. Renders
  inline on GitHub and PyPI. Prefer PNG over SVG for cross-tool
  reliability — GitHub renders SVG fine, PyPI is inconsistent.
- **Blee panel**: same relative-link syntax; Blee honours `#+ATTR_HTML`
  for size/alignment.
- **Legend placement**: put the legend *before* the figure. Readers
  pre-load the conventions and can then decode the picture in one
  glance. Legend-after-figure forces a scroll-back the first time a
  reader encounters an unfamiliar colour.
- Use an org table for the legend — more scannable than a bullet list.

## Commit both source and rendered outputs

The `images/` directory should hold both the `.pcs` source *and* the
committed rendered outputs (`.png`, `.pdf`, `.svg`, `.gv`). Consumers
of the repo should be able to view the figures without needing the
graphviz toolchain installed. Regenerate before commit with:

```sh
./myFile-graphviz.pcs --format=all -i ngProcess all
```

The `.gv` (DOT source) file is useful to commit alongside the rendered
outputs — it lets a reader inspect the graphviz-level intermediate
without running Python.

## Debugging layout surprises

When graphviz places nodes unexpectedly:

- **Nodes appearing on the wrong rank**: an edge is imposing a rank
  constraint. Add `constraint='false'` to edges that shouldn't
  influence layout.
- **Clusters and rank=same fighting**: the same node cannot be in both
  a `rank='same'` subgraph and a `cluster_` subgraph on the same
  authoritative pass. Pick one.
  The symptom is concrete: a cluster's *box disappears* (its nodes are
  laid out, unframed) when those nodes are also put in a `rank='same'`
  subgraph outside the cluster --- e.g. a column-ordering loop that wraps
  each pair in `with d.subgraph() as s: s.attr(rank='same')`. Keep the
  ordering edges plain (`d.edge(a, b, style='invis', constraint='false')`)
  or put the `rank='same'` subgraph *inside* the cluster.
- **`got multiple values for keyword argument 'style'`**: a node given a
  shared attribute dict and its own `style` (`**pythonNode, style=...`).
  Merge first: `**{**pythonNode, 'style': 'filled,dashed'}`.
- **Text spilling out of nodes**: labels can carry `\n` for line breaks;
  graphviz does not auto-wrap. Break long labels manually.
- **Edges crossing when they shouldn't**: try reordering the
  `d.edge(...)` calls — graphviz uses source order as a tiebreaker.
  Or set `d.attr(rankdir='LR')` if a horizontal flow avoids the
  crossing.
- **Layout dramatically changes between renders**: you may be using
  graphviz's non-deterministic layouts. Prefer `dot` (the default);
  avoid `neato` / `fdp` unless you specifically want force-directed.
- **Nodes in a `rank='same'` row come out in the wrong left-to-right
  order**: `dot` does *not* honour source order within the subgraph,
  and neither `dir='back'` nor a labelled flat edge pins it. Add
  invisible flat edges in the order you want
  (`d.edge(left, right, style='invis')`); `dot` always draws a flat edge
  tail-left, head-right.
- **A long back-edge (e.g. a "next item" loop) routes round the wrong side
  and crosses everything**: ports (`tailport='w'`) don't steer it. Route
  it through invisible waypoints, one `shape='point'` node per rank,
  pinned to the side you want. Chain the segments *top-down* (the ranking
  direction), with `dir='back'` on the segment whose arrowhead should show
  and `dir='none'` on the rest. A zero-size point leaves a visible gap in
  the line; use `width='0.03'` in the edge colour.
- **Many long edges back up to a few nodes at the top tangle**: draw
  thin-bordered *reference nodes* on the writer's own rank ("see above")
  so every edge is short, and explain the thin border in the legend.
- **A column of side nodes won't line up**: give them a shared `group`
  and chain them with invisible edges; `group` only straightens edges
  *between* members.
- **The legend widens or lengthens the image**: anchor it where there is
  already empty space. In TB figures, put it under the main path, not
  under a side label column. In LR trees, put it on the root's rank (a
  `rank='same'` subgraph with the root): that column is otherwise empty.

Worked examples of all of the above:
`/bisos/git/bxRepos/bisos-pip/aiActivity/py3/images/` (`aiUsageWorkflow`,
`aiStartupWorkflow`, `aiCommandsSkillsTrees`, `aiActivity`). (Before 2026-10-20 the first three were in
the templates tree's `_nonTemplate_/images/`.)

## When *not* to write a graphviz figure

Some information is better left as prose or a table:

- **State machines with more than ~7 states**: usually clearer as a
  table of transitions than a diagram.
- **File-directory layouts**: `tree` output in a code block is more
  precise and edit-friendly than a folder-node graph.
- **Sequence-of-operations**: often clearer as a numbered list. A
  graph implies non-linear structure; a list implies sequence.

If you're tempted to draw a figure that's just labels-and-arrows with
no visual weight to add, prose or a table probably wins.
