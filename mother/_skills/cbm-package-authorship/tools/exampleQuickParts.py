import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
from csParts import cmndHead, EXAMPLES_HEAD

SUMMARY = """\
* ~[Summary]~ :: A =CmndSvc= cheat sheet of direct commands for this host's Prometheus,
  node_exporter, promtool and their systemd units."""

DESCRIPTION = """\
* [[elisp:(org-cycle)][| ~Description~ |]] :: [[file:/bisos/git/auth/bxRepos/blee-binders/bisos-core/PyFwrk/bisos-pip/bisos.cs/_nodeBase_/fullUsagePanel-en.org][BISOS CmndSvcs Panel]]   [[elisp:(org-cycle)][| ]]

Direct invocations --- promtool, curl against the HTTP API, systemctl, journalctl --- with this
host's addresses filled in from =bisos.prometheus.prometheusInfo=. prometheusAdmin.cs has the
organized views; this is the flat cheat sheet. Modelled on =bisos.kafka='s =quickKafka.cs=.

** Status: Starting point"""

IMPORTS = """\
from bisos.prometheus.prometheusInfo import prometheusInfo
"""

i = "prometheusInfo"

BODY = EXAMPLES_HEAD.replace("        cmnd = cs.examples.cmndEnter\n", "") + f'''
        prometheusDirectCmnds().pyCmnd()

        return(cmndOutcome)


{cmndHead("prometheusDirectCmnds")}        self.cmndDocStr(f""" #+begin_org
** [[elisp:(org-cycle)][| *CmndDesc:* | ]]  Provide direct examples of how to use Prometheus, node_exporter,
        promtool and this host's prometheus / prometheus-node-exporter systemd units.
        #+end_org """)

        literal = cs.examples.execInsert
        _url = {i}.localUrl

        cs.examples.menuChapter('=Direct Prometheus Interface Commands=')

        cs.examples.menuSection('/Environment/')
        literal(f"export PATH={{{i}.homeLink}}:$PATH   # prometheus and promtool are not on PATH by default")
        literal(f"export PROM={{_url}}")
        literal("promtool --version")

        cs.examples.menuSection('/Queries -- PromQL/')
        literal("promtool query instant $PROM up")
        literal("promtool query instant $PROM 'count by (job) (up)'")
        literal("promtool query labels $PROM job")
        literal("curl -s \\"$PROM/api/v1/query?query=up\\"")

        cs.examples.menuSection('/Targets and Health/')
        literal("curl -s $PROM/-/healthy ; curl -s $PROM/-/ready")
        literal("curl -s $PROM/api/v1/targets | head -c 600")
        literal(f"curl -s http://{{{i}.nodeExporterAddr}}/metrics | grep ^node_load")

        cs.examples.menuSection('/Config and Rules/')
        literal(f"sudo -u {{{i}.acctName}} promtool check config {{{i}.configFile}}")
        literal("systemctl reload prometheus.service   # SIGHUP: re-read prometheus.yml after an edit")

        cs.examples.menuSection('/systemd Units/')
        literal("systemctl status prometheus.service prometheus-node-exporter.service")
        literal("systemctl restart prometheus-node-exporter.service prometheus.service")

        cs.examples.menuSection('/Logs -- journald only/')
        literal("journalctl -u prometheus.service -f")
        literal("journalctl -u prometheus-node-exporter.service -f")

        cs.examples.menuChapter('=Web UI Hints=')

        cs.examples.menuSection('/Getting In/')
        literal(f"# {{{i}.baseUrl}}   -- no login: Prometheus is loopback-only, without auth")
        literal(f"# {{_url}}  -- directly, bypassing nginx")

        cs.examples.menuSection('/Reading Failures/')
        literal("# Target down             -> Status > Targets; the exporter's unit, then its port")
        literal("# Unit will not start     -> promtool check config; journalctl -u prometheus.service")
        literal("# Links point at :24010   -> --web.external-url in /etc/default/prometheus")

        return(cmndOutcome)
'''
