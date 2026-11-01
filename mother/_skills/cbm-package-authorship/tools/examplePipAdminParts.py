import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
from csParts import cmndHead, EXAMPLES_HEAD, desc, DRIFT_HELPERS

SUMMARY = """\
* ~[Summary]~ :: A =CmndSvc= for admin-facing information about this host's
  =pypiserver.here= package index + pypi-browser installation: listeners, login, service
  status, paths, using the index, and config drift."""

DESCRIPTION = """\
* [[elisp:(org-cycle)][| ~Description~ |]] :: [[file:/bisos/git/auth/bxRepos/blee-binders/bisos-core/PyFwrk/bisos-pip/bisos.cs/_nodeBase_/fullUsagePanel-en.org][BISOS CmndSvcs Panel]]   [[elisp:(org-cycle)][| ]]

This is an admin-facing =CmndSvc= for this host's =pypiserver.here= installation --- pypiserver,
the package index, and pypi-browser, its web UI: the listeners, the upload login and where things
live, links for operating the =pypiserver-sysd.pcs= and =pypi-browser-sysd.pcs= units, pip and twine
against the index, and a read-only =driftCheck= of the live config files, the units and the pinned
packages in the shared venv against =bisos.pypiserver.pypiserverInfo=. Modelled on
=bisos.prometheus='s =prometheusAdmin.cs=.

** Status: Starting point
** /[[elisp:(org-cycle)][| Planned Improvements |]]/ :
*** TODO Live status Cmnds (package count, health) rather than printed examples"""

IMPORTS = """\
# The facts of the installation --- account, venv, pins, paths, listeners, fqdn, login --- come from
# bisos.pypiserver.pypiserverInfo, the one source the sbom, the units, dns and vhost read too.
import pathlib
import subprocess

from bisos.basics import pyRunAs
from bisos.pypiserver.pypiserverInfo import (
    pypiserverInfo, envFileContent, browserEnvFileContent, kvDrift, textDrift, unitDrift,
)
"""

i = "pypiserverInfo"

