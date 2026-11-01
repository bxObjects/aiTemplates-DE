import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
from csParts import cmndHead, EXAMPLES_HEAD, desc, DRIFT_HELPERS

SUMMARY = """\
* ~[Summary]~ :: A =CmndSvc= for admin-facing information about this host's
  =prometheus.here= Prometheus + node_exporter installation: listeners, service status,
  paths, PromQL queries and config drift."""

DESCRIPTION = """\
* [[elisp:(org-cycle)][| ~Description~ |]] :: [[file:/bisos/git/auth/bxRepos/blee-binders/bisos-core/PyFwrk/bisos-pip/bisos.cs/_nodeBase_/fullUsagePanel-en.org][BISOS CmndSvcs Panel]]   [[elisp:(org-cycle)][| ]]

This is an admin-facing =CmndSvc= for this host's =prometheus.here= installation ---
the Prometheus server and this host's node_exporter: the listeners and where things live,
links for operating the =prometheus-sysd.pcs= and =prometheus-node-exporter-sysd.pcs= units,
PromQL queries through promtool and the HTTP API, and a read-only =driftCheck= of the live
config files and units against =bisos.prometheus.prometheusInfo=. Modelled on
=bisos.kafka='s =kafkaAdmin.cs=.

** Status: Starting point
** /[[elisp:(org-cycle)][| Planned Improvements |]]/ :
*** TODO Live status Cmnds (targets up, TSDB size) rather than printed examples"""

IMPORTS = """\
# The facts of the installation --- account, versions, paths, listeners, fqdn --- come from
# bisos.prometheus.prometheusInfo, the one source the sbom, the units, dns and vhost read too.
import pathlib

from bisos.basics import pyRunAs
from bisos.prometheus.prometheusInfo import (
    prometheusInfo, configFileContent, envFileContent, nodeExporterEnvFileContent,
    kvDrift, textDrift, unitDrift,
)
"""

i = "prometheusInfo"

