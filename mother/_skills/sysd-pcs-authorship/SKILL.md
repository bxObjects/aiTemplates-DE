---
name: sysd-pcs-authorship
description: Use when authoring a `*-sysd.pcs` planted file that installs and manages a systemd service via `bisos.debian`. Covers `systemd_seedInfo.setup()` parameters, `sysdUnitFileFunc`, `preFunc`/`postFunc` hooks, oneshot units, multi-unit ordering with `Requires=`/`After=`, and the CBS assembly pattern.
---

# Authoring a `*-sysd.pcs` File

A `*-sysd.pcs` file is a planted CS file that defines and manages a single
systemd unit. It is the configuration layer in the 3-layer seed/plantation
pattern of `bisos.debian`.

## Reference Implementations

| File | What it shows |
|------|---------------|
| `/bisos/asc/web/bin/airflow-webserver-sysd.pcs` | Standard service with banna port |
| `/bisos/asc/web/bin/airflow-db-sysd.pcs` | `Type=oneshot` + `RemainAfterExit=yes` |
| `/bisos/asc/web/bin/airflow-scheduler-sysd.pcs` | `Requires=`/`After=` unit ordering |

## Minimal Skeleton

```python
#!/usr/bin/env python

from bisos.debian import systemd_seedInfo
from bisos.debian import systemd_seed as systemd_seed  # noqa
from bisos.basics import pathPlus

def sysdUnitFileFunc() -> str | None:
    if (execPath := pathPlus.whichBinPath("myservice")) is None:
        return None
    return f"""
[Unit]
Description=My Service
After=network.target
[Service]
ExecStart={execPath} --flag
Restart=on-failure
RestartSec=10
[Install]
WantedBy=multi-user.target
"""

systemd_seedInfo.setup(
    seedType="sysdSysUnit",
    sysdUnitName="myservice",
    sysdUnitFileFunc=sysdUnitFileFunc,
)
```

## `systemd_seedInfo.setup()` Parameters

| Parameter | Type | Required | Purpose |
|-----------|------|----------|---------|
| `seedType` | `str` | Yes | Unit class selector: `"sysdSysUnit"`, `"sysdUserUnit"` |
| `sysdUnitName` | `str` | Yes | Base unit name — no `.service` suffix (e.g. `"airflow-scheduler"`) |
| `sysdUnitFileFunc` | `Callable` | Yes | Returns the unit file content as a string, or `None` if the binary is absent |
| `examplesHook` | `Callable` | No | Hook for the seed's examples menu |
| `preFunc` | `Callable` | No | Called at Python level *before* enable+start during `SysUnit.ensure()` |
| `postFunc` | `Callable` | No | Called at Python level *after* enable+start during `SysUnit.ensure()` |

## The `sysdUnitFileFunc` Guard

Always guard with `pathPlus.whichBinPath()` and return `None` if the binary
is absent. The framework treats a `None` return as "not yet installable" and
skips writing the unit file gracefully:

```python
from bisos.basics import pathPlus

def sysdUnitFileFunc() -> str | None:
    if (execPath := pathPlus.whichBinPath("airflow")) is None:
        return None
    return f"...[Unit]...ExecStart={execPath}..."
```

Never hardcode the full binary path — always resolve it at call time so the
unit file reflects the actual installation.

## Port Numbers and IP Addresses

Never hardcode ports that `bisos.banna` tracks. Always look them up:

```python
from bisos.banna import tcpPorts as bannaTcpPorts
_portNu = bannaTcpPorts.tcpPortsAssignedList.tcpPortsList['myservice'].portNu
```

For IP addresses that are registered in `/etc/hosts`, resolve at module level:

```python
import socket
_ip = socket.gethostbyname('myservice.here')
```

See the `banna-lookup` skill for the full pattern.

## Pre/Post Hook Semantics

`preFunc` and `postFunc` are **Python-level** callables invoked by
`SysUnit.ensure()` — not by systemd itself. They receive no arguments; the
`.pcs` file closes over whatever context it needs.

