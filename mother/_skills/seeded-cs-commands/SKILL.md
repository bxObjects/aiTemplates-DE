---
name: seeded-cs-commands
description: Use when creating, reading, or modifying a seeded CS package — a bisos-pip package whose entry point is a `.cs` seed file extended by `.pcs` (Planted Command Service) files. Covers the package anatomy, the three ways `.pcs` files pass input to the seed (scalar controlInfo fields as in `bisos.capDns`, typed lists via factory functions and `setup()` as in `bisos.sbom`, or a combination of both), and how to author a new capability package in either style.
---

# Seeded CS Commands and `.pcs` Planted Command Services

A **seeded CS package** is a bisos-pip pattern where a reusable set of CS
commands (the *seed*) can be invoked either directly via the seed's `.cs`
entry point, or extended by a per-target `.pcs` (*Planted Command Service*)
file that configures the seed for a specific use case.

Two reference implementations exist:
- `bisos.capDns` — `.pcs` passes scalar control parameters via a `CmndsControlInfo` dataclass.
- `bisos.sbom` — `.pcs` passes typed lists of inputs (packages, specs) via factory functions and a `setup()` call.

A `.pcs` file may use either style, or combine both.

## Three Ways a `.pcs` File Passes Input to the Seed

The `.pcs` pattern is flexible. A `.pcs` file can configure the seed in three ways:

**1. Scalar controlInfo** (`bisos.capDns` style)

The package defines a `CmndsControlInfo` singleton dataclass in `_seedInfo.py`.
The `.pcs` sets individual fields on it before declaring `csCmndsList`:

```python
cntrlInfo.dnsSpecMethod = capDns_seedInfo.DnsSpecMethod.etcHosts
cntrlInfo.fqdn = "airflow.here"
```

Use this when each invocation targets a single entity described by a small
number of named parameters (a hostname, a method enum, a path, etc.).

**2. Typed lists** (`bisos.sbom` style)

The package defines factory functions and a `setup()` call in its data module
(e.g. `pkgsSeed.py`). The `.pcs` builds lists of typed objects and passes them
to `setup()`:

```python
aptPkgsList  = [ ap("djbdns"), ap("facter"), ap("gh", func=ghAptSource), ]
pipPkgsList  = [ pp("bisos.marmee"), ]
pipxPkgsList = [ pp("bisos.marmee"), ]
sbomsList    = [ sbomSpec("exmpl-sbom.pcs"), ]

pkgsSeed.setup(
    aptPkgsList=aptPkgsList,
    pipPkgsList=pipPkgsList,
    pipxPkgsList=pipxPkgsList,
    sbomsList=sbomsList,
)
```

Use this when the seed operates over a collection of items (packages to
install, repos to clone, files to process, etc.) where the set varies per
deployment.

**3. Combination**

A `.pcs` file may both populate a `cntrlInfo` singleton *and* call a `setup()`
with lists — for seeds that need both a target identity and a collection of
items to operate on.

The atexit wiring, `csCmndsList` declaration, and seed dispatch mechanism are
identical across all three styles.

## The Package Anatomy

A seeded CS package under `py3/bisos/<pkgName>/` has these files:

| File                 | Style  | Role                                                              |
|----------------------|--------|-------------------------------------------------------------------|
| `<pkg>_seedInfo.py`  | scalar | Defines `CmndsControlInfo` dataclass and enums.                   |
|                      |        | Singleton `cmndsControlInfo` is set by `.pcs` files.              |
| `<pkg>_seed.py`      | scalar | Thin file: registers seed name via `atexit_plantWithWhich`.       |
| `<pkg>DataModule.py` | list   | Combined data model + seed registration.                          |
|                      |        | Defines typed item classes, factory functions, and `setup()`.     |
|                      |        | Contains `atexit_plantWithWhich` — no separate `_seed.py` needed. |
|                      |        | Example: `pkgsSeed.py` in `bisos.sbom`.                           |
| `<pkg>_csu.py`       | both   | CS-Lib with all `cs.Cmnd` command classes.                        |
| `<pkg>_seed.cs`      | both   | Executable csxu entry point. Loads planted `.pcs` if active.      |

## `_seedInfo.py` — Control Parameters

This file owns the dataclass that `.pcs` files populate. Pattern:

```python
import enum
from dataclasses import dataclass

@enum.unique
class DnsSpecMethod(enum.Enum):
    etcHosts = "etcHosts"
    tinydns  = "tinydns"

@dataclass
class CmndsControlInfo(object):
    dnsSpecMethod: DnsSpecMethod | None = None
    fqdn: str | None = None

    # Singleton enforcer
    _instance = None
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

cmndsControlInfo = CmndsControlInfo()   # the singleton used by .pcs files
```