BODY = EXAMPLES_HEAD + f'''
        cs.examples.menuChapter('=Prometheus.Here -- Host, Listeners and Paths=')
        cmnd('hostInfo', comment=" # fqdn, the two banna ports, install/config/data paths")

        cs.examples.menuChapter('=Prometheus.Here -- systemd Units=')
        cmnd('servicesInfo', comment=" # links to prometheus-sysd.pcs and prometheus-node-exporter-sysd.pcs")

        cs.examples.menuChapter('=Prometheus.Here -- Queries=')
        cmnd('queriesInfo', comment=" # PromQL through promtool and the HTTP API; targets; reload")

        cs.examples.menuChapter('=Prometheus.Here -- Do Installation And Code Agree?=')
        cmnd('driftCheck', comment=" # read-only: live config files, units and links against bisos.prometheus.prometheusInfo")

        cs.examples.menuChapter('=Full Overview=')
        cmnd('fullUpdate', comment=" # Show hostInfo + servicesInfo + queriesInfo")

        return(cmndOutcome)

{cmndHead("fullUpdate")}{desc("Print hostInfo, servicesInfo and queriesInfo together.")}
        hostInfo().pyCmnd()
        servicesInfo().pyCmnd()
        queriesInfo().pyCmnd()

        return cmndOutcome


{cmndHead("hostInfo")}{desc("Print this host's Prometheus listeners and where things live.")}
        literal = cs.examples.execInsert

        cs.examples.menuSection('/Host/')
        literal(f"echo {{{i}.fqdn}}   # fqdn -- see py3/bin/prometheus-here-dns.pcs")
        literal(f"{{{i}.baseUrl}}   # Prometheus -- open in a browser")
        literal(f"curl -s {{{i}.localUrl}}/-/healthy   # directly, bypassing nginx")

        cs.examples.menuSection('/Listeners -- ports from bisos.banna tcpPorts/')
        literal(f"echo {{{i}.listenAddr}}   # prometheus: web UI and HTTP API")
        literal(f"echo {{{i}.nodeExporterAddr}}   # node_exporter: /metrics")
        literal(f"ss -ltnp | grep -E ':({{{i}.portNu}}|{{{i}.nodeExporterPortNu}}) '")

        cs.examples.menuSection('/Installation -- versions are pinned in bisos.prometheus.prometheusInfo/')
        literal(f"ls -l {{{i}.homeLink}} {{{i}.nodeExporterLink}}")
        literal(f"{{{i}.promBin}} --version")
        literal(f"{{{i}.nodeExporterBin}} --version")

        cs.examples.menuSection('/Config -- root:prometheus 640, written only when absent/')
        literal(f"sudo cat {{{i}.configFile}}")
        literal(f"sudo cat {{{i}.envFile}}")
        literal(f"sudo cat {{{i}.nodeExporterEnvFile}}")

        cs.examples.menuSection('/Data -- the TSDB/')
        literal(f"sudo du -sh {{{i}.dataDir}}")

        cs.examples.menuSection('/Logs -- journald only/')
        literal("journalctl -u prometheus.service -f")
        literal("journalctl -u prometheus-node-exporter.service -f")

        return cmndOutcome


{cmndHead("servicesInfo")}{desc("Print links for operating the two units (the exporter first, then the server).")}
        literal = cs.examples.execInsert

        cs.examples.menuSection('/node_exporter/')
        literal("prometheus-node-exporter-sysd.pcs -i examples   # list this unit's Cmnds")
        literal("systemctl status prometheus-node-exporter.service")

        cs.examples.menuSection('/Prometheus/')
        literal("prometheus-sysd.pcs -i examples")
        literal("systemctl status prometheus.service")
        literal("systemctl reload prometheus.service   # SIGHUP: re-reads prometheus.yml")

        cs.examples.menuSection('/prometheus.here -- dns and nginx vhost/')
        literal("prometheus-here-dns.pcs -i dnsCap_verify")
        literal("prometheus-wvd.pcs -i webVd_verify")
        literal("prometheus-assemble.cs -i fullUpdate   # both of the above, updated")

        cs.examples.menuSection('/CBS/CBM assembly (sboms + 2 units + assemble as one bundle)/')
        literal("prometheus-cbs.pcs -i examples")
        literal("cbmProc-prometheus.spcs -i examples")

        return cmndOutcome


{cmndHead("queriesInfo")}{desc("Print PromQL queries through promtool and the HTTP API.")}
        literal = cs.examples.execInsert

        cs.examples.menuSection('/promtool -- from prometheusUsage-sbom.pcs/')
        literal(f"{{{i}.promtool}} query instant {{{i}.localUrl}} up")
        literal(f"{{{i}.promtool}} query instant {{{i}.localUrl}} 'node_load1'")
        literal(f"{{{i}.promtool}} query range --start=$(date -d -1hour +%s) --end=$(date +%s) --step=60s {{{i}.localUrl}} 'rate(node_cpu_seconds_total{{{{mode=\\"idle\\"}}}}[5m])'")

        cs.examples.menuSection('/HTTP API/')
        literal(f"curl -s '{{{i}.localUrl}}/api/v1/query?query=up'")
        literal(f"curl -s {{{i}.localUrl}}/api/v1/targets | head -c 600")
        literal(f"curl -s http://{{{i}.nodeExporterAddr}}/metrics | head")

        cs.examples.menuSection('/Config/')
        literal(f"sudo -u {{{i}.acctName}} {{{i}.promtool}} check config {{{i}.configFile}}")

        return cmndOutcome


{cmndHead("driftCheck")}{desc("Compare the live installation with bisos.prometheus.prometheusInfo. Read-only.")}
        # The files are root:prometheus 640, so they are read as root. Nothing is written.
        # They are written only when absent: hand overrides are legitimate, and generator lines
        # added later never reach existing hosts. "missing" is therefore a finding, not an error.
        _reportTextDrift({i}.configFile, configFileContent())
        _reportKvDrift({i}.envFile, envFileContent())
        _reportKvDrift({i}.nodeExporterEnvFile, nodeExporterEnvFileContent())
        _reportUnitDrift("prometheus", {i}.envFile)
        _reportUnitDrift("prometheus-node-exporter", {i}.nodeExporterEnvFile)
        _reportLink({i}.homeLink, {i}.distDir(_arch()))
        _reportLink({i}.nodeExporterLink, {i}.nodeExporterDir(_arch()))

        return cmndOutcome


def _arch() -> str:
    import subprocess
    return subprocess.run(["dpkg", "--print-architecture"], capture_output=True, text=True).stdout.strip()

{DRIFT_HELPERS}
'''
