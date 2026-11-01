---
name: walkable-tree-planting
description: Use when planting a walkable filesystem tree on top of `bisos.fileObj` — either extending an existing seed (e.g. `bisos.dockerProc`, `bisos.lcnt`) to participate in walks, or authoring the branch-side `ftoBranchProc.spcs` files that let a BPO tree be walked top-down. Covers the two seed-side functions (`walkExamples()`, `leafProcessorNames()`) that the branch consumes, the branch `.spcs` template, marker-file conventions (mostly none, per Deliverable 5), and the two walker Cmnds (`fto_forwardToLeaves` Mode 1 verb-forwarding and `fto_walkRunExternal` Mode 2 external-cmnd walks) including the `recurseMode` subprocess/inProcess knob. Load `seeded-cs-commands` and `spread-seeded-cs-commands` first for the underlying `.pcs`/`.spcs` mechanism.
---

# Walkable Tree Planting

BISOS lets you build **walkable filesystem trees** where a top-level command
walks a tree and dispatches per-leaf work to a domain seed. Today's canonical
example: `bro_dockerfiles` (a tree of Dockerfile leaves) walked by
`bisos.fileObj`'s branch-side `ftoBranchProc.spcs`, dispatching to
`bisos.dockerProc.containerProc-seed.cs` at each leaf. Future consumers
(`bisos.lcnt`, static-web publication, `pypiProc.spcs`) follow the same
pattern.

This skill covers what you do to **make a tree walkable** — not the underlying
`.pcs`/`.spcs` machinery (see `seeded-cs-commands` and
`spread-seeded-cs-commands` for that) and not writing individual `cs.Cmnd`
subclasses (see `writing-cs-commands`).

## The three-box mental model

Every walkable tree involves three layers (see
`/bisos/git/auth/bxRepos/bisos-pip/pycs/spcs/README.org` for the diagram):

1. **PyCS Infrastructure** — `bisos.csSeed` (.spcs mechanism) + `bisos.fileObj`
   (walker, `WalkExampleSpec` dataclass, branch-side `ftoBranchProc.spcs` +
   `ftoBranch-seed.cs`, `fto_forwardToLeaves`, `fto_walkRunExternal`).
   *Consumed as-is.*
2. **Custom Seed** — the domain-specific package you author or extend
   (`bisos.dockerProc` today; `bisos.lcnt` etc. tomorrow). Provides
   Cmnds that operate at one leaf, plus **two special functions** that let
   the walker discover leaves and populate the branch's examples menu.
3. **Planted Tree** — the on-disk BPO/`bro_*` tree of directories. You
   plant `ftoBranchProc.spcs` at each branch you want to walk from, and
   leaf `.spcs` files at each leaf. Marker files (`_tree_`, `_treeProc_`)
   are usually not needed.

This skill covers *Box 2 additions* (two functions) and *Box 3 fully* (the
tree-planting mechanics).

## What the domain seed must expose

Two module-level functions in the seed's `_seedInfo.py`. Both are consumed by
the branch's `ftoBranchProc.spcs` and passed to
`ftoBranch_seedInfo.setup(...)`.

### `leafProcessorNames() → list[str]`

Filenames whose *presence in a directory* identifies that directory as a
leaf. Definitional leaf detection — no `_tree_=leaf` marker file needed
(Deliverable 5). Symmetric with the leaf `.spcs` files your seed already
ships.

```python
def leafProcessorNames() -> list[str]:
    """Filenames identifying a leaf directory for this domain."""
    return ['dockerProc.spcs', 'podmanProc.spcs']
```

