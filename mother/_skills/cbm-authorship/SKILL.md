---
name: cbm-authorship
description: Use when authoring or modifying CBM (Capability Bundle Materialization) leaves — `cbmProc.spcs` planted files, `cbmProc-seed.cs`, the `cbm_*` Cmnd classes, or the `cbmProc.control`/`cbmProc.status` gate files. Covers the two-tier CBM/CBS layering (CBM sits on top of CBS via subprocess; it does NOT duplicate CBS content), the `cbmProc.spcs`-as-pointer pattern (`capabilityName` + `cbsSpec`), the service/usage sbom split (`<name>-sbom.pcs` + `<name>Usage-sbom.pcs`, joined only by the CBS through a `<name>Cbs-sbom.pcs` bundle), the two `cbm_*` verb families (control/status + materialize-subprocess), gate-as-Cmnd-body rationale, `cbsSpec` resolution (absolute path OR basename-via-PATH), and the non-invasive rule (never edit `cba_csu.py`, `cba_seed.py`, `cba_sysd_seed.py`, `cba_sysd_csu.py`). Load `spread-seeded-cs-commands` first for the underlying `.spcs` mechanism, and `walkable-tree-planting` if the CBM leaves will be walked from a branch.
---

# CBM (Capability Bundle Materialization) Authorship

BISOS ships **capabilities as bundles** — a systemd service + its sbom + its
DNS entry + its nginx vhost, all declared once and materialized in one shot
on a target host. The abstractions form a three-way triad:

| Term | Meaning | Concrete artifact |
|---|---|---|
| **CBA** | Capability Bundle *Abstraction* | The `bisos.capability` framework (`cba_seed.py`, `cba_sysd_seed.py`, `cba_csu.py`) |
| **CBS** | Capability Bundle *Specification* | A standalone executable `.pcs` file that declares one capability's contents. E.g. `/bisos/asc/web/bin/airflow-cbs.pcs`. |
| **CBM** | Capability Bundle *Materialization* | A `cbmProc.spcs` planted at a leaf in the CBM tree, gated by a `cbmProc.control` file. **Points to** a CBS, does not duplicate it. |

**The load-bearing principle:** *CBM sits on top of CBS. It does not
duplicate CBS content.* `cbmProc.spcs` is a **pointer** to a CBS executable,
plus a per-leaf gate. When the user runs `cbm_materialize` at the leaf,
CBM subprocess-invokes the CBS with `-i cbs_materialize`.

Getting this layering wrong (inlining CBS content into `cbmProc.spcs`) is
the primary mistake to avoid. Two CBSs for one capability is one too many.

**Creating a whole package** (repo, banna registrations, `<name>Info.py`, sboms, units,
vhost, CBS, admin CS, docs) for an open-source program is the `cbm-package-authorship`
skill; this one covers the CBM leaf and the sbom split it relies on.

The layering (raw platform, generic packages as the base, `.here` regression runs, niching and
CapabilityBPOs later) and the catalog of planted and planned leaves with their gates are in
`/bisos/git/bxRepos/bxGenesis/start/rawBisosCBMs/README.org`.
When you plant a leaf or change its gate, update that README's tables and the hereWeb
`branchesOrdered` list.

## The `cbmProc.spcs` file shape

A CBM leaf is a directory with three files:

```
sys/cbm/<realm>/<capabilityType>/<capabilityName>/
├── cbmProc.spcs        # THE pointer + atexit hook (executable)
├── cbmProc.control     # gate state: available | enabled | disabled
└── cbmProc.status      # append-only outcome log (machine-written)
```

The `cbmProc.spcs` body is intentionally short. Airflow as canonical
example:

```python
#!/usr/bin/env python

# atexit hook: register cbmProc-seed.cs as this file's seed
from bisos.capability import cbmProc_seed  # noqa: F401  _atExit_

# declare capability + point to CBS
from bisos.capability import cbmProc_seedInfo
cbmProc_seedInfo.setup(
    capabilityName="airflow",
    cbsSpec="airflow-cbs.pcs",   # basename form (PATH-resolved)
    # cbsSpec="/bisos/asc/web/bin/airflow-cbs.pcs",  # absolute-lock alternative
)
```

