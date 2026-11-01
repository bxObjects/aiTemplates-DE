"""Shared pieces for the parts files of makeCs.py: the generated classHead dblocks, in kafkaAdmin.cs's exact form."""

_nav = ("*  _[[elisp:(blee:menu-sel:outline:popupMenu)][±]]_ _[[elisp:(blee:menu-sel:navigation:popupMenu)][Ξ]]_ "
        "[[elisp:(outline-show-branches+toggle)][|=]] [[elisp:(bx:orgm:indirectBufOther)][|>]] "
        "*[[elisp:(blee:ppmm:org-mode-toggle)][|N]]*  CmndSvc-   [[elisp:(outline-show-subtree+toggle)][||]] ")


def cmndHead(name: str) -> str:
    """classHead of a 0-arg, 0-param, ro=cli Cmnd, through its ####+END:."""
    return f'''####+BEGIN: b:py3:cs:cmnd/classHead :cmndName "{name}" :comment "" :extent "verify" :ro "cli" :parsMand "" :parsOpt "" :argsMin 0 :argsMax 0 :pyInv ""
""" #+begin_org
{_nav}<<{name}>>  =verify= ro=cli   [[elisp:(org-cycle)][| ]]
#+end_org """
class {name}(cs.Cmnd):
    cmndParamsMandatory = [ ]
    cmndParamsOptional = [ ]
    cmndArgsLen = {{'Min': 0, 'Max': 0,}}

    @cs.track(fnLoc=True, fnEntry=True, fnExit=True)
    def cmnd(self,
             rtInv: cs.RtInvoker,
             cmndOutcome: b.op.Outcome,
    ) -> b.op.Outcome:

        failed = b_io.eh.badOutcome
        callParamsDict = {{}}
        if self.invocationValidate(rtInv, cmndOutcome, callParamsDict, None).isProblematic():
            return failed(cmndOutcome)
####+END:
'''


EXAMPLES_HEAD = f'''####+BEGIN: b:py3:cs:cmnd/classHead :cmndName "examples" :extent "verify" :ro "noCli" :comment "FrameWrk: CS-Main-Examples" :parsMand "" :parsOpt "" :argsMin 0 :argsMax 0 :pyInv ""
""" #+begin_org
{_nav}<<examples>>  *FrameWrk: CS-Main-Examples*  =verify= ro=noCli   [[elisp:(org-cycle)][| ]]
#+end_org """
class examples(cs.Cmnd):
    cmndParamsMandatory = [ ]
    cmndParamsOptional = [ ]
    cmndArgsLen = {{'Min': 0, 'Max': 0,}}
    rtInvConstraints = cs.rtInvoker.RtInvoker.new_noRo() # NO RO From CLI

    @cs.track(fnLoc=True, fnEntry=True, fnExit=True)
    def cmnd(self,
             rtInv: cs.RtInvoker,
             cmndOutcome: b.op.Outcome,
    ) -> b.op.Outcome:
        """FrameWrk: CS-Main-Examples"""
        failed = b_io.eh.badOutcome
        callParamsDict = {{}}
        if self.invocationValidate(rtInv, cmndOutcome, callParamsDict, None).isProblematic():
            return failed(cmndOutcome)
####+END:
        self.cmndDocStr(f""" #+begin_org
***** [[elisp:(org-cycle)][| *CmndDesc:* | ]]  Conventional top level example.
        #+end_org """)

        cs.examples.myName(cs.G.icmMyName(), cs.G.icmMyFullName())
        cs.examples.commonBrief()

        cmnd = cs.examples.cmndEnter
'''


def desc(text: str) -> str:
    return f'''        if self.cmndDocStr(f""" #+begin_org
** [[elisp:(org-cycle)][| *CmndDesc:* | ]]  {text}
        #+end_org """): return(cmndOutcome)
'''


# The drift-reporting loop every <name>Admin.cs driftCheck shares. Uses names from <name>Info:
# kvDrift, textDrift, unitDrift, pyRunAs. Format it with info=<name>Info.
DRIFT_HELPERS = '''
def _exists(path) -> bool:
    """Whether path exists, also inside a directory the invoker cannot search (e.g. /etc/grafana 750)."""
    try:
        return path.exists()
    except PermissionError:
        import subprocess
        return subprocess.run(["sudo", "test", "-e", str(path)]).returncode == 0


def _reportKvDrift(livePath, generated) -> None:
    """KEY=VALUE files (EnvironmentFiles): missing / differs / extra, as kafkaAdmin.cs does."""
    print(f"* {livePath}")
    if not _exists(livePath):
        print("  not installed")
        return
    liveText = pyRunAs.as_root_readFromFile(livePath)
    if not liveText:
        print(f"  cannot read {livePath}")
        return
    drift = kvDrift(liveText, generated)
    for key in drift["missing"]:
        print(f"  missing  {key}   (generator has it, live file does not)")
    for key, expected, live in drift["differs"]:
        print(f"  differs  {key}   expected={expected}   live={live}")
    for key in drift["extra"]:
        print(f"  extra    {key}   (not generated -- a hand addition)")
    if not (drift["missing"] or drift["differs"] or drift["extra"]):
        print("  agrees with the generator")


def _reportTextDrift(livePath, generated) -> None:
    """Structured files (YAML, INI): a unified diff against the generator."""
    print(f"* {livePath}")
    if not _exists(livePath):
        print("  not installed")
        return
    liveText = pyRunAs.as_root_readFromFile(livePath)
    if not liveText:
        print(f"  cannot read {livePath}")
        return
    diff = textDrift(liveText, generated)
    if diff:
        for line in diff:
            print(f"  {line}")
    else:
        print("  agrees with the generator")


def _reportUnitDrift(unitName, envFile) -> None:
    unitPath = pathlib.Path(f"/etc/systemd/system/{unitName}.service")
    print(f"* {unitPath}")
    if not unitPath.exists():
        print("  not installed")
        return
    lacking = unitDrift(unitPath.read_text(), envFile)
    for line in lacking:
        print(f"  missing  {line}")
    if not lacking:
        print("  identity lines agree (User, Group, EnvironmentFile)")


def _reportLink(link, pinned) -> None:
    print(f"* {link}")
    if not link.exists():
        print("  not installed")
    elif link.resolve() != pinned:
        print(f"  points at {link.resolve()}, the pinned version is {pinned}")
    else:
        print(f"  points at the pinned {pinned.name}")
'''