Rules:
- `CmndsControlInfo` is a **singleton dataclass**. There is exactly one
  instance, created at module level as `cmndsControlInfo`.
- Fields default to `None`. `.pcs` files set them before `csCmndsList` is
  declared.
- Add an enum for any field with a fixed set of choices (like `DnsSpecMethod`).
- Also define `<Pkg>SeedInfo` (another singleton dataclass) with `seedType`
  and `examplesFuncsList` — this is boilerplate; copy from the reference.

## `_seed.py` — Seed Registration

Thin file. Its sole job is to register the seed name via `atexit`:

```python
import atexit
from bisos.csSeed import seedsLib

seedCSMU = 'capDns_seed.cs'

@atexit.register
def atexit_plantWithWhich(asExpected: str = seedCSMU) -> None:
    seedsLib.plantWithWhich(asExpected)
```

The `@atexit.register` decoration ensures `plantWithWhich` fires when the
Python interpreter exits, binding the seed name to whatever `.pcs` file
invoked it. Do not add logic here.

## List-Style Data Module — `pkgsSeed.py` Pattern (`bisos.sbom`)

When the seed operates over a collection of items, the data module combines
the data model, factory functions, `setup()`, and seed registration in one file.
There is no separate `_seedInfo.py` or `_seed.py`.

```python
from dataclasses import dataclass
import atexit
from bisos.csSeed import seedsLib

@dataclass
class AptPkg:
    name: str
    func: typing.Callable | None = None
    osVers: str | None = None

@dataclass
class PipPkg:
    name: str
    func: typing.Callable | None = None
    ver: str | None = None

# Factory functions used by .pcs files
def aptPkg(pkgName, func=None, osVers=None): return AptPkg(pkgName, func, osVers)
def pipPkg(pkgName, func=None, ver=None):    return PipPkg(pkgName, func, ver)

@dataclass
class PkgsSeedInfo:
    aptPkgsList:  list | None = None
    pipPkgsList:  list | None = None
    pipxPkgsList: list | None = None
    sbomsList:    list | None = None
    examplesHook: typing.Callable | None = None

    _instance = None
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

pkgsSeedInfo = PkgsSeedInfo()   # singleton

def setup(aptPkgsList=None, pipPkgsList=None, pipxPkgsList=None,
          sbomsList=None, examplesHook=None):
    pkgsSeedInfo.aptPkgsList  = aptPkgsList  or []
    pkgsSeedInfo.pipPkgsList  = pipPkgsList  or []
    pkgsSeedInfo.pipxPkgsList = pipxPkgsList or []
    pkgsSeedInfo.sbomsList    = sbomsList    or []
    pkgsSeedInfo.examplesHook = examplesHook

# Seed registration — same atexit mechanism as _seed.py
@atexit.register
def atexit_plantWithWhich(asExpected: str = 'seedSbom.cs') -> None:
    seedsLib.plantWithWhich(asExpected)
```

Key points:
- The `_csu.py` reads from `pkgsSeedInfo` (the singleton) rather than
  `cmndsControlInfo`.
- The `setup()` call in the `.pcs` file replaces the field-by-field
  assignment on `cntrlInfo`.
- Factory functions (`aptPkg`, `pipPkg`, etc.) give the `.pcs` author a
  clean, typed API for building input lists.
- Sub-collections are supported: a `sbomsList` entry can name another `.pcs`
  file, allowing recursive capability stacks.

## `_csu.py` — The Commands

Standard CS-Lib (`cs-u` classification). The data singleton
(`cmndsControlInfo` or `pkgsSeedInfo`) is available at runtime because `.pcs`
already populated it before the seed dispatches commands. Commands read from it:

Scalar style — read from `cmndsControlInfo`:
```python
from bisos.capDns import capDns_seedInfo

class capDns_update(cs.Cmnd):
    ...
    def cmnd(self, rtInv, cmndOutcome, ...):
        ci = capDns_seedInfo.cmndsControlInfo
        fqdn = ci.fqdn
        method = ci.dnsSpecMethod
```

List style — read from the data module singleton:
```python
from bisos.sbom import pkgsSeed

class aptPkgs_update(cs.Cmnd):
    ...
    def cmnd(self, rtInv, cmndOutcome, ...):
        for pkg in pkgsSeed.pkgsSeedInfo.aptPkgsList:
            # install pkg.name, call pkg.func if set
```

Follow the `writing-cs-commands` skill for command class shape. Add every
command to `examples_csu()` under a `/For <capability>/` section.

## `_seed.cs` — The Seed Entry Point