**Do NOT** include `cba_seed.setup(...)`, `cba_sysd_seed.setup(...)`,
`sysdUnitsList=[...]`, or any other CBS content in the `cbmProc.spcs`.
Those live in the CBS file (`airflow-cbs.pcs`) which stays put.

## Service and usage sboms: two per capability, joined by the CBS

A capability package that runs a service (a CBS with sysd units) usually has
two sides: running the service, and using it. Keep them in two sboms:

| sbom | Holds | Example (bisos.kafka) |
|---|---|---|
| `<name>-sbom.pcs` | The service: runtime, binaries, account, config, data init | `kafka-sbom.pcs` (JRE, Kafka, Kafbat UI, storage format) |
| `<name>Usage-sbom.pcs` | What a host needs to *use* the service, local or remote: client libraries, build deps, auth tooling | `kafkaUsage-sbom.pcs` (librdkafka built with Kerberos) |

Rules:

- **The service sbom does NOT pull in the usage sbom** (no `sbomsList` entry
  for it). Materializing only the server is a normal, supported case, and a
  host that only uses a remote service runs only the usage sbom.
- **The CBS is what does both.** It materializes the capability as a whole.
- **Name the usage side "Usage", not "Client".** "Client" is fine where the
  scope is wider than one service (e.g. `bisos.postgres`'s
  `dbClients-sbom.pcs` covers SQL clients generally); for one service's own
  usage side, use `<name>Usage-sbom.pcs`.
- Python client packages still go into each consumer's own virtenv, not into
  the usage sbom; the usage sbom supplies what they build or run against.

**How the CBS names both today.** `cba_seed.setup(sbom=...)` takes *one*
string, and `cbs_sbom` runs it as `{sbom} -i sbom_fullUpdate`. So add a third,
package-less bundle sbom, `<name>Cbs-sbom.pcs`, whose `sbomsList` names the
service sbom then the usage sbom, and point the CBS at it:

```python
# kafkaCbs-sbom.pcs
_binDir = pathlib.Path(__file__).resolve().parent
pkgsSeed.setup(sbomsList=[
    pkgsSeed.sbomSpec(str(_binDir / "kafka-sbom.pcs")),
    pkgsSeed.sbomSpec(str(_binDir / "kafkaUsage-sbom.pcs")),
])

# kafka-cbs.pcs
cba_seed.setup(seedType="systemd", sbom="kafkaCbs-sbom.pcs", assemble="kafka-assemble.cs", ...)
```

Do NOT pack two commands into the `sbom=` string (`"a-sbom.pcs -i
sbom_fullUpdate && b-sbom.pcs"`): it works only because the string is pasted
into bash. Making `cba_seed.sbom` accept a list is the real fix; it is a
framework change (see the non-invasive rule below) and is recorded in
`AI-Outputs.org` (`:REPO:` capability). When it lands, retire the bundle sbom.

Caveat: `sbomSpecs_fullUpdate` in `bisos.sbom` reports a failed sub-sbom and
carries on, and `g_csMain` exits 0 regardless (see below), so a failure in the
service sbom does not stop the usage sbom or the CBS's later steps. Read the
output.

## `cbsSpec` resolution

`resolveCbsSpec()` in `cbmProc_seedInfo.py` applies one clear rule (no magic):

- **Contains `/` or starts with `~`** → treat as explicit path. Expand `~`,
  `.resolve()` for symlinks, require the file to exist. Use this to **lock**
  a specific location.
- **Bare basename** → `shutil.which()` against `$PATH`. Use this when the
  CBS is expected to be on PATH via deployment.

Both are supported deliberately. Basename is the default for portability;
absolute is available for pinning.

Unresolvable specs raise `ValueError` with an actionable message and
write a `failed: ... cbsSpec-unresolvable: ...` line to `cbmProc.status`.
Do NOT catch and hide these errors.

## Two `cbm_*` verb families

