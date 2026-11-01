---
name: spread-seeded-cs-commands
description: Use when creating, reading, or modifying a `.spcs` (Spread Planted Command Service) — a seeded CS where the planted file's directory path is an implicit parameter source in addition to the file's own content. Load `seeded-cs-commands` first for base `.pcs` concepts; this skill covers only the `.spcs` delta: the path-as-parameter mechanism, when to spread vs plant, how to author `paramsFromPlantPath()` in the seed, and path-parsing guidelines.
---

# Spread Planted Command Services (`.spcs`)

Load the `seeded-cs-commands` skill first. This skill covers only the delta
that distinguishes `.spcs` from `.pcs`.

## The One Difference: Directory Path as Implicit Parameters

A `.pcs` (Planted CS) receives all its parameters from **within the file**.

A `.spcs` (Spread Planted CS) receives parameters from **two sources**:
1. Content within the `.spcs` file (same as `.pcs` — explicit `seedInfo.setup()` calls).
2. The **directory path in which the `.spcs` file resides** (implicit — parsed by the seed).

The seed receives `seededCsxuInfo.plantOfThisSeed` (`sys.argv[0]` of the `.spcs`
invocation) and parses it to extract operating context from the path segments.
The filesystem hierarchy IS the configuration — no separate parameter file needed.

## The "Spread" in Spread Planted

The same `.spcs` file content is **spread identically** across many directories.
Each instance is contextualised entirely by its location. This contrasts with
`.pcs`, where each file is individually authored for its specific target.

| | `.pcs` | `.spcs` |
|---|---|---|
| Parameters from within the file | yes | yes (via `setup()`) |
| Parameters from directory path | no | **yes** (parsed by seed) |
| One file per target | yes | no — same file, many locations |
| Adding a new instance requires | new `.pcs` file | new directory only |

## When to Use `.spcs` Instead of `.pcs`

Use `.spcs` when:
- The **same file content** will be planted in multiple locations and the only
  variation between instances is their position in a structured hierarchy.
- The hierarchy itself encodes all (or most) of the per-instance parameters.
- Adding a new instance means adding a directory and its assets, not authoring
  a new configuration file.

Use `.pcs` when each instance has meaningfully distinct explicit parameters
that cannot be derived from a path structure.

## Mechanism

