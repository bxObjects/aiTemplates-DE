---
name: sbom-authoring
description: Use when creating or modifying a BISOS -sbom.pcs file — deciding between apt, pip, pipx, or custom-source installation, setting the target venv, declaring sbom dependencies, and authoring the readme command and examples_csu function.
---

# Authoring BISOS `-sbom.pcs` Files

A `-sbom.pcs` file is a PyCS planted command service that installs software
(Debian packages, pip packages, pipx packages) and runs post-install steps.
The `pkgsSeed` module provides the API. Existing examples live at:
- `/bisos/core/bsip/bin/*-sbom.pcs`
- `/bisos/git/bxRepos/bisos-pip/webCap/py3/bin/*-sbom.pcs` (nginx, reactPlus, django, gunicorn,
  the `webCap-sboms.pcs` bundle; moved from `/bisos/asc/web/bin/` on 2026-10-18)
- `/bisos/git/bxRepos/bisos-pip/*/py3/bin/*-sbom.pcs` (the CBM packages)

**Scope — Debian/apt only.** `pkgsSeed` supports `apt`, `pip`, and `pipx`
only; there is **no `dnf`/`rpm` support**. For RHEL/dnf hosts, package lists
must be handled manually (or captured as reference data) until `bisos.sbom`
grows dnf support.

## File Structure

```python
#!/usr/bin/env python

""" #+begin_org
* Panel::  [[file:/bisos/panels/bisos-apps/NameOfThePanelComeHere/_nodeBase_/fullUsagePanel-en.org]]
* Overview and Relevant Pointers
#+end_org """

from bisos import b
from bisos.b import cs
from bisos.b import b_io

from bisos.sbom import pkgsSeed  # pkgsSeed.plantWithWhich("seedSbom.cs")
ap = pkgsSeed.aptPkg
pp = pkgsSeed.pipPkg
sbom = pkgsSeed.sbomSpec

# Set target venv for all pp() entries (omit if using system pip):
pkgsSeed.pkgsSeedInfo.virtenv = "/bisos/venv/py3/asc"

# Prerequisite sboms (run before this sbom's own installs):
sbomsList = [
    sbom("/absolute/path/to/other-sbom.pcs"),
]

aptPkgsList = [
    ap("some-deb-pkg"),
]

pipPkgsList = [
    pp("some-pip-pkg"),
    pp("pinned-pkg", ver=">=1.2.0"),
]

pkgsSeed.setup(
    aptPkgsList=aptPkgsList,
    pipPkgsList=pipPkgsList,
    sbomsList=sbomsList,
)
```

Followed by a `readme` command class and `examples_csu()` function (see below).

## Decision Tree: Which Installer?

| Situation | Use |
|---|---|
| Standard Debian package | `ap("pkg-name")` |
| Standard apt package needing a custom apt source first | `ap("pkg-name", func=myAptSourceFn)` |
| Python package — importable as library AND CLI | `pp("pkg-name")` with `pkgsSeed.pkgsSeedInfo.virtenv` set |
| Python package — CLI only, isolated | `pipxPkg("pkg-name")` (pipx) |
| Post-install step after a pip install (e.g. `playwright install`) | `pp("stepName", func=myPostInstallFn)` |
| Host/user config step after install (write `~/.config`, drop files) | named `func=` pseudo-entry: `ap("stepName", func=fn)` |
| Step needing root (write `/etc`, `systemctl`, `loginctl`) | `func=` pseudo-entry running a `sudo -s` block (see Root / sudo Steps) |
| This sbom depends on another sbom being run first | `sbom("/absolute/path/to/other-sbom.pcs")` |

**Key rule:** use `func=` only when custom shell logic is required (adding an apt
source, running a post-install binary). Never use `func=` for a plain pip or apt
install — `pp()` and `ap()` handle those directly.

## Setting the Target Venv

```python
pkgsSeed.pkgsSeedInfo.virtenv = "/bisos/venv/py3/asc"
```

Set this when pip packages must be installed into a specific venv rather than
the system default. All `pp()` entries in the file share this setting.
The standard BISOS asc venv is `/bisos/venv/py3/asc`.