The `cbmProc.spcs` leaf's **public interface** is `cbm_*` only. The
`cbs_*` verbs from `cba_csu.py` remain reachable at the leaf's csuList
for anyone who really wants ungated raw access, but the leaf advertises
only `cbm_*` in its examples and `walkExamples()`.

### Family 1: Control / Status (gate manipulation — never gated themselves)

| Cmnd | Purpose |
|---|---|
| `cbm_control` | Read (0-arg) or write (1-arg: `available`/`enabled`/`disabled`) the `cbmProc.control` file |
| `cbm_status` | Print current `cbmProc.status` contents |
| `cbm_isEnabled` | Predicate; `opResults` = `True` iff enabled |
| `cbm_enable` / `cbm_disable` / `cbm_available` | Write state (convenience wrappers over `cbm_control`) |

`cbm_disable` is **passive** — the walker will skip this leaf, but no
teardown fires. To actually un-materialize a previously-materialized
capability, run `cbm_unMaterialize` explicitly.

### Family 2: Materialize (subprocess-dispatch to CBS — gated)

| Cmnd | Subprocess-invokes |
|---|---|
| `cbm_materialize` | `cbsSpec -i cbs_materialize` |
| `cbm_reMaterialize` | `cbsSpec -i cbs_reMaterialize` |
| `cbm_unMaterialize` | `cbsSpec -i cbs_unMaterialize` |
| `cbm_sbom` | `cbsSpec -i cbs_sbom` |

Every verb in this family goes through `_dispatchCbs()` in `cbmProc_csu.py`:

```
1. controlRead(plantDir); if not Enabled → statusWrite skip; return
2. resolveCbsSpec(); on failure → statusWrite failure; return bad outcome
3. subprocess.run([cbsExec, '-i', verb], check=False)
4. statusWrite "ran: <verb> ok" or "ran: <verb> failed rc=<n>"
```

Initial state after planting: `cbmProc.control = available`. First
`cbm_materialize` is a no-op skip until someone runs `cbm_enable`.
That's safety by design — no capability materializes just because its
leaf got planted.

## Gate design: as Cmnd body, NOT as `__main__` interceptor

The gate check lives **inside each Family-2 Cmnd's body**, via
`controlRead(plantDir)`. Not in `if __name__ == '__main__':` before
`g_csMain`.

Reason: doing gate-in-`__main__` requires `sys.exit(0)` on skip, which
produces a `SystemExit: 0` traceback in the terminal (BISOS treats bare
`sys.exit` inside `.spcs` invocation paths as an exception path). Ugly.

Doing gate-in-Cmnd-body:
- Uses `cmndOutcome.set(opError=Success, opResults="skipped: ...")` to return normally
- Never touches `sys.exit`
- Family-1 verbs (`cbm_enable` etc.) bypass the gate naturally — they don't call `_dispatchCbs()`

If a fresh Claude reviews `cbmProc-seed.cs`, they'll see NO gate logic there.
`_applyControlGate()` deliberately does not exist. That's correct.

## Non-invasive rule (LOAD-BEARING)

`bisos.capability` ships with existing files that are used by other systems.
Do **not** edit them when adding CBM machinery:

| File | Why it must stay untouched |
|---|---|
| `cba_csu.py` | Provides `cbs_load`, `cbs_sbom`, `cbs_assemble`, `cbs_materialize`, `cbs_reMaterialize`, `cbs_unMaterialize`, `cbs_deMaterialize`, `cbs_type`, `cbs_isMaterialized`, `cbmSymlinkToThisCbs`. Used by existing CBS files like `airflow-cbs.pcs`. |
| `cba_seed.py` | `CbaSeedInfo` singleton + `setup()` used by every CBS file. |
| `cba_sysd_seed.py` | `SysdUnit`, `SysdSeedInfo`, `sysdUnit()` factory, `setup(sysdUnitsList=...)`, `plantWithWhich("cba-sysd.cs")`. Used by every systemd CBS. |
| `cba_sysd_csu.py` | Existing `sysdUnitsProc` Cmnd. |
| `cbm_csu.py` | Existing `cbmBase`, `processCbs` Cmnds. |