`seedsLib.plantWithWhich(seededCsxu)` (called via the `atexit` hook in the
seed's import) resolves the seed executable, records:
- `seededCsxuInfo.seedOfThisPlant` — the seed name (e.g. `dockerProc-seed.cs`)
- `seededCsxuInfo.plantOfThisSeed` — the `.spcs` file's own resolved path

The seed reads `plantOfThisSeed` and passes it to `paramsFromPlantPath()` to
derive the implicit parameters for that planted instance.

## Authoring: Changes Needed in the Seed

The `.spcs` file itself is written exactly like a `.pcs` file. The additional
work is entirely in the **seed package**:

### 1. Add `paramsFromPlantPath()` to `_seedInfo.py` (or the data module)

```python
import pathlib
from bisos.csSeed import seedsLib

def paramsFromPlantPath() -> dict:
    plant = seedsLib.seededCsxuInfo.plantOfThisSeed
    if plant is None:
        return {}
    parts = pathlib.Path(plant).parts
    # Anchor on a known segment rather than counting from root —
    # the absolute prefix varies across machines.
    try:
        anchor = parts.index("debian")   # example anchor for bro_dockerfiles
    except ValueError:
        raise ValueError(f"Expected 'debian' segment in plant path: {plant}")
    # Extract segments relative to anchor
    release  = parts[anchor + 1]   # "12" or "13"
    profile  = parts[anchor + 2]   # "confined" / "privileged" / "rootless-sysd"
    # ... derive remaining params
    return {"release": release, "profile": profile, ...}
```

Rules:
- Make it a **pure function** (no side effects) — independently testable.
- **Anchor on a known named segment**, not a numeric index from root.
- **Raise `ValueError` clearly** if the path does not match the expected
  structure — mis-planted files must fail loudly, not silently produce wrong params.
- Return a plain `dict` or a typed dataclass; document each derived field.

### 2. Merge path-derived params in `_csu.py` commands

Commands call `paramsFromPlantPath()` at dispatch time and merge with any
explicit `seedInfo` fields:

```python
from bisos.dockerProc import dockerProc_seedInfo

class dockerProc_build(cs.Cmnd):
    def cmnd(self, rtInv, cmndOutcome, ...):
        pathParams = dockerProc_seedInfo.paramsFromPlantPath()
        release = pathParams["release"]
        profile = pathParams["profile"]
        # ... use params
```

### 3. The `.spcs` file calls `setup()` only for non-path parameters

If the path encodes everything, `setup()` may be a no-op or omitted entirely.
Only supply explicit params for things that genuinely cannot be derived from
the path (e.g. a runtime override, a non-structural option).

### 4. Name the file `<seedName>.spcs`

The filename is **identical across all planted instances** — the directory is
what distinguishes them. E.g. `dockerProc.spcs` appears in all six image leaf
directories; `pypiProc.sh` appears in all 50+ `bisos-pip/<pkg>/py3/` dirs.

## Path Parsing Guidelines

- Use `pathlib.Path(plantOfThisSeed).parts` to get all path segments as a tuple.
- **Anchor on a known segment** (e.g. `"debian"`, `"bisos-pip"`) — never count
  from index 0, as the absolute prefix differs across machines and users.
- After finding the anchor index, extract relative segments by offset:
  `parts[anchor + N]`.
- For optional segments or variable-depth paths, search for known segment names
  rather than relying on fixed offsets.
- Return a typed result (dataclass preferred over plain dict for larger param sets).
- Test `paramsFromPlantPath()` with representative paths in `examples_csu()`.

## Existing `.spcs` Implementations

**Bash precedent — `pypiProc.sh`** (50+ instances across `bisos-pip`):
```bash
# Entire planted file:
if [ "${loadFiles}" == "" ] ; then
    /bisos/core/bsip/bin/seedPypiProc.sh -l $0 "$@"
    exit $?
fi
```
The seed receives `$0`, derives package name, namespace (`bisos.`), Python
version (`py3`), repo root, and build/dist paths from `dirname $0`.
No per-package config file exists anywhere.

Reference: any `bisos-pip/<pkg>/py3/pypiProc.sh` (all identical content).

**Python — `djangoProc.spcs`, `reactProc.spcs`** (`bisos.webCap`):
The seed uses `plantOfThisSeed` to locate the Django/React project root
relative to the planted file's directory.

Reference:
- `/bisos/git/auth/bxRepos/bisos-pip/webCap/py3/bin/djangoProc.spcs`
- `/bisos/git/auth/bxRepos/bisos-pip/webCap/py3/bin/reactProc.spcs`
- `/bisos/git/auth/bxRepos/bisos-pip/webCap/py3/bisos/webCap/djangoProc_seedInfo.py`

**Planned — `dockerProc.spcs`** (`bisos.dockerProc` + `bro_dockerfiles`):
Planted in each of six image leaf directories. Path
`debian/<release>/<profile>/vnc/xfce/<imageName>/` encodes:

| Path segment  | Parameter derived                                                    |
|---------------|----------------------------------------------------------------------|
| `debian`      | distro (anchor segment)                                              |
| `<release>`   | `12` or `13` → base OS, base image tag                              |
| `<profile>`   | `confined` / `privileged` / `rootless-sysd` → engine, init, privilege |
| `vnc/xfce`    | desktop type → VNC/noVNC ports, xstartup variant                    |
| `<imageName>` | image name → DockerHub name, container name                          |

Reference:
- Work plan: `/bisos/git/auth/bxRepos/bxObjects/bro_dockerfiles/AI-WorkPlan.org` Stage 5
- Blee panel: `/bisos/git/auth/bxRepos/bisos-pip/csSeed/py3/panels/bisos.csSeed/dotSPCS-SpreadPlantedCS/_nodeBase_/fullUsagePanel-en.org`

## Framework Reference

- `seedsLib.py` (plantWithWhich, SeededCsxuInfo):
  `/bisos/git/auth/bxRepos/bisos-pip/csSeed/py3/bisos/csSeed/seedsLib.py`
- `bisos.csSeed` source:
  `/bisos/git/auth/bxRepos/bisos-pip/csSeed/`