The walker uses this list at every visited directory: if any of these
filenames exists at path X, X is a Leaf. Otherwise (and no `_tree_` marker),
X is treated as AuxBranch (traverse but don't apply) — per Deliverable 5's
auxBranch default.

### `walkExamples() → list[WalkExampleSpec]`

The catalog of "which of my Cmnds make sense to walk with." Renders in the
branch's `-i examples` menu as a "Leaf-Provided Walk Examples" chapter, one
`fto_forwardToLeaves --cmndName=X` entry per spec. **This is the source of
truth** for what walking makes sense across your domain's leaves — update
here once, every planted branch under any consumer tree picks it up.

`WalkExampleSpec` lives in `bisos.fileObj.ftoBranch_seedInfo`. Import lazily
to avoid a hard `bisos.fileObj` dependency at seedInfo module-load time:

```python
def walkExamples() -> list:
    """WalkExampleSpec entries for this domain's Cmnds."""
    from bisos.fileObj.ftoBranch_seedInfo import WalkExampleSpec
    return [
        WalkExampleSpec(
            cmndName='<domain>_instancePs',
            comment="# read-only: list instances at this leaf",
            tags=frozenset({'read-only'}),
        ),
        WalkExampleSpec(
            cmndName='<domain>_imageBuild',
            pars={'noCache': 'true'},
            comment="# --no-cache build",
            tags=frozenset({'destructive', 'build'}),
        ),
        # ... one entry per verb worth walking with
    ]
```

`WalkExampleSpec` fields:

| Field       | Purpose                                                                   |
|-------------|---------------------------------------------------------------------------|
| `cmndName`  | For Mode 1 forwarding: the leaf-side Cmnd verb name. For Mode 2 external: the external cmnd (`argv[0]`). |
| `pars`      | Dict of param-name → value forwarded to the leaf Cmnd (Mode 1) or ignored (Mode 2). |
| `args`      | For Mode 2: args appended after `cmndName`. Ignored for Mode 1.           |
| `comment`   | One-line description shown after the invocation in the menu.              |
| `mode`      | `'forwardToLeaves'` (Mode 1, default) or `'walkRunExternal'` (Mode 2).    |
| `tags`      | Free-form frozenset for future filtering (e.g. `read-only`, `destructive`). |

Canonical example: see
`/bisos/git/auth/bxRepos/bisos-pip/dockerProc/py3/bisos/dockerProc/containerProc_seedInfo.py`
— 13 entries covering the full `containerProc_*` surface.

## Planting a walkable tree — the recipe

Assume the domain seed exists and exposes both `leafProcessorNames()` and
`walkExamples()`. To make an existing directory tree walkable:

### 1. Plant the leaf `.spcs` files (usually already done)

Each leaf directory needs its domain `.spcs` file (`dockerProc.spcs`,
`podmanProc.spcs`, `lcntProc.spcs`, etc.). This is the file the domain seed
already ships in `py3/bin/`; the tree author plants a copy or symlink at each
leaf. **This is a `.spcs`-mechanism concern** — see `spread-seeded-cs-commands`
for the authoring / planting details.

Make sure each planted leaf `.spcs` is `chmod +x`.

### 2. Plant the branch `.spcs` at each level you want to walk from

At each directory you want to invoke walks from (typically the root of a
tree or a subtree), plant an `ftoBranchProc.spcs` with content:

```python
#!/usr/bin/env python
""" #+begin_org
* ~[Summary]~ :: ftoBranchProc Spread Planted CS --- for the =<tree-path>= branch.
#+end_org """

from bisos.fileObj import ftoBranch_seed  # noqa: F401  # _atExit_
from bisos.fileObj import ftoBranch_seedInfo

from bisos.<domain> import <domain>_seedInfo   # e.g. bisos.dockerProc.containerProc_seedInfo

ftoBranch_seedInfo.setup(
    leafExamples=<domain>_seedInfo.walkExamples(),
    leafProcessors=<domain>_seedInfo.leafProcessorNames(),
)

def examples_pcs() -> None:
    pass
```

`chmod +x` it. The `ftoBranch_seed` import triggers an atexit hook that
invokes `bisos.fileObj.ftoBranch-seed.cs` when the `.spcs` runs. The
`setup()` call populates the singleton so the walker knows how to identify
leaves in this tree and how to render the domain's examples menu.

**Where to plant it:** at every directory you want to run walks from. For
`bro_dockerfiles`, that's `debian/`, `debian/12/`, `debian/13/`, and each of
the six leaf-adjacent branches. From any of these you can invoke a walk
that dispatches to descendant leaves.

**Content across all planting sites is identical** — that's the "spread" in
Spread Planted CS. Rewrite only the docstring's path reference for
readability if desired.

### 3. Marker files — usually none

Post-Deliverable-5, unmarked directories default to auxBranch (traverse
but don't apply). Leaf detection is definitional via `leafProcessorNames()`.
So you typically need **zero** `_tree_` / `_treeProc_` marker files.

Exceptions where you might want explicit markers:
- **Regression canary.** Keep one branch with explicit markers so the
  legacy code path stays exercised (`bro_dockerfiles/debian/12/confined/`
  is kept this way for this reason).
- **`_tree_=auxLeaf`** — "this directory looks like a leaf but skip
  applying commands here." Rare; explicit override.
- **`_tree_=ignore`** — "skip me and everything below." Useful to hide a
  WIP subtree from walks.

If you need to stamp explicit markers, `fto_branchCreate`, `fto_leafCreate`,
`fto_auxBranchCreate`, `fto_auxLeafCreate`, `fto_ignoreCreate` Cmnds are
available. They're niche — the recommended path is markerless.

### 4. Verify the tree walks correctly

From any planted branch:

```
./ftoBranchProc.spcs -i fto_treeList
```

Should print `Branch:` at the current dir, `Leaf:` at each descendant leaf
directory, and traverse silently through intermediates (they show up as
`visited:` but not `Leaf:`).

## Walking

Two Cmnds. Both are exposed at any planted branch. The difference:
who supplies the executable at each leaf.

### `fto_forwardToLeaves --cmndName=X` — Mode 1

Invokes `<leafDir>/<_treeProc_> -i X` at each effective leaf. The verb `X`
is a Cmnd name the *leaf's own dispatcher* understands. Different leaves
can have different `_treeProc_` (e.g. `dockerProc.spcs` at docker leaves,
`podmanProc.spcs` at rootless-sysd leaves) and implement `-i X` however
they wish.

```
./ftoBranchProc.spcs -i fto_forwardToLeaves --cmndName=containerProc_imageBuild
./ftoBranchProc.spcs -i fto_forwardToLeaves --cmndName=containerProc_instanceUp --recurseMode=inProcess
```

The branch itself is NOT applied — forwarding targets leaves only.

### `fto_walkRunExternal <cmnd> [args...]` — Mode 2

Invokes an **external** cmnd at each visited node (branch, auxBranch, leaf
— but not auxLeaf or ignore), running it in that node's directory. The
leaf's `_treeProc_` is *not* consulted; the external cmnd supplies its
own executable. Resolution ("perhapsRun"): `<nodeDir>/<cmnd>` first, then
`shutil.which(cmnd)`; skip silently if neither.

```
./ftoBranchProc.spcs -i fto_walkRunExternal git status
./ftoBranchProc.spcs -i fto_walkRunExternal ls -la _tree_
./ftoBranchProc.spcs -i fto_walkRunExternal pypiProc.sh -i pkgReInstall edit /bisos/venv/py3/bisos3
```

Matches bash `ftoWalkRunCmnd` semantics.

### `recurseMode` — subprocess vs in-process (Deliverable 6)

Both Cmnds accept `--recurseMode`:

- **`subprocess`** (default) — each sub-branch that has its own
  `ftoBranchProc.spcs` is invoked as a subprocess. That subprocess re-runs
  its own `.spcs`, re-establishes its own domain context, and walks its own
  subtree autonomously. Results stream to each subprocess's stdout; the
  parent does NOT merge them. **This is what enables heterogeneous walks**
  (a top-level branch spanning multiple domains where each subtree
  establishes its own context).

- **`inProcess`** — opt-in for homogeneous trees. Single Python process
  walks the whole subtree. One flat aggregate result. Faster (no
  subprocess spawn overhead) but only correct when every branch shares
  the same domain seed / `leafProcessors` / etc.

For the default subprocess mode, no aggregation across sub-branches:
each subprocess prints its own `visited=N failed=M skipped=K` line. Users
post-process the stream (`grep`, `awk`) if they need tree-wide totals.

### Ordering leaves

`branchesOrdered` / `leavesOrdered` in a branch `.spcs` are taken *verbatim* as
the names of that branch's **direct** children (ordered = authoritative; excludes
ignored). They do not reach leaves one or more plain directories below (e.g.
`debian/13/privileged/vnc/xfce/<leaf>`): to order those, plant a branch `.spcs` at
their level. Without a list, children are walked in sorted order. (A redesign,
`childNodesOrdered`, is a TODO in `bisos.fileObj`'s AI-WorkPlan, Stage 3.)

## Generic lifecycle verbs --- `fto_prepare` ... `fto_status` (bisos.fileObj)

`bisos.fileObj` defines one lifecycle vocabulary for every kind of walkable
leaf, with a CBM-style gate and status log, so one walk can drive leaves of
different kinds. The reference is `bisos.fileObj`'s README, "Generic Lifecycle
Verbs"; first consumer: `bisos.dockerProc`.

| Verb                | Means                                   | Runs when the gate is |
|---------------------+-----------------------------------------+-----------------------|
| `fto_prepare`       | make ready to run (non-destructive)     | not `disabled`        |
| `fto_materialize`   | bring to the running state              | `enabled`             |
| `fto_reMaterialize` | re-create with the current preparation  | `enabled`             |
| `fto_unMaterialize` | take the running state down             | `enabled`             |
| `fto_clean`         | undo prepare                            | `enabled`             |
| `fto_verify`        | check (read-only)                       | not `disabled`        |
| `fto_status`        | show state (read-only, not logged)      | not `disabled`        |

- **Gate and log in the leaf**, named after its planted file:
  `<leaf>/<plantStem>.control` (`enabled` | `available` | `disabled`; missing =
  `available`; `disabled` = leave the leaf completely alone) and
  `<leaf>/<plantStem>.status` (one timestamped line per run). Same formats as
  CBM's `cbmProc.control` / `cbmProc.status`. Gate commands, always run:
  `fto_control`, `fto_statusLog`, `fto_enable`, `fto_available`, `fto_disable`.
  Whether to commit the files is the tree's call (bro_rawBisos commits its
  `cbmProc.*`; bro_dockerfiles git-ignores its `dockerProc.*`: one VM per clone).
- **A consumer (leaf seed) does three things:** registers what each verb does,
  in its csu module at import:
  ```python
  from bisos.fileObj import ftoLeaf_seedInfo
  ftoLeaf_seedInfo.setup(prepare=_prepare, materialize=_materialize, ...)  # (cmndOutcome) -> Outcome
  ```
  (a verb left out is "unsupported": success, logged `skipped: unsupported`);
  adds `bisos.fileObj.ftoLeaf_csu` to its **leaf** seed's `csuList` spec and has
  the `csuListImportPlus` dblock regenerated (Blee); appends
  `ftoLeaf_seedInfo.lifecycleWalkExamples()` to its `walkExamples()` and calls
  `ftoLeaf_seedInfo.lifecycleExamplesMenu()` in its leaf menu.
- **At a branch the same names walk**: `./ftoBranchProc.spcs -i fto_prepare`
  forwards to every leaf below, hands the same verb to sub-branches with their
  own `.spcs`, and ends with a summary read back from the leaves' status logs
  (`ran / skipped / failed / noLog`) --- because walk exit codes are unreliable
  (`bisos.b` exits 0 on failure). Branch `.spcs` files need no change.

## Coexistence with legacy explicit markers

The walker still honors explicit `_tree_` / `_treeProc_` files when they
exist. This makes both styles coexist in the same tree, which is useful
for gradual migration or intentional regression canaries.

Precedence rules (highest first):
1. `_tree_=ignore` marker — skip entire subtree.
2. `_tree_` marker with any other value — respected.
3. Directory contains a file in `leafProcessors` — classified as Leaf
   (definitional).
4. No marker and no leaf-processor match — default to AuxBranch
   (Deliverable 5).

## Higher-level branches for one-shot multi-tree walks

Once you have a leaf-adjacent `ftoBranchProc.spcs` at each of several
sibling branches, you can plant additional `ftoBranchProc.spcs` files at
higher levels to enable "walk all sibling subtrees in one shot." The
content is identical — same imports, same `setup()` call from the domain
seed.

Example: `bro_dockerfiles/debian/ftoBranchProc.spcs` fans out to all 6
image leaves; `bro_dockerfiles/debian/12/ftoBranchProc.spcs` fans out to
the 3 deb12 leaves; each leaf-adjacent branch fans out to 1 leaf. The
tree structure encodes the filter: filter-by-flag becomes
filter-by-location.

Under `recurseMode=subprocess` (default), the top-level walk streams
per-subprocess aggregate summaries — one line per branch subprocess. This
is a clean unix pipeline: post-process with `grep` / `awk` as needed.

## Pilot recipe: from zero to walkable tree

Assume you have a domain seed package that exposes Cmnds at each leaf but
has not yet added the two walkable-tree hooks.

1. **Extend the domain seed's `_seedInfo.py`:** add `walkExamples()` and
   `leafProcessorNames()` module-level functions (patterns above).
2. **Verify the seed installs:** `pypiProc.sh -i pkgReInstall` and confirm
   `python3 -c "from bisos.<domain>.<pkg>_seedInfo import walkExamples,
   leafProcessorNames; print(walkExamples()); print(leafProcessorNames())"`
   works.
3. **Plant an `ftoBranchProc.spcs`** at the root of the tree you want to
   walk. Use the template above with `<domain>` filled in. `chmod +x`.
4. **Confirm leaves are discovered:**
   ```
   cd <tree-root>
   ./ftoBranchProc.spcs -i fto_treeList
   ```
   Should show `Leaf:` for every directory containing a leaf `.spcs`.
5. **Confirm the examples menu renders correctly:**
   ```
   ./ftoBranchProc.spcs
   ```
   Should show a "Leaf-Provided Walk Examples" chapter with one entry per
   `WalkExampleSpec`.
6. **Try a read-only walk:**
   ```
   ./ftoBranchProc.spcs -i fto_forwardToLeaves --cmndName=<read-only-verb>
   ```
   Should dispatch to every leaf.
7. **If you want one-shot walks at higher levels:** plant additional
   `ftoBranchProc.spcs` copies at parent directories. Same content.

## What NOT to do

- **Don't hand-plant marker files** by default. The markerless pattern
  (Deliverable 5) is the recommended path. Only plant markers for
  intentional overrides (`_tree_=auxLeaf`, `_tree_=ignore`) or as a
  regression canary.
- **Don't merge subprocess results in your `.spcs`.** The stream-of-
  aggregates output is the intended semantic. Aggregation happens in the
  user's pipeline, not in the walker.
- **Don't import the domain seed's Cmnd module from the branch `.spcs`.**
  The branch `.spcs` should only import `_seedInfo` (small, side-effect-free)
  and pass its outputs to `ftoBranch_seedInfo.setup()`. Importing `_csu`
  or `-seed.cs` would pull in every Cmnd class at branch load time,
  which is unnecessary and slow.
- **Don't put walk-example strings in the branch `.spcs`.** The source of
  truth is the domain seed's `walkExamples()`. Copying strings into
  branches invites drift.
- **Don't add `bisos.fileObj.ftoLeaf_csu` to the branch seed**
  (`ftoBranch-seed.cs`). It belongs in the *leaf* seed's `csuList`; in the
  branch seed its leaf `fto_*` would replace the branch-side ones (same names,
  later module wins), so branch verbs would act on the branch directory instead
  of walking.
- **Don't copy the gate code into a consumer** (`controlRead`, `statusWrite`,
  ...). Use `bisos.fileObj.ftoLeaf_seedInfo` --- the copies drift.