The CBM layer is additive: it adds `cbmProc_seedInfo.py`, `cbmProc_seed.py`,
`cbmProc_csu.py`, `cbmProc-seed.cs`, and does its work by *composition* in
`cbmProc-seed.cs`'s csuList — not by modification.

## Known gotcha: `cba_sysd_seed.plantWithWhich("cba-sysd.cs")`

`cba_sysd_seed.plantWithWhich()` is hardcoded (line ~261) to accept only
`"cba-sysd.cs"` as its argument — any other value silently returns
without planting. If a naive `cbmProc.spcs` calls
`cba_sysd_seed.plantWithWhich("cbmProc-seed.cs")`, it will do nothing and
the seed binding fails silently.

**Workaround:** don't use it. `cbmProc.spcs` uses `cbmProc_seed`'s own
atexit registrar (imported via `from bisos.capability import cbmProc_seed`)
which binds the .spcs to `cbmProc-seed.cs`. This is one reason CBM has
its own tiny `cbmProc_seed.py` module.

Modernizing `cba_sysd_seed.plantWithWhich()` to accept any seed name is a
future task; the workaround costs nothing in the meantime.

## Known limitation: `g_csMain` exit-code propagation

`bisos.b.cs.main.g_csMain` currently exits 0 even when a Cmnd raises or
sets `opError=Failure`. This means `_dispatchCbs()` can see subprocess
`rc=0` for a `cbsSpec -i cbs_materialize` that internally failed
(because the CBS's own Cmnd returned failure but g_csMain still exited 0).

Result: `cbmProc.status` may report `ran: cbs_materialize ok` when the
underlying materialization actually failed. Same limitation flagged in
`bisos.fileObj` Stage 2 #C TODO. Do NOT try to work around it locally
in `cbmProc_csu.py`; the fix belongs in `bisos.b` and applies to every
downstream consumer.

For now: users who need to know if materialization actually succeeded
should inspect the CBS's own output (e.g. by capturing stderr from the
subprocess), not trust the top-line `cbmProc.status` line.

## `cbmProc.control` and `cbmProc.status` file formats

**Plain text, NOT JSON** (per explicit design decision — revisit if state
outgrows single-word semantics).

- `cbmProc.control` — one word on one line: `available` / `enabled` / `disabled`.
  Absent file → treated as `available` (safe default). Unknown value → also
  treated as `available` (safe fallback, no raise; callers may be about to
  fix it via `cbm_control <value>`).
- `cbmProc.status` — append-only log, ISO-timestamp + one-line message per
  event:
  ```
  2026-08-15T17:47:50  skipped: control=available at cbs_materialize
  2026-08-15T17:47:51  failed: cbs_materialize cbsSpec-unresolvable: ...
  2026-08-15T17:48:05  ran: cbs_materialize ok
  ```

If either format needs to become richer (per-aspect fields, structured
schemas), the change is scoped to `controlRead/Write` + `statusRead/Write`
in `cbmProc_seedInfo.py`. Callers deal in `ControlState` enum values, not
raw strings.

## The canonical exemplar

Airflow at:
```
/bisos/git/auth/bxRepos/bxObjects/bro_rawBisos/bro_rawBisosPlatform/sys/cbm/collective/hereWeb/airflow/
```

Contents:
- `cbmProc.spcs` — pointer to `airflow-cbs.pcs` (either basename or absolute)
- `cbmProc.control` — initial `available`
- `cbmProc.status` — populated by test runs

Walked from the parent by:
```
/bisos/git/auth/bxRepos/bxObjects/bro_rawBisos/bro_rawBisosPlatform/sys/cbm/collective/ftoBranchProc.spcs
```

Which imports `bisos.capability.cbmProc_seedInfo.leafProcessorNames()` and
`walkExamples()` to wire `bisos.fileObj`'s walker to detect CBM leaves
and render `cbm_*` walk examples.

Verify suite (54 assertions covering singleton, cmnd presence, control/status
roundtrips, paramsFromPlantPath, walkExamples coverage, and cbsSpec
resolution across absolute/slash/basename forms):
```
/bisos/git/auth/bxRepos/bisos-pip/capability/py3/tests/verify.sh
```

