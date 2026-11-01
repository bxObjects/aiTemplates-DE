"""Assemble a csmu .cs from kafkaAdmin.cs's framework parts plus a new summary, description, imports and Cmnds.

Usage: python makeCs.py <out.cs> <moduleName> <parts.py>
parts.py defines SUMMARY, DESCRIPTION, IMPORTS, BODY (strings).
"""
import pathlib
import sys
import runpy

model = pathlib.Path("/bisos/git/bxRepos/bisos-pip/kafka/py3/bin/kafkaAdmin.cs").read_text().splitlines(keepends=True)
out, moduleName, partsFile = sys.argv[1:4]
parts = runpy.run_path(partsFile)


def find(prefix, start=0):
    for i in range(start, len(model)):
        if model[i].startswith(prefix):
            return i
    raise SystemExit(f"not found: {prefix}")


iSummaryEnd = find('#+end_org """', 3)                     # end of the summary docstring
iDescStart = find('""" #+begin_org', find("####+END:", find("####+BEGIN: b:py3:file/particulars-csInfo")))
iDescEnd = find('#+end_org """', iDescStart)
iFacts = find("# The facts of the installation")
iFactsEnd = find(")", iFacts)
iCmndSvcsEnd = find("####+END:", find("####+BEGIN: blee:bxPanel:foldingSection :outLevel 0 :sep nil :title \"CmndSvcs\""))
iMain = find('####+BEGIN: blee:bxPanel:foldingSection :outLevel 0 :sep nil :title "Main"')

head = "".join(model[:3]) + '""" #+begin_org\n' + parts["SUMMARY"].rstrip() + "\n#+end_org \"\"\"\n"
middle = "".join(model[iSummaryEnd + 1:iDescStart])
middle = middle.replace("/bxRepos/bisos-pip/airflow/py3/bin/airflowAdmin.cs", str(pathlib.Path(out).resolve()).replace("/bisos/git/auth/", "/bisos/git/"))
middle = middle.replace("'airflowAdmin'", f"'{moduleName}'").replace("airflowAdmin-Panel.org", f"{moduleName}-Panel.org")
desc = '""" #+begin_org\n' + parts["DESCRIPTION"].rstrip() + "\n#+end_org \"\"\"\n"
afterDesc = "".join(model[iDescEnd + 1:iFacts])
imports = parts["IMPORTS"].rstrip() + "\n"
toCmnds = "".join(model[iFactsEnd + 1:iCmndSvcsEnd + 1])
tail = "".join(model[iMain:])

pathlib.Path(out).write_text(head + middle + desc + afterDesc + imports + toCmnds + "\n" + parts["BODY"].strip("\n") + "\n\n\n" + tail)
print(f"wrote {out}")