```python
def preFunc():
    # create dirs, write config files that ExecStart reads on first launch
    pathlib.Path('/var/lib/myservice').mkdir(exist_ok=True)

def postFunc():
    # verify the service came up, record a flag file, etc.
    pass

systemd_seedInfo.setup(
    ...
    preFunc=preFunc,
    postFunc=postFunc,
)
```

**Intended for**: preparations that `ExecStart` depends on — creating
directories, populating config files, setting permissions.

**Not for**: things systemd should track or that need to survive reboots.
For those, use a dedicated `Type=oneshot` unit instead (see below).

## Oneshot Units (e.g. DB Migration)

For initialisation tasks that should run exactly once and be tracked by
systemd, use `Type=oneshot` + `RemainAfterExit=yes`:

```python
def sysdUnitFileFunc() -> str | None:
    if (execPath := pathPlus.whichBinPath("airflow")) is None:
        return None
    return f"""
[Unit]
Description=Airflow DB Migration
After=network.target
[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart={execPath} db migrate
[Install]
WantedBy=multi-user.target
"""
```

`RemainAfterExit=yes` causes systemd to report the unit as `active` after
`ExecStart` exits successfully — subsequent units that declare
`Requires=` / `After=` this unit will then start correctly.

## Multi-Unit Ordering with `Requires=` / `After=`

When a service depends on another unit completing first (e.g. DB migration
before the scheduler starts), declare it in the `[Unit]` section:

```python
return f"""
[Unit]
Description=Airflow Scheduler
After=network.target airflow-db.service
Requires=airflow-db.service
[Service]
ExecStart={execPath} scheduler
Restart=on-failure
RestartSec=10
[Install]
WantedBy=multi-user.target
"""
```

- `Requires=` — if the listed unit fails or is stopped, this unit stops too
- `After=` — this unit starts only after the listed units have started
- Both are needed together: `Requires=` alone does not enforce ordering

## CBS Assembly (`*-cbs.pcs`)

A CBS (Capability Bundle Specification) orchestrates multiple sysd units.
Declare them in dependency order — the oneshot/migration unit first:

```python
from bisos.capability import cba_sysd_seed
from bisos.capability import cba_seed

cba_seed.setup(
    seedType="systemd",
    loader=None,
    sbom="myservice-sbom.pcs",
    assemble=None,
    materialize=None,
)

sysdUnitsList = [
    cba_sysd_seed.sysdUnit("myservice-db",        "myservice-db-sysd.pcs"),
    cba_sysd_seed.sysdUnit("myservice-webserver",  "myservice-webserver-sysd.pcs"),
    cba_sysd_seed.sysdUnit("myservice-scheduler",  "myservice-scheduler-sysd.pcs"),
]

cba_sysd_seed.setup(
    sysdUnitsList=sysdUnitsList,
)
```

List order matters — the CBS `ensure` command processes units in order.
Put the oneshot/DB unit first so it completes before dependent services start.

## Pre/Post Hook vs. Oneshot Unit — Decision Table

| Criterion | `preFunc` hook | Dedicated oneshot unit |
|-----------|---------------|----------------------|
| Recorded by systemd | No | Yes (journal + `RemainAfterExit`) |
| Survives reboots | No (runs only at `ensure` time) | Yes (systemd tracks completion) |
| Ordering with other units | Not visible to systemd | Declared via `Requires=`/`After=` |
| Use case | ExecStart preparations | DB migration, initialisation |

## Common Mistakes

- **Hardcoding the binary path**: use `pathPlus.whichBinPath()` — the path
  varies by venv and installation method.
- **Hardcoding port numbers**: use `bisos.banna` — ports are assigned and
  may be shared across units.
- **Missing `After=` on a dependent unit**: `Requires=` alone does not
  enforce start ordering; both `Requires=` and `After=` are needed.
- **Using `preFunc` for things systemd should track**: if a preparation
  needs to be recorded, ordered, or retriable across reboots, it belongs
  in a dedicated oneshot unit, not a Python hook.
- **`sysdUnitName` with `.service` suffix**: pass only the base name
  (e.g. `"airflow-scheduler"`, not `"airflow-scheduler.service"`).