**Important:** if this sbom is declared as a prerequisite by another sbom that
sets a `virtenv`, this sbom must set the same `virtenv` — otherwise the pip
packages end up in different venvs and imports will fail.

## The `func=` Pattern

### Execution contract

- **No arguments.** A func is defined `def myFn():` — it takes no parameters.
- **Body is shell, not Python.** Do the work through
  `b.subProc.WOpW(invedBy=None, log=1).bash(f"""...""")`. Do **not** use
  pure-Python file/dir manipulation (`os.makedirs`, `open().write()`) — keep to
  shell so behavior and logging match the rest of BISOS.
- **The func owns its work.** When `func=` is set, the framework runs the func
  *instead of* a plain install of that entry's name. So the name is either a
  **real package** whose func installs it via a custom source (e.g.
  `ap("gh", func=ghAptSource)` where the func runs `apt install gh`), or an
  arbitrary **pseudo-entry** label for a step that installs nothing (e.g.
  `pp("playwrightInstall", ...)`, `ap("myConfigStep", ...)`). A pseudo-entry
  name is never apt/pip-installed — this is why the shipped examples with
  non-package names work.
- **Idempotent.** Funcs re-run on every `sbom_fullUpdate`; guard writes
  (`[ ! -f ... ]`, `mkdir -p`, never clobber existing user config).

### Custom apt source (func installs a real package)

```python
def myToolAptSource():
    outcome = b.subProc.WOpW(invedBy=None, log=1).bash(f"""
sudo install -d -m 0755 /etc/apt/keyrings \
    && sudo curl -fsSL https://example.com/key.asc \
         -o /etc/apt/keyrings/mytool.asc \
    && echo "deb [signed-by=/etc/apt/keyrings/mytool.asc] https://example.com/apt stable main" \
         | sudo tee /etc/apt/sources.list.d/mytool.list \
    && sudo apt update \
    && sudo apt install -y mytool
""")

aptPkgsList = [
    ap("mytool", func=myToolAptSource),
]
```

### pip post-install step (pseudo-entry)

```python
def playwrightInstall():
    outcome = b.subProc.WOpW(invedBy=None, log=1).bash(f"""
playwright install
""")

pipPkgsList = [
    pp("playwright", ver=">=1.40.0"),
    pp("playwrightInstall", func=playwrightInstall),
]
```

### Host/user config step (pseudo-entry, no sudo)

Write user config after install. Idempotent, and parameterize host-specific
values (see Parameters below):

```python
import os
MY_STORE = ""   # parameter; env override below; empty => skip

def myUserConfig():
    store = os.environ.get("MY_STORE", MY_STORE)
    b.subProc.WOpW(invedBy=None, log=1).bash(f"""
mkdir -p ~/.config/mytool
if [ -n "{store}" ] && [ ! -f ~/.config/mytool/conf ]; then
  echo 'store = "{store}"' > ~/.config/mytool/conf
fi
""")

aptPkgsList = [
    ap("mytool"),                              # real package, plain install
    ap("myUserConfig", func=myUserConfig),     # pseudo-entry, post-install config
]
```

### Root / sudo steps

For steps needing root (writing `/etc`, `systemctl`, `loginctl`), run the
privileged commands in a **single `sudo -s` shell**. Caveats:

- **Non-interactive risk.** Funcs may run without a TTY, so a `sudo` password
  prompt can **hang or fail**. Either the host grants `NOPASSWD` for these
  commands, or the sbom must be run interactively. Document which.
- **Capture the invoking user before the sudo shell** — inside `sudo` you are
  root, so grab `id -un` first if a step (e.g. `loginctl enable-linger`) needs
  the real user.
- **Deferred effects.** Some changes (e.g. a `user@.service` drop-in) apply
  only after `systemctl daemon-reload` **and a re-login** — say so in output.

```python
def myRootStep():
    b.subProc.WOpW(invedBy=None, log=1).bash(f"""
targetUser="$(id -un)"
sudo -s <<EOF
mkdir -p /etc/systemd/system/user@.service.d
cat > /etc/systemd/system/user@.service.d/delegate.conf <<'CONF'
[Service]
Delegate=cpu cpuset io memory pids
CONF
systemctl daemon-reload
loginctl enable-linger "$targetUser"
EOF
""")
```