The seed csxu wires together the CSU list and handles both the standalone
and planted cases. Key differences from a plain csxu:

1. **Load the planted `.pcs`** if one is active:
   ```python
   from bisos.csSeed import seedsLib
   if seedsLib.seededCsxuInfo.plantOfThisSeed is not None:
       b.importFileAs('plantedCsu', seedsLib.seededCsxuInfo.plantOfThisSeed,
                      __file__, __name__)
   ```

2. **`csuListProc` includes `plantedCsu`** in its elisp list:
   ```
   "bisos.csPlayer.csxuFps_csu"
   "bisos.<pkg>.<pkg>_csu"
   "bisos.csSeed.csCmndsList_csu"
   "plantedCsu"
   ```
   The generated Python removes `plantedCsu` from `csuList` when no plant
   is active.

3. **`g_csMain` uses `ignoreUnknownParams=True`** — planted `.pcs` files
   may pass parameters the seed does not know about.

4. **`examples` command** branches on whether the seed is planted:
   ```python
   if seedsLib.seededCsxuInfo.seedOfThisPlant is None:
       csCmndsList_csu.examples_seed().pyCmnd()
   else:
       csCmndsList_csu.examples_seed().pyCmnd()
       seedsLib.plantedCsuExamplesRun()
   ```

## `.pcs` Files — Planted Command Services

A `.pcs` file is a plain Python script that configures one specific
instance of a seed and declares which commands to run. It lives in
`py3/bin/` alongside the seed's `.cs`.

**Scalar controlInfo style** (`bisos.capDns`):

```python
#!/usr/bin/env python

from bisos.b import cs
import collections
from bisos.csSeed import seedsLib

# 1. Import the seed (triggers atexit registration)
from bisos.capDns import capDns_seed  # noqa: F401  _atExit_

# 2. Populate scalar control info
from bisos.capDns import capDns_seedInfo
cntrlInfo = capDns_seedInfo.cmndsControlInfo

cntrlInfo.dnsSpecMethod = capDns_seedInfo.DnsSpecMethod.etcHosts
cntrlInfo.fqdn = "airflow.here"

# 3. Declare the command list
from bisos.csSeed import csCmndsList_seedInfo
csCmnd = csCmndsList_seedInfo.csCmnd

csCmndsList = [
    csCmnd("capDns_update",  doContinue=True),
    csCmnd("capDns_verify",),
    csCmnd("capDns_resolve",),
    csCmnd("capDns_fqdnPing", args=f"{cntrlInfo.fqdn}", doContinue=True),
]

# 4. Register the list
csCmndsList_seedInfo.setup(csCmndsList=csCmndsList)
```

**Typed lists style** (`bisos.sbom`):

```python
#!/usr/bin/env python

from bisos.sbom import pkgsSeed

# 1. Import the data module (contains atexit registration)
ap = pkgsSeed.aptPkg
pp = pkgsSeed.pipPkg

# 2. Build input lists using factory functions
aptPkgsList  = [ ap("djbdns"), ap("facter"), ap("gh", func=ghAptSource), ]
pipPkgsList  = [ pp("bisos.marmee"), ]
pipxPkgsList = [ pp("bisos.marmee"), ]
sbomsList    = [ pkgsSeed.sbomSpec("exmpl-sbom.pcs"), ]

# 3. Register via setup()  (replaces field-by-field cntrlInfo assignment)
pkgsSeed.setup(
    aptPkgsList=aptPkgsList,
    pipPkgsList=pipPkgsList,
    pipxPkgsList=pipxPkgsList,
    sbomsList=sbomsList,
)

# 4. Optional: examples function
def examples_pcs() -> None:
    cs.examples.menuChapter('*Seed Extensions*')
```

**Combination style** — populate both a `cntrlInfo` singleton *and* call
`setup()` with lists. Useful when the seed needs both a named target and a
variable-length collection to operate on.

**Rules for `.pcs` files:**

- Always import the `_seed` module (step 1) — this is what wires the
  `atexit` hook that links the `.pcs` back to the `.cs` at exit time.
  The `# noqa: F401  _atExit_` comment marks the intentional side-effect import.
- Set **all** required `cntrlInfo` fields **before** declaring `csCmndsList`
  — the list entries may reference `cntrlInfo` values (e.g. `args=f"{cntrlInfo.fqdn}"`).
- `doContinue=True` on a `csCmnd` means the sequence continues even if that
  command fails. Omit it (or set `False`) for commands that must succeed
  before proceeding.
- The `.pcs` filename encodes the target: `<target>-<capability>.pcs`
  (e.g. `airflow-here-dns.pcs`, `exmpl-here-dns.pcs`).