## When authoring a NEW CBM leaf

Steps (in order):

1. **Create the CBS first, if it doesn't exist.** A `-cbs.pcs` file that
   uses `cba_seed.setup()` + (typically) `cba_sysd_seed.setup(sysdUnitsList=...)`
   + `cba_sysd_seed.plantWithWhich("cba-sysd.cs")`. Standalone executable,
   invocable as `./foo-cbs.pcs -i cbs_materialize`. Put it wherever your
   convention dictates: the `py3/bin/` of the bisos-pip package that provides the capability
   (`bisos.webCap` for nginx, reactPlus, django, gunicorn; moved there from `/bisos/asc/web/bin/`
   on 2026-10-18).
2. **Choose realm + capabilityType** for the CBM leaf:
   `sys/cbm/<realm>/<capabilityType>/<capabilityName>/`. Realms today:
   `platform`, `site`, `pals`, `user`, `collective`. Capability types today:
   `hereWeb` (HTTP via `.here`), `hereMail` (mail via `.here`), `rpyc` (PyCS
   performer), `induct` (non-service install).
3. **Write the leaf's `cbmProc.spcs`** — the ~10-line pointer. Set
   `capabilityName` and `cbsSpec`. `chmod +x` it.
4. **Create `cbmProc.control`** with contents `available` (initial safe state).
5. **Create empty `cbmProc.status`**.
6. **Test:**
   - `./cbmProc.spcs` → bare menu (verifies seed loads)
   - `./cbmProc.spcs -i cbm_control` → prints `available`
   - `./cbmProc.spcs -i cbm_materialize` → should skip + audit to `.status`
   - `./cbmProc.spcs -i cbm_enable` → flips to `enabled`
   - `./cbmProc.spcs -i cbm_materialize` → subprocess-invokes CBS
7. **If the leaf will be walked**, ensure a `ftoBranchProc.spcs` exists at
   an ancestor directory. See `walkable-tree-planting` skill.

## What NOT to do

- Do NOT include `cba_seed.setup(...)` or `cba_sysd_seed.setup(...)` in a
  `cbmProc.spcs`. CBS content lives in the CBS file, not the CBM leaf.
- Do NOT edit `cba_csu.py`, `cba_seed.py`, `cba_sysd_seed.py`,
  `cba_sysd_csu.py`, or `cbm_csu.py`. These ship as-is; CBM composes them,
  not modifies them.
- Do NOT add gate logic to `cbmProc-seed.cs`. Gate lives in Cmnd bodies.
  If you see `_applyControlGate()` or `sys.exit(0)` there, that's a
  regression to the earlier (rejected) design.
- Do NOT use JSON for `cbmProc.control` or `cbmProc.status`. Plain text.
- Do NOT catch `ValueError` from `resolveCbsSpec()` and hide it. That
  error is how a user learns their PATH is wrong or their CBS moved.

## References

- Framework source: `/bisos/git/auth/bxRepos/bisos-pip/capability/`
- CBM files (four, all added additively): `cbmProc_seedInfo.py`,
  `cbmProc_seed.py`, `cbmProc_csu.py`, `cbmProc-seed.cs`
- Airflow exemplar:
  `/bisos/git/auth/bxRepos/bxObjects/bro_rawBisos/bro_rawBisosPlatform/sys/cbm/collective/hereWeb/airflow/`
- Legacy CBS (unchanged; do not modernize casually):
  `/bisos/asc/web/bin/airflow-cbs.pcs`
- Verify suite: `bisos.capability/py3/tests/verify.sh`
- Related skills: `spread-seeded-cs-commands` (underlying `.spcs` mechanism),
  `walkable-tree-planting` (walking CBM leaves from a branch),
  `seeded-cs-commands` (the `.pcs` mechanism CBS files use)
- Platform README explaining realms + capability types:
  `/bisos/git/auth/bxRepos/bxObjects/bro_rawBisos/bro_rawBisosPlatform/README.org`