BODY = EXAMPLES_HEAD + f'''
        cs.examples.menuChapter('=Pypiserver.Here -- Host, Listeners, Login and Paths=')
        cmnd('hostInfo', comment=" # fqdn, the two banna ports, the upload login, venv, config/data paths")

        cs.examples.menuChapter('=Pypiserver.Here -- systemd Units=')
        cmnd('servicesInfo', comment=" # links to pypiserver-sysd.pcs and pypi-browser-sysd.pcs")

        cs.examples.menuChapter('=Pypiserver.Here -- Using the Index=')
        cmnd('indexInfo', comment=" # pip, twine and curl against the index")

        cs.examples.menuChapter('=Pypiserver.Here -- Do Installation And Code Agree?=')
        cmnd('driftCheck', comment=" # read-only: config files, units and the pinned packages against pypiserverInfo")

        cs.examples.menuChapter('=Full Overview=')
        cmnd('fullUpdate', comment=" # Show hostInfo + servicesInfo + indexInfo")

        return(cmndOutcome)

{cmndHead("fullUpdate")}{desc("Print hostInfo, servicesInfo and indexInfo together.")}
        hostInfo().pyCmnd()
        servicesInfo().pyCmnd()
        indexInfo().pyCmnd()

        return cmndOutcome


{cmndHead("hostInfo")}{desc("Print this host's pypiserver listeners, upload login and where things live.")}
        literal = cs.examples.execInsert

        cs.examples.menuSection('/Host and Login/')
        literal(f"echo {{{i}.fqdn}}   # fqdn -- see py3/bin/pypiserver-here-dns.pcs")
        literal(f"{{{i}.baseUrl}}   # pypi-browser -- open in a browser")
        literal(f"echo {{{i}.indexUrl}}   # the index, for pip")
        literal(f"echo {{{i}.adminUser}} / {{{i}.adminPassword}}   # upload login; rawBisos convention, insecure by design")

        cs.examples.menuSection('/Listeners -- ports from bisos.banna tcpPorts/')
        literal(f"echo {{{i}.listenAddr}}   # pypiserver (waitress)")
        literal(f"echo {{{i}.browserAddr}}   # pypi-browser (uvicorn)")
        literal(f"ss -ltnp | grep -E ':({{{i}.portNu}}|{{{i}.browserPortNu}}) '")
        literal(f"curl -s {{{i}.localUrl}}/health")

        cs.examples.menuSection('/Installation -- pinned in bisos.pypiserver.pypiserverInfo; asc and an isolated venv/')
        literal(f"{{{i}.venvBin('pip')}} show pypiserver waitress passlib | grep -E '^(Name|Version)'")
        literal(f"{{{i}.browserVenvBin('pip')}} show pypi-browser-webapp starlette uvicorn | grep -E '^(Name|Version)'   # isolated venv")

        cs.examples.menuSection('/Config -- root:pypiserver 640, written only when absent/')
        literal(f"sudo cat {{{i}.envFile}}")
        literal(f"sudo cat {{{i}.browserEnvFile}}")
        literal(f"sudo cat {{{i}.htpasswdFile}}")

        cs.examples.menuSection('/Data/')
        literal(f"sudo ls -l {{{i}.packagesDir}}   # the index")
        literal(f"sudo du -sh {{{i}.browserCacheDir}}   # pypi-browser's cache")

        cs.examples.menuSection('/Logs -- journald only/')
        literal("journalctl -u pypiserver.service -f")
        literal("journalctl -u pypi-browser.service -f")

        return cmndOutcome


{cmndHead("servicesInfo")}{desc("Print links for operating the two units (the index first, then the UI).")}
        literal = cs.examples.execInsert

        cs.examples.menuSection('/pypiserver/')
        literal("pypiserver-sysd.pcs -i examples   # list this unit's Cmnds")
        literal("systemctl status pypiserver.service")
        literal("systemctl restart pypiserver.service")

        cs.examples.menuSection('/pypi-browser/')
        literal("pypi-browser-sysd.pcs -i examples")
        literal("systemctl status pypi-browser.service")

        cs.examples.menuSection('/pypiserver.here -- dns and nginx vhost/')
        literal("pypiserver-here-dns.pcs -i dnsCap_verify")
        literal("pypiserver-wvd.pcs -i webVd_verify")
        literal("pypiserver-assemble.cs -i fullUpdate   # both of the above, updated")

        cs.examples.menuSection('/CBS/CBM assembly (sboms + 2 units + assemble as one bundle)/')
        literal("pypiserver-cbs.pcs -i examples")
        literal("cbmProc-pypiserver.spcs -i examples")

        return cmndOutcome


{cmndHead("indexInfo")}{desc("Print pip, twine and curl invocations against the index.")}
        literal = cs.examples.execInsert

        cs.examples.menuSection('/pip -- no login; --trusted-host because the index is plain HTTP/')
        literal(f"pip install {{{i}.pipExtraIndexArgs}} <package>   # this index and PyPI")
        literal(f"pip install {{{i}.pipIndexArgs}} <package>   # this index only (no fallback to PyPI)")
        literal(f"pip download --no-deps {{{i}.pipIndexArgs}} <package> -d /tmp")

        cs.examples.menuSection('/twine -- from pypiserverUsage-sbom.pcs; the upload login/')
        literal(f"{{{i}.twineBin}} upload --repository-url {{{i}.uploadUrl}} -u {{{i}.adminUser}} -p {{{i}.adminPassword}} dist/*")

        cs.examples.menuSection('/Copy a file in directly (no upload)/')
        literal(f"sudo install -o {{{i}.acctName}} -g {{{i}.acctName}} -m 644 <file.whl> {{{i}.packagesDir}}/")

        cs.examples.menuSection('/curl/')
        literal(f"curl -s {{{i}.indexUrl}}")
        literal(f"curl -s {{{i}.localUrl}}/<package>/json | head -c 400")

        return cmndOutcome


{cmndHead("driftCheck")}{desc("Compare the live installation with bisos.pypiserver.pypiserverInfo. Read-only.")}
        # The files are root:pypiserver 640, so they are read as root. Nothing is written.
        # They are written only when absent: hand overrides are legitimate, and generator lines
        # added later never reach existing hosts. "missing" is therefore a finding, not an error.
        _reportKvDrift({i}.envFile, envFileContent())
        _reportKvDrift({i}.browserEnvFile, browserEnvFileContent())
        _reportHtpasswd()
        _reportUnitDrift("pypiserver", {i}.envFile)
        _reportUnitDrift("pypi-browser", {i}.browserEnvFile)
        _reportPins()

        return cmndOutcome


def _reportHtpasswd() -> None:
    """The htpasswd hash is salted, so it cannot be compared with a generator: check the user is there."""
    path = {i}.htpasswdFile
    print(f"* {{path}}")
    if not _exists(path):
        print("  not installed")
        return
    liveText = pyRunAs.as_root_readFromFile(path) or ""
    users = [line.split(":", 1)[0] for line in liveText.splitlines() if ":" in line]
    if {i}.adminUser in users:
        print(f"  has {{{i}.adminUser}} (users: {{', '.join(users)}})")
    else:
        print(f"  lacks {{{i}.adminUser}} (users: {{', '.join(users) or 'none'}})")


def _installedVersions(python) -> dict:
    """{{canonical name: version}} of every distribution in the venv of python; {{}} if it does not exist."""
    if not python.exists():
        return {{}}
    out = subprocess.run([str(python), "-c",
                          "import importlib.metadata as m, re; "
                          "[print(re.sub(r'[-_.]+', '-', d.metadata['Name']).lower(), d.version) for d in m.distributions()]"],
                         capture_output=True, text=True).stdout
    return dict(line.split(" ", 1) for line in out.splitlines() if " " in line)


def _reportVenvPins(title, python, pins) -> None:
    """pins: (name, version) pairs. Each installed version against its pin."""
    print(f"* {{title}}")
    installed = _installedVersions(python)
    if not installed:
        print("  not installed")
        return
    off = 0
    for name, want in pins:
        got = installed.get(name)
        if got is None:
            print(f"  missing  {{name}}   (pinned {{want}})"); off += 1
        elif got != want:
            print(f"  differs  {{name}}   pinned={{want}}   installed={{got}}"); off += 1
    if not off:
        print(f"  all {{len(pins)}} as pinned")


def _reportPins() -> None:
    ascPins = [(p.split("==")[0].split("[")[0], p.split("==")[1]) for p in {i}.pipPins]
    _reportVenvPins(f"{{{i}.virtenv}} (shared venv)", {i}.venvBin("python"), ascPins)
    _reportVenvPins(f"{{{i}.browserVenv}} (isolated venv, hash-pinned)", {i}.browserVenvBin("python"),
                    [(n, v) for n, v, _ in {i}.browserReqs])

{DRIFT_HELPERS.split("def _reportTextDrift")[0]}
def _reportUnitDrift{DRIFT_HELPERS.split("def _reportUnitDrift")[1].split("def _reportLink")[0]}
'''