- `.pcs` files are **not** listed in `setup.py` scripts — they are
  invoked directly as Python scripts (`python airflow-here-dns.pcs` or
  `./airflow-here-dns.pcs` after `chmod +x`).

## How the Seed Dispatch Works at Runtime

When `./airflow-here-dns.pcs` runs:

1. Python executes the `.pcs` top-level: imports `capDns_seed` (registers
   atexit), populates `cmndsControlInfo`, declares and registers `csCmndsList`.
2. `csCmndsList_seedInfo.setup()` records the list.
3. The `.pcs` script itself exits normally — the `atexit` hook fires.
4. `seedsLib.plantWithWhich('capDns_seed.cs')` resolves the seed path and
   invokes `capDns_seed.cs` with the `.pcs` file recorded as the active plant.
5. `capDns_seed.cs` starts, sees the plant, imports it as `plantedCsu`,
   and dispatches the `csCmndsList` entries in order.

The key insight: **the `.pcs` file is the driver; the `.cs` is the engine.**
The `.pcs` configures what to do; the `.cs` knows how to do it.

## Creating a New Capability Package

**If each invocation targets a single entity (scalar controlInfo style):**
Copy `bisos.capDns` as a starting point.

1. In `_seedInfo.py`: replace `DnsSpecMethod` with your capability's enum,
   replace `fqdn`/`dnsSpecMethod` fields with your control parameters.
   Rename `CmndsControlInfo` and `CapDnsSeedInfo` to match your package.
2. In `_seed.py`: change `seedCSMU = 'capFoo_seed.cs'`.
3. In `_csu.py`: replace the capDns commands with your capability's commands.
   Each command reads from `capFoo_seedInfo.cmndsControlInfo`.
4. In `_seed.cs`: update all `capDns` → `capFoo` references in imports and
   the elisp `csuList`.
5. Write `.pcs` files for each target (e.g. `myservice-here-foo.pcs`).
6. Add `capFoo_seed.cs` to `setup.py` scripts list.
7. Locally install: `pip install -e py3/` from the repo root.

**If each invocation operates over a collection of items (typed lists style):**
Copy `bisos.sbom` as a starting point.

1. In the data module (`fooSeed.py`): define typed item dataclasses and
   factory functions for your items; define the singleton `FooSeedInfo` with
   list-typed fields; write `setup()` to populate it; add `atexit_plantWithWhich`.
2. In `_csu.py`: write commands that iterate over `fooSeedInfo.<list>`.
3. In `_seed.cs`: update imports and the elisp `csuList`.
4. Write `.pcs` files that call `fooSeed.setup(...)` with built lists.
5. Add `fooSeed.cs` to `setup.py` scripts list and locally install.

**If you need both:** start from whichever style is dominant, then add the
other module alongside it.

## Common Pitfalls

- **Forgetting `# noqa: F401  _atExit_`** on the seed import in a `.pcs` —
  linters will flag the unused import and may strip it, breaking the atexit
  wiring.
- **Setting `cntrlInfo` fields after `csCmndsList`** — if a `csCmnd` entry
  uses `args=f"{cntrlInfo.fqdn}"`, that f-string is evaluated at list
  construction time. Fields must be set first.
- **Calling `setup()` after `csCmndsList`** — same issue for list style:
  `setup()` must be called before any code that reads from the singleton.
- **Listing `.pcs` in `setup.py` scripts** — don't. Only `_seed.cs` goes
  there. `.pcs` files are per-deployment configs, not installed commands.
- **Editing `_csuList` generated content** — the `csuListProc` dblock body
  is generated; edit only the elisp list above it and regenerate in Blee.
- **Confusing list-style and scalar-style** — in list style there is no
  `_seedInfo.py` or `_seed.py`; the data module (`pkgsSeed.py`) handles both
  roles. Don't look for a separate `cmndsControlInfo` singleton in sbom-style
  packages.

## Reference Files

**Primary templates — `bisos.csSeed` (addCmnds seed) and `bisos.gitist`**

`bisos.csSeed` ships minimal reference seeds that are the canonical starting
points. Read these before any domain-specific example:

- Seed `.cs`: `/bisos/git/auth/bxRepos/bisos-pip/csSeed/py3/bin/addCmnds-seed.cs`
- Example `.pcs`: `/bisos/git/auth/bxRepos/bisos-pip/csSeed/py3/bin/exmpl-addCmnds.pcs`
- csCmndsList seed: `/bisos/git/auth/bxRepos/bisos-pip/csSeed/py3/bin/csCmndsList-seed.cs`
- Example csCmndsList `.pcs`: `/bisos/git/auth/bxRepos/bisos-pip/csSeed/py3/bin/exmpl-csCmndsList.pcs`