(Note the nested heredocs: quote the inner `'CONF'` so its body is literal;
leave the outer `EOF` unquoted only if you need a var like `$targetUser` to
expand from the calling shell.)

### Parameters

For host-specific values (a path, a store location), use an **environment
variable with a module-level default**, and **skip cleanly when unset** rather
than hardcoding a wrong value:

```python
MY_STORE = os.environ.get("MY_STORE", "")   # empty => the step skips itself
```

### Ordering

Place post-install `func=` pseudo-entries **last** in the list, after the real
packages they depend on (and user-scoped steps before root-scoped ones when
both apply). *[Verify the framework's list-ordering guarantee before relying on
it — the install/func-dispatch logic lives in the seed harness, not
`pkgsSeed.py`.]*

## Sbom Dependencies

Declare prerequisite sboms using absolute paths:

```python
sbomsList = [
    sbom("/bisos/core/lcnt/bin/playwright-sbom.pcs"),
]
pkgsSeed.setup(
    pipPkgsList=pipPkgsList,
    sbomsList=sbomsList,
)
```

The prerequisite sbom runs to completion before this sbom's own installs begin.

## The `readme` Command Class

Every `-sbom.pcs` must include a `readme` command class. Author only the body
after `####+END:` — the class head is generated boilerplate, do not hand-edit it.

```python
####+BEGIN: b:py3:cs:cmnd/classHead :cmndName "readme" :extent "verify" :comment "Describe" :parsMand "" :parsOpt "" :argsMin 0 :argsMax 0 :pyInv ""
""" #+begin_org
*  ... <<readme>>  *Describe*  =verify= ro=cli
#+end_org """
class readme(cs.Cmnd):
    cmndParamsMandatory = [ ]
    cmndParamsOptional = [ ]
    cmndArgsLen = {'Min': 0, 'Max': 0,}

    @cs.track(fnLoc=True, fnEntry=True, fnExit=True)
    def cmnd(self,
             rtInv: cs.RtInvoker,
             cmndOutcome: b.op.Outcome,
    ) -> b.op.Outcome:
        """Describe"""
        failed = b_io.eh.badOutcome
        callParamsDict = {}
        if self.invocationValidate(rtInv, cmndOutcome, callParamsDict, None).isProblematic():
            return failed(cmndOutcome)
####+END:
        descriptionStr = """\
** Scope: <one-line scope>

** Components installed:

  1) pkg-name
       - What it does.
       - CLI: pkg-name <args>
       - Library: from pkg import Thing

** Installation:
       my-sbom.pcs -i sbom_fullUpdate

** Update:
       /bisos/venv/py3/asc/bin/pip install --upgrade pkg-name\
"""
        print(descriptionStr)

        return cmndOutcome.set(
            opError=b.op.OpError.Success,
            opResults=None,
        )
```

## The `examples_csu` Function

Provides usage examples shown in the CLI menu. Pattern:

```python
def examples_csu() -> b.op.Outcome:
    cmnd = cs.examples.cmndEnter
    literal = cs.examples.execInsert
    cmndOutcome = b.op.Outcome()

    cs.examples.menuChapter('*pkg-name Examples*')
    if not (resStr := b.subProc.Op(outcome=cmndOutcome, log=0).bash(
       f"""which pkg-name""").stdout):
        pass

    literal(f"which pkg-name # {resStr.strip()}")
    literal("pkg-name --help")

    cmnd('readme', comment=" # An overview short description")

    cs.examples.menuChapter('*Install / Update*')
    literal("my-sbom.pcs -i sbom_fullUpdate")
    literal("/bisos/venv/py3/asc/bin/pip install --upgrade pkg-name  # manual update")

    cs.examples.menuChapter('*Uninstall*')
    literal("/bisos/venv/py3/asc/bin/pip uninstall pkg-name")

    cs.examples.menuChapter('*End-Of  pkg-name Examples*')
    return cmndOutcome
```

## Running the Sbom

```bash
my-sbom.pcs -i sbom_fullUpdate   # install/update everything
my-sbom.pcs -i readme            # show description
my-sbom.pcs -i examples          # show usage examples
```