- **Don't add new walker-level parameters as CS params** on
  `fto_forwardToLeaves` / `fto_walkRunExternal` unless the recurse
  behavior genuinely needs them. Each subprocess re-invokes the Cmnd from
  scratch and picks up its own state; adding CLI-level params just to
  thread state through subprocess boundaries fights the design.

## Related skills (load first)

- **`seeded-cs-commands`** — `.pcs` (Planted CS) authoring, seed CSXU +
  `_seed.py` + `_seedInfo.py` + `_csu.py` package anatomy.
- **`spread-seeded-cs-commands`** — the `.spcs` delta on `.pcs`: path-as-
  parameter, `paramsFromPlantPath()`, when to spread vs plant. **Load this
  before this skill** if you're new to the `.spcs` mechanism.
- **`writing-cs-commands`** — `cs.Cmnd` subclass authoring: `classHead`
  dblock, params, args, body shape.

## Canonical references

**Architectural narrative + figure:**
- `/bisos/git/auth/bxRepos/bisos-pip/pycs/spcs/README.org` — three-box
  architecture, walker mechanics, the whole picture.

**Framework (Box 1 — infrastructure you don't touch):**
- `/bisos/git/auth/bxRepos/bisos-pip/fileObj/py3/bisos/fileObj/fto.py` —
  walker library, `WalkResult`, `treeRecurse`, `BRANCH_SPCS_FILENAME`.
- `/bisos/git/auth/bxRepos/bisos-pip/fileObj/py3/bisos/fileObj/ftoBranch_seedInfo.py`
  — `WalkExampleSpec`, `FtoBranchSeedInfo` singleton, `setup()`.
- `/bisos/git/auth/bxRepos/bisos-pip/fileObj/py3/bin/ftoBranch-seed.cs` —
  branch-side seed CSXU.
- `/bisos/git/auth/bxRepos/bisos-pip/fileObj/py3/bin/ftoBranchProc.spcs` —
  the *template* for what you plant.

**First concrete consumer (Box 2 — canonical example of what you author):**
- `/bisos/git/auth/bxRepos/bisos-pip/dockerProc/py3/bisos/dockerProc/containerProc_seedInfo.py`
  — `leafProcessorNames()`, `walkExamples()` (13 entries).
- `/bisos/git/auth/bxRepos/bisos-pip/dockerProc/py3/bin/containerProc-seed.cs`
  — domain seed CSXU.

**First real planted tree (Box 3 — canonical example of what you plant):**
- `/bisos/git/auth/bxRepos/bxObjects/bro_dockerfiles/debian/ftoBranchProc.spcs`
  — top-level branch (all 6 leaves).
- `/bisos/git/auth/bxRepos/bxObjects/bro_dockerfiles/debian/12/ftoBranchProc.spcs`
  — release-level branch (3 deb12 leaves).
- `/bisos/git/auth/bxRepos/bxObjects/bro_dockerfiles/debian/12/confined/ftoBranchProc.spcs`
  — profile-level branch (1 leaf; kept with explicit markers as regression canary).
- `/bisos/git/auth/bxRepos/bxObjects/bro_dockerfiles/debian/12/rootless-sysd/vnc/xfce/bisos_deb12-rootless-sysd/podmanProc.spcs`
  — a leaf `.spcs` (the domain seed planted at a leaf).