`bisos.gitist` is a scalar controlInfo seed that operates on Git repositories
across providers (Github, Gitlab). It demonstrates the combination of:
- A rich `CmndsControlInfo` dataclass with enums (`GitProviderBrand`,
  `GitAccessType`, `GitAuthAccessMethod`)
- A separate `cmndsControlInfo` singleton used by all four `.pcs` variants
- Four `.pcs` files encoding provider × access-type in the filename

Key files:
- `_seedInfo.py`: `/bisos/git/auth/bxRepos/bisos-pip/gitist/py3/bisos/gitist/gitist_seedInfo.py`
- `_seed.py`: `/bisos/git/auth/bxRepos/bisos-pip/gitist/py3/bisos/gitist/gitist_seed.py`
- `_csu.py`: `/bisos/git/auth/bxRepos/bisos-pip/gitist/py3/bisos/gitist/gitist_csu.py`
- Seed `.cs`: `/bisos/git/auth/bxRepos/bisos-pip/gitist/py3/bin/gitist-seed.cs`
- `.pcs` (anon github): `/bisos/git/auth/bxRepos/bisos-pip/gitist/py3/bin/pub-anon-github-gitist.pcs`
- `.pcs` (auth github): `/bisos/git/auth/bxRepos/bisos-pip/gitist/py3/bin/pub-auth-github-gitist.pcs`
- `.pcs` (anon gitlab): `/bisos/git/auth/bxRepos/bisos-pip/gitist/py3/bin/pub-anon-gitlab-gitist.pcs`
- `.pcs` (auth gitlab): `/bisos/git/auth/bxRepos/bisos-pip/gitist/py3/bin/pub-auth-gitlab-gitist.pcs`

**Scalar controlInfo style (`bisos.capDns`)**
- `_seedInfo.py`: `/bisos/git/auth/bxRepos/bisos-pip/capDns/py3/bisos/capDns/capDns_seedInfo.py`
- `_seed.py`: `/bisos/git/auth/bxRepos/bisos-pip/capDns/py3/bisos/capDns/capDns_seed.py`
- `_csu.py`: `/bisos/git/auth/bxRepos/bisos-pip/capDns/py3/bisos/capDns/capDns_csu.py`
- `_seed.cs`: `/bisos/git/auth/bxRepos/bisos-pip/capDns/py3/bin/capDns_seed.cs`
- Example `.pcs`: `/bisos/git/auth/bxRepos/bisos-pip/capDns/py3/bin/airflow-here-dns.pcs`
- Example `.pcs`: `/bisos/git/auth/bxRepos/bisos-pip/capDns/py3/bin/exmpl-here-dns.pcs`

**Typed lists style (`bisos.sbom`)**
- Data module: `/bisos/git/auth/bxRepos/bisos-pip/sbom/py3/bisos/sbom/pkgsSeed.py`
- `_csu.py`: `/bisos/git/auth/bxRepos/bisos-pip/sbom/py3/bisos/sbom/sbom_csu.py`
- `_seed.cs`: `/bisos/git/auth/bxRepos/bisos-pip/sbom/py3/bin/seedSbom.cs`
- Minimal `.pcs`: `/bisos/git/auth/bxRepos/bisos-pip/sbom/py3/bin/exmpl-sbom.pcs`
- Featured `.pcs`: `/bisos/git/auth/bxRepos/bisos-pip/sbom/py3/bin/exmpl-featured-sbom.pcs`

**Spread Planted CS style (`bisos.webCap`)**
- `djangoProc.spcs`: `/bisos/git/auth/bxRepos/bisos-pip/webCap/py3/bin/djangoProc.spcs`
- `reactProc.spcs`: `/bisos/git/auth/bxRepos/bisos-pip/webCap/py3/bin/reactProc.spcs`
- seed data module: `/bisos/git/auth/bxRepos/bisos-pip/webCap/py3/bisos/webCap/djangoProc_seedInfo.py`

**Spread Planted CS style (planned — `bisos.dockerProc`)**
- Concept and path-parameter mapping: `/bisos/git/auth/bxRepos/bxObjects/bro_dockerfiles/AI-WorkPlan.org` Stage 5
- Blee panel: `/bisos/git/auth/bxRepos/bisos-pip/csSeed/py3/panels/bisos.csSeed/dotSPCS-SpreadPlantedCS/_nodeBase_/fullUsagePanel-en.org`

**Framework**
- `bisos.csSeed` source: `/bisos/git/auth/bxRepos/bisos-pip/csSeed/`
