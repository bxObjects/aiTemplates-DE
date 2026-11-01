---
name: configfile-pattern
description: Use when wiring a seed package to manage a config file using `bisos.debian.configFile.ConfigFile`. Covers subclassing ConfigFile in the `_csu.py`, exposing the singleton in the seed, adding the required csuList entries (`configFile` + `clsMethod_csu`), and using `configFileStdout`/`configFileUpdate` with `--cls` in `.pcs` files.
---

# The `configFile` Pattern for Seed Packages

The `configFile.ConfigFile` facility (from `bisos.debian`) provides a standard
set of CS commands for managing a config file: `configFileStdout`, `configFilePath`,
`configFileUpdate`, `configFileCat`, `configFileVerify`, `configFileDelete`.

Rather than writing bespoke file-writing logic in a `_csu.py`, subclass
`ConfigFile` and get all of these commands for free.

## Reference Implementation

`bisos.webCap.capWebVd` is the reference. Compare with `bisos.debian.bifSystemd_csu`
which uses the same pattern for systemd unit files.

## Step 1 — Subclass `ConfigFile` in `_csu.py`

In your `<pkg>_csu.py`, import and subclass `configFile.ConfigFile`:

```python
from bisos.debian import configFile
from bisos.basics import pyRunAs
from bisos.<pkg> import <pkg>_seedInfo

class ConfigFile_<name>(configFile.ConfigFile):

    @cs.track(fnLoc=True, fnEntry=True, fnExit=True)
    def configFilePath(self) -> pathlib.Path:
        ci = <pkg>_seedInfo.cmndsControlInfo
        return pathlib.Path(f'/path/to/{ci.someField}')

    @cs.track(fnLoc=True, fnEntry=True, fnExit=True)
    def configFileStr(self) -> str | None:
        ci = <pkg>_seedInfo.cmndsControlInfo
        if ci.configFunc is None:
            print(f"EH_problem Missing configFunc")
            return None
        return ci.configFunc()

    @cs.track(fnLoc=True, fnEntry=True, fnExit=True)
    def configFileUpdate(self):
        contentStr = self.configFileStr()
        destPath = self.configFilePath()
        pyRunAs.as_root_writeToFile(destPath, contentStr)


configFile_<name> = ConfigFile_<name>()
```

The singleton `configFile_<name>` must be instantiated at module level — it is
looked up by name via `getattr(__main__, cls)` when `--cls=configFile_<name>`
is passed on the command line.

## Step 2 — Expose the singleton in the seed

In the seed `.cs` file, after the `csuList` block, assign the singleton into
the seed's module namespace so it becomes visible as a `__main__` attribute:

```python
configFile_<name> = <pkg>_csu.configFile_<name>
```

This line is what makes `--cls=configFile_<name>` work at runtime. Without it,
`getattr(__main__, 'configFile_<name>')` raises `AttributeError`.

## Step 3 — Add two entries to `csuList` in the seed

Both `bisos.debian.configFile` and `bisos.b.clsMethod_csu` must be in the
seed's `csuList`:

```python
from bisos.debian import configFile
from bisos.b import clsMethod_csu

csuList = [
    'bisos.csPlayer.csxuFps_csu',
    'bisos.<pkg>.<pkg>_csu',
    'bisos.debian.configFile',      # provides configFileStdout, configFileUpdate, etc.
    'bisos.b.clsMethod_csu',        # provides --cls argparse declaration
    'bisos.csSeed.csCmndsList_csu',
    'plantedCsu',
]
```

**Why both?**

- `bisos.debian.configFile` — contributes the `configFileStdout`, `configFileUpdate`,
  `configFileCat`, `configFileVerify`, `configFileDelete`, `configFilePath` command
  classes to the seed's command dispatch.
- `bisos.b.clsMethod_csu` — its `commonParamsSpecify` registers `--cls` with
  argparse. Without this, passing `--cls=configFile_<name>` on the command line
  produces `BadUsage: Missing parameter definition: cls`. This is the non-obvious
  part — `configFile.commonParamsSpecify` only registers `--runAs`, not `--cls`.

## Step 4 — Use `configFileStdout` / `configFileUpdate` in `.pcs`

In the `.pcs` file's `csCmndsList`, replace any bespoke update command with:

```python
csCmnd("configFileStdout", pars={'cls': 'configFile_<name>'},),
csCmnd("configFileUpdate", pars={'cls': 'configFile_<name>', 'runAs': 'root'},),
```

`configFileStdout` prints what would be written (preview without side effects).
`configFileUpdate` writes it to disk (as root via `pyRunAs.as_root_writeToFile`).

## The Full Command Set Available

Once wired up, all of these work via `--cls=configFile_<name>`:

| Command            | What it does                                              |
|--------------------|-----------------------------------------------------------|
| `configFileStdout` | Print config string to stdout (preview)                   |
| `configFilePath`   | Print the destination file path                           |
| `configFileUpdate` | Write config string to destination file                   |
| `configFileCat`    | Cat the current file on disk                              |
| `configFileVerify` | Check that file on disk matches what `configFileStr` returns |
| `configFileDelete` | Delete the config file                                    |

## Common Mistakes

- **Forgetting `clsMethod_csu` in `csuList`**: causes `BadUsage: Missing parameter
  definition: cls` even though `--cls` appears to be used correctly everywhere else.
- **Not assigning the singleton in the seed**: causes `AttributeError: module
  'bisos.<pkg>.<pkg>_csu' has no attribute 'configFile_<name>'` at atexit time.
- **Stale non-editable copy in site-packages**: if a `bisos/<pkg>/` directory
  exists directly under `site-packages/`, it shadows the editable source tree
  even when the package is installed editable. Remove it:
  `rm -rf /bisos/venv/py3/bisos3/lib/python3.11/site-packages/bisos/<pkg>/`