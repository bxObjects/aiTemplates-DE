---
name: cbm-package-authorship
description: Use when creating a new bisos-pip CBM package that runs a common open-source program as a BISOS capability (e.g. bisos.kafka, bisos.prometheus, bisos.grafana, bisos.pypiserver) — or adding a second program to one. Covers the decisions to settle first (install source, usage side, login, integrations), the banna registrations (ports, .here IP, uid/gid), pinning and verifying upstream releases, scaffolding the repo from a model package (tools/cbmPkgScaffold.sh), the files to write and their contracts (<name>Info.py as the single source of facts, Python programs in the shared /bisos/venv/py3/asc venv or an /bisos/venv/py3/isolated/<program> exception, the server/usage/bundle sbom trio, units, dns, vhost, assemble, CBS, CBM pointer, <name>Admin.cs with driftCheck, quick<Name>.cs, verify.sh, README), generating the .cs files (tools/makeCs.py), installing, verifying read-only, materializing, and the pitfalls already found. Load `cbm-authorship` for the CBM leaf itself and the sbom-split rules, `sysd-pcs-authorship` for unit details, `banna-lookup` for the registries.
---

# Creating a pip CBM Package for an Open-Source Program

A *CBM package* is a bisos-pip package that makes one open-source program a BISOS capability:
installed from pinned sources, run by systemd as its own account, reachable as `<name>.here`
through nginx, materialized by one CBS that a CBM leaf points at. Four packages follow the
pattern exactly and are the models:

| Package | Shape | Use it as the model when |
|---|---|---|
| `bisos.prometheus` | 2 units, YAML, no login | no login; **default model** |
| `bisos.grafana` | 1 unit, INI + provisioning, login | a login or provisioning |
| `bisos.kafka` | 2 units, Java, storage format | something is built or formatted |
| `bisos.pypiserver` | 2 Python programs, one fqdn | Python, or two programs share a name |
| `bisos.devpi` | isolated venv, setup oneshot | setup needs the service running |
| `bisos.gitlab` | vendor `.deb`, no units, base only | a big program for a dedicated VM |
| `bisos.geneweb` | zip release, demo data, 1 unit | a zip, or the program needs initial data |

Usage sides: promtool (prometheus), gcx (grafana), a Kerberos-built librdkafka (kafka), twine
through pipx (pypiserver), devpi-client through pipx (devpi), glab as a tarball (gitlab).
pypiserver has the `asc` venv plus an isolated one, devpi an isolated one only (§7a). geneweb's
usage side is its own command-line tools (GEDCOM import/export) from the same zip.

`bisos.airflow` and `bisos.postgres` predate the pattern in parts (airflow: one sbom; postgres:
bedrock, no web UI). Do not copy their deviations.

The leaf-level CBM rules (pointer, gate, `cbm_*` verbs) and the sbom-split rules are in
`cbm-authorship`. This skill is the package around them.

Where these packages sit --- Raw-BISOS as the base platform, generic CBM packages as the base
layer, `.here` for out-of-the-box use and regression (`sysCbmManage.cs -i fullyMaterialize`),
niching and CapabilityBPOs later, dedicated-VM CBMs --- and the catalog of existing CBMs (gates,
footprints, minimal settings) are in
`/bisos/git/bxRepos/bxGenesis/start/rawBisosCBMs/README.org`.
Read it first; it decides a new package's minimal configuration and whether it is enabled or
only available.

## 1. Settle these with the user first

Each is a real decision; propose a default, do not silently pick.

1. **Install source.** Default: the upstream release, pinned with its published checksum, when
   Debian lacks the program or lags a major version (Grafana: absent; Prometheus: 2.x vs 3.x;
   Kafka: absent). Use apt when Debian's version is current. One method across packages is part
   of the consistency. **Python programs** (no tarball; PyPI is the release): exact pins into
   the shared venv `/bisos/venv/py3/asc`, or, only for a demonstrated conflict, an isolated venv
   of their own (§7a). A Python *CLI* on the usage side goes through pipx (`/bisos/pipx`).
2. **Usage side.** What a host needs to *use* the service without running it: the separately
   packaged tools that talk to it (promtool, gcx, a client C library). Python libraries are
   *named* in the usage sbom's readme, not installed (they go in each consumer's venv). If
   there is genuinely nothing, ask before omitting the usage sbom.
3. **Login.** rawBisos (`bro_rawBisos`) is public and recognized as insecure. Convention: user
   `admin`, password = the service's name (`admin / grafana`), set where the program applies it
   once, stated in the readme. A program with no login listens on loopback only. A separate
   "secure it" layer, on top, owns real passwords, HTTPS (bisos.crypt) and non-loopback listeners.
4. **Integrations.** If the program talks to another capability (Grafana → Prometheus), take
   the other's port from `bisos.banna`, never import the other package. It must still work, with
   the integration unreachable, when the other is absent.
5. **Architectures.** Pin amd64; the install script refuses others with a clear message. Add an
   architecture by adding its checksum.

## 2. Register in bisos.banna (load `banna-lookup`)

- `tcpPorts.py`: next ports in the 24xxx service series; `hereIp` = the next free 127.0.22.x,
  *stored* on the port (never derived); `hereName` only if it differs from `portName`. Ports with
  no web UI (exporters, controllers) get no `hereIp`.
- `sysAccts.py`: the next uid in the single-account range (504–509 at the time of writing);
  `homeDir` = the data dir's parent. A helper process (node_exporter) runs as the main account.
- Before choosing: `getent passwd <uid>; getent group <gid>; ss -ltn | grep <port>`.
- Update banna's README.org (the uid list) and AI-DevStatus.org. Banna's import-time check rejects
  a duplicate IP/name; import it once to confirm.

## 3. Pin and verify the upstream release

```bash
# tags and assets of the latest releases:
curl -fsSL "https://api.github.com/repos/<org>/<repo>/releases?per_page=6" | python3 -c '...'
```

Download each tarball into the scratchpad, check it against the *published* checksum
(`sha256sums.txt`, `<tarball>.sha256`, or the GitHub asset `digest`), and `tar -tzf` it: note the
top directory name (with or without the architecture) or its absence (gcx has none →
`hasTopDir=False`). Record version and checksum in `<name>Info.py` only after both match.

## 4. Scaffold the repo

```bash
cd /bisos/git/bxRepos/bisos-pip/<name>          # the cloned, empty GitHub repo
/bisos/venv/py3/devbin/aiActivity.cs -i initiate --activity=bisos-pip
<skill>/tools/cbmPkgScaffold.sh <name> prometheus   # copies the program-independent skeleton
```

The scaffold copies fto/tree markers, `py3/` packaging files, the namespace `__init__`, and the
panel tree, renaming the model's name; it never overwrites. Everything below is written by hand.

## 5. The files to write

| File (`py3/`) | Role | Copy from |
|---|---|---|
| `bisos/<name>/<name>Info.py` | the single source of facts and generators (§6) | prometheusInfo.py |
| `bin/<name>-sbom.pcs` | the server: account, dist, config | prometheus-sbom.pcs |
| `bin/<name>Usage-sbom.pcs` | the usage side (§1.2) | prometheusUsage-sbom.pcs |
| `bin/<name>Cbs-sbom.pcs` | bundle of the two, for the CBS | `sed` of prometheusCbs-sbom.pcs |
| `bin/<name>[-part]-sysd.pcs` | one per unit (load `sysd-pcs-authorship`) | prometheus-sysd.pcs |
| `bin/<name>-here-dns.pcs` | `/etc/hosts` entry | `sed` of prometheus-here-dns.pcs |
| `bin/<name>-wvd.pcs` | nginx vhost → `listenIp:port` (§8) | prometheus-wvd.pcs / grafana-wvd.pcs |
| `bin/<name>-assemble.cs` | hereDns + webVirtDom | `sed` of prometheus-assemble.cs, fix prose |
| `bin/<name>-cbs.pcs` | the CBS: bundle sbom + units + assemble | prometheus-cbs.pcs |
| `bin/cbmProc-<name>.spcs` | CBM pointer (absolute `cbsSpec`) | `sed` of cbmProc-prometheus.spcs |
| `bin/<name>Admin.cs` | info Cmnds, driftCheck, fullUpdate | `tools/makeCs.py` (§9) |
| `bin/quick<Name>.cs` | flat cheat sheet of direct commands | `tools/makeCs.py` (§9) |
| `tests/verify.sh` | smoke test + `<name>Info` invariants | prometheus's |
| `../README.org` | the package's README (§11) | prometheus's / grafana's |

## 6. `<name>Info.py` --- the contract

Pure (no side effects at import). One frozen dataclass and singleton `<name>Info`, plus module
functions. Everything else imports it; nothing else holds a fact.

- `acctName`; `version` + `distSha256` as a tuple of `(debianArch, sha256)`; the same for each
  extra binary (exporter, CLI).
- Paths: `installBase=/opt/<name>`, `distDir`, `homeLink=/opt/<name>/current` (units and CLIs go
  through the link, never the versioned dir), `confDir=/etc/<name>`, `dataDir=/var/lib/<name>[/data]`,
  `envFile=/etc/default/<name>` (one per unit).
- `listenIp="127.0.0.1"`, ports via `_bannaPortNu(...)` (never literals), `fqdn="<name>.here"`,
  `baseUrl`, `localUrl`, and the login if any.
- `tarballSetupScript(url, sha256, dirName, link, base, hasTopDir=True)`: bash that picks the
  checksum by `dpkg --print-architecture`, downloads to a temp dir, verifies, unpacks root-owned
  once per version, then flips the link. Identical in every package (copy it verbatim).
- One generator per config file (`configFileContent`, `envFileContent`, ...): what the sbom
  writes *only when absent*, and what driftCheck compares against.
- `sysdServiceLines(envFile)` (`User=`, `Group=`, `EnvironmentFile=`), `unitDrift`, `kvDrift`
  (KEY=VALUE files), `textDrift` (unified diff, for YAML/INI/JSON).

## 7. The sboms and units

- Server sbom: `curl`, then func-bearing pseudo-packages in load-bearing order:
  `<name>AcctSetup` (`sysAccts.useraddScript()`, data dir chowned, 750), `<name>DistSetup`,
  extra binaries, `<name>ConfSetup` (each file written only when absent, `root:<acct> 640`; run
  the program's own config check if it has one, e.g. `promtool check config`). Every func runs on
  every `sbom_fullUpdate` and must be idempotent.
- Usage sbom: `curl` + one func per tool; may reuse the server's dist script (promtool lives in
  the Prometheus tarball: whichever sbom runs first unpacks it).
- Bundle sbom: the generic file, renamed.
- Units: `Type=simple`, identity lines from `sysdServiceLines`, `ExecStart=<homeLink>/... $ARGS`
  with flags in the EnvironmentFile (`$ARGS` splits into words; `${ARGS}` would not),
  `Restart=on-failure`. `sysdUnitFileFunc` returns `None` while the binary is absent. List units
  in the CBS in start order (what is scraped/needed first).

## 7a. Python programs: `asc`, `isolated`, and how pins are applied

- **`/bisos/venv/py3/asc`** --- the shared venv of BISOS's adopted software components (created by
  `pyVenv-asc-sbom.pcs`; bisos.airflow's programs live there). The default for every Python
  program. Exact pins (`name==version`); **no hashes**: a shared venv cannot require them without
  covering every other capability's packages. Install behind a **dry-run guard**: `pip install
  --dry-run --report` first, and refuse if any package the pins do not own would change version
  (copy `pipSetupScript()` from `pypiserverInfo.py`). A package another capability also uses
  (uvicorn, starlette) is never pinned by you: list it as `unpinnedShared` (installed if absent).
- **`/bisos/venv/py3/isolated/<program>/`** --- the exceptions (user's naming, 2026-10-16). Rules:
  1. *When*: only for a conflict actually shown --- the guard refusing, or the program failing
     against `asc`'s versions. Wanting a venv of one's own is not a reason.
  2. *Leaf name*: the program, camelCase as banna names are (`isolated/pypiBrowser`), not the
     capability: the conflict is the program's, and one capability may need two.
  3. *The reason is recorded* next to the venv path in `<name>Info.py` and in the README, with the
     upstream fix if known; move back to `asc` and delete the venv when the reason is gone.
  4. *Created by the capability's sbom*: the same base Python as `asc` (`asc/pyvenv.cfg`), no sudo
     (`/bisos/venv/py3` is group-writable), then the **whole resolved set hash-pinned**:
     `pip install --require-hashes --no-deps -r <set>`, then `pip check`. Copy
     `browserVenvSetupScript()`. Binary wheels make the set architecture- and Python-specific:
     record which, and refuse others.
  5. *pipx is not the answer*: it is for CLIs (it refuses a package with no entry point, and
     manages the venv itself). Keep it for usage-side CLIs like twine.
- **Making the hashed set**: in a scratch venv from the same Python, `pip download -d dl <pins>`;
  sha256 each file; check every hash against PyPI's published digest
  (`https://pypi.org/pypi/<name>/<version>/json` → `urls[].digests.sha256`); install it into a
  second scratch venv with `--require-hashes --no-deps` and **start the program** there before
  writing anything.
- **The guard sees only declared conflicts.** pypi-browser declares no Starlette bound, so pip and
  the guard both accepted it into `asc`, where it failed on every request. The real test is
  starting the service and requesting a page.
- **Pins are applied by func-bearing pseudo-packages**, never by `pipPkgsList` / `pipxPkgsList`:
  bisos.sbom's pip and pipx steps ignore `ver=` and skip anything already installed (AI-Outputs.org),
  so a pin would never be applied or bumped. pip is a no-op when a pin is satisfied, so the
  pseudo-package stays idempotent; for pipx, compare the installed version and `pipx install
  --force 'name==version'` only when it differs (`twineSetupScript()`).
- **The PyPI name may not be the program's.** `pypi-browser` on PyPI is an unrelated 2007 project;
  the program is `pypi-browser-webapp`. Check `https://pypi.org/pypi/<name>/json` (summary, date).
- **WSGI and ASGI need a server process.** A Python web app is called by a server: WSGI apps
  (bottle, Flask; pypiserver) by waitress or gunicorn, ASGI apps (Starlette, FastAPI; pypi-browser)
  by uvicorn. That server is the unit's `ExecStart`, on loopback; nginx stays the reverse proxy in
  front, as for every `.here`. Check that the program really uses the server you install
  (pypiserver's `--server` rejects `waitress` by name; its `auto` picks it --- confirm by thread
  count or the `Server:` header).
- **pip and plain HTTP.** pip ignores an index on plain HTTP other than localhost unless named with
  `--trusted-host` ("not a trusted or secure host and is being ignored"). Every `.here` is HTTP: put
  the arguments in `<name>Info` (`pipIndexArgs`) and use them everywhere.

## 7a2. Initial data, zips, and components that cannot bind loopback

- **Out-of-the-box data.** When the program serves nothing until data exists (GeneWeb's bases), the
  sbom creates a minimal one once, with the program's own tool, as the account (`demoBaseScript()`:
  `gwc -o demo` when `demo.gwb` is absent). Never sample personal data; an empty base is enough.
- **A zip release.** `zipSetupScript()` in `genewebInfo.py` is the zip form of `tarballSetupScript`
  (`unzip -d <dir>`, for a zip without a top directory); add `unzip` to the apt list.
- **A component that cannot bind an address** (GeneWeb's `gwsetup` listens on every interface; it
  only filters clients with `-only`): leave it out of the CBS and say so in the README; do what it
  did with the command-line tools instead.
- **Test the read-only layout first**: run the program in scratch from a `chmod -R a-w` copy of the
  release, with only its data and work directories writable, before writing the unit.

## 7b. Setup that needs the service running: a oneshot unit

`cbs_materialize` runs **sbom, then assemble, then the units** (`cba_csu.py`). So anything that
talks to the running service --- creating users or indexes over its API --- cannot go in the sbom or
the assemble step: on a first materialization the service is not up yet. Make it a oneshot unit
ordered after the service (`Type=oneshot`, `RemainAfterExit=yes`, `After=` and `Requires=` the
service), listed after it in the CBS. Its script is generated from `<name>Info` and written by the
sbom on every run (it is code, not configuration); it waits for the service, then creates only what
is absent, so it is idempotent. Model: `devpi-accounts-sysd.pcs` and `accountsScriptContent()`.

## 7c. Base-only packages: big programs for a dedicated VM

Some programs are too big for a raw platform (GitLab: 8 vCPU / 16 GB baseline). Build the package
here as *base code*, plant its leaf as `available`, and materialize it in a dedicated VM. Check
everything that needs no installation, and say plainly what was not run:

- every menu and readme, the sbom lists, `bash -n` of every script, pyflakes, `verify.sh`;
- the generated config with the program's own syntax checker when it is on the host (`ruby -c` for
  `gitlab.rb`), the vhost with `nginx -t` in a scratch config;
- the pinned download with a ranged request (`curl -r 0-1023 -L`), not the whole file.

**A vendor that supervises its own services** (GitLab's `gitlab-runsvdir.service`, runit inside)
gets *no* unit of ours: the CBS's unit list is empty (bisos.capability skips it), and the sbom runs
the vendor's own apply step (`gitlab-ctl reconfigure`). Write the vendor's config file *before*
installing the package when the package only creates one if absent. Give the vendor's accounts banna
numbers (a block, as qmail's and gitlab's) and create them first, so banna's check applies.

**Pinning a `.deb` from a vendor repository**: read version, filename and SHA-256 from the
repository's `Packages` index for the right Debian release; check that index's hash against the
`Release` file (say whether the `Release` signature was verified). Probe the download URL: GitLab's
index `Filename` (`pool/main/...`) is a 404; the working path carries the codename
(`pool/trixie/main/...`). Refuse another release or architecture in the install script.

## 8. The vhost

Always `proxy_pass http://<listenIp>:<port>` (loopback), not the `.here` address. Add what the
program needs: Server-Sent Events → `proxy_buffering off` (Kafbat); WebSocket → a location with
`Upgrade`/`Connection "upgrade"` (Grafana Live at `/api/live/`); uploads → `client_max_body_size`
(nginx's 1m default refuses them). Set the program's external URL (`--web.external-url`,
`root_url`) to `http://<name>.here/` so its links are right.

**Two programs on one fqdn** (pypiserver.here: the index and its browser): route by path, and when
one path belongs to both (`/` is pypiserver's upload `POST` and pypi-browser's home page `GET`), by
request method with a `map` at the top of the vhost file (it is included in nginx's http context)
--- not with `if`. Give the map variable a name carrying the fqdn's (`$pypiserverHereRoot`): map
names are global across vhosts. `proxy_pass http://$var;` with an IP:port value needs no resolver.
Test the generated file with `nginx -t` in a scratch config before materializing.

## 9. Generate the .cs files

The `.cs` files carry the full COMEEGA dblock chain. `tools/makeCs.py` assembles one from
bisos.kafka's `kafkaAdmin.cs` framework parts (header dblocks, csuList, main, endOfFile) plus a
parts file that defines `SUMMARY`, `DESCRIPTION`, `IMPORTS` and `BODY`:

```bash
python3 <skill>/tools/makeCs.py <name>Admin.cs <name>Admin <parts>.py     # run in py3/bin
```

`tools/csParts.py` gives `cmndHead(name)`, `EXAMPLES_HEAD`, `desc(text)` (the generated classHead
blocks, in their exact form) and `DRIFT_HELPERS` (`_exists`, `_reportKvDrift`, `_reportTextDrift`,
`_reportUnitDrift`, `_reportLink`). `tools/exampleAdminParts.py` and `exampleQuickParts.py` are
prometheus's, to copy; `tools/examplePipAdminParts.py` is pypiserver's (driftCheck of venv pins
instead of tarball links). The dblock bodies are what Blee would generate; a Blee dblock update later
refreshes them.

Parts files are Python source that writes Python source: `BODY` is an f-string, so `{{`/`}}` give a
literal brace and `{{{i}.x}}` gives `{i.x}` in the output. Do **not** use backslash escapes inside
it (`\"`, `\n`): they are consumed once and produce broken code. Quote with single quotes inside
double-quoted literals, and write multi-statement `python -c` as one line joined with `; `. Run
pyflakes on every generated file.

## 10. Install, verify read-only, materialize

```bash
# setup.py's scripts list is dblock-generated: until Blee regenerates it, list every
# bin/*.cs|.pcs|.spcs in generated form (see bisos-pip-setup-py)
/bisos/venv/py3/bisos3/bin/pip install --no-deps --no-build-isolation -e py3
cd /bisos/venv/py3/devbin && for f in <repo>/py3/bin/*; do ln -sfn "$f" "$(basename $f)"; done
```

`cbs_sbom` runs the sbom by bare name, so the devbin links are required. Then, without sudo:
each sbom's `-i readme` and `-i aptPkgs_list`, the bundle's `-i sbomSpecs_list`, the vhost's
`-i configFileStdout --cls=configFile_nginxVd`, `bash -n` of every generated script, every admin
Cmnd, and `cd py3/tests && bash -i ./verify.sh` (needs `lpDo`).

Materialize (needs sudo; ask unless the user granted it): `<name>-cbs.pcs -i cbs_materialize`.
(Base-only packages: §7c instead.) Check: units active; `id <acct>` shows the banna numbers;
`ss -ltn` shows loopback only; the
program's health endpoint; **its main use, end to end, as a user would** (pypiserver: anonymous
upload refused, twine upload with the login, pip install back, the file in the browser; then remove
the test data); `curl http://<name>.here/...` 200 (poll: a first start can take 30 s+
and nginx returns 502 meanwhile); the integration works end to end; `<name>Admin.cs -i
driftCheck` agrees everywhere. Run `cbs_materialize` again: rc 0, nothing re-downloaded.

## 11. Document

- Run `tools/orgTableAlign.py <file>` on every org file you write: it aligns every table by raw
  characters (leaving dblocks and example/src blocks alone) and lists every line over 105. On a
  file you did not write, use `--check` only: write mode re-pads tables other people own.
- Add the capability to the tables of `/bisos/git/bxRepos/bxGenesis/start/rawBisosCBMs/README.org`
  (packaged or planned; its gate, real home, minimal setting, measured footprint).
- Every line at 105 characters or less, tables included (the `readme-authorship` skill):
  absolute paths and long flags go in a list under the table, not in a cell.
- README.org sections: Overview; The BISOS <Name> Model (pattern, rawBisos stance, date
  materialized); [The Login]; What Gets Installed, and Where (table: what, where, owner);
  The 3 sboms; The systemd Unit(s); Listeners and Ports (banna names); Installation; Usage;
  Key Files; the standard BISOS/Blee/Support sections; Planned Improvements.
- The `_nodeBase_` panel: Overview + Entry points.
- AI-DevStatus.org and AI-WorkPlan.org of the new repo; banna's notes; an AI-Outputs entry for any
  framework finding.

Left for the user/Blee: dblock refresh (particulars, csInfo, setup.py, panel navigator), commits,
and planting the CBM leaf in `bro_rawBisos` (`sys/cbm/collective/hereWeb/<name>/`).

## Pitfalls already found

- **Runtime downloads.** Grafana fetches "preinstalled" plugins from grafana.com at every start,
  outside the sbom (`[plugins] preinstall_disabled = true`). Check every program for downloads,
  update checks and usage reporting at start, and turn them off in the generated config.
- **CLIs that want a desktop keychain.** gcx stores credentials in the OS keychain and refuses
  to fall back to a file (`GCX_KEYCHAIN=off` allows it). A BISOS host has no keychain service:
  run a usage tool's login once on the host, and carry the workaround in `<name>Info` (`gcxLogin`).
- **Login applied once.** Grafana applies `admin_password` only when it creates grafana.db.
  Changing the generator later does not change a live login.
- **750 config dirs.** When `/etc/<name>` is `root:<acct> 750` (it holds a password), the invoker
  cannot even `stat` the files: `Path.exists()` raises PermissionError. driftCheck uses `_exists`
  (falls back to `sudo test -e`); the sbom's tests use `sudo test`.
- **Planted files run at import.** A `.pcs` executes its seed when imported; to unit-test one of
  its functions, extract it with `ast` rather than importing the file.
- **Do not put `py3/` on PYTHONPATH**: its `bisos/__init__.py` shadows the bisos namespace.
- **Failures can look like success**: `g_csMain` exits 0 for a failed Cmnd, and
  `sbomSpecs_fullUpdate` carries on after a failed sub-sbom (both in AI-Outputs.org). Read the
  output of a materialization, not only its exit status.
- **Shared code is copied, not shared** (`tarballSetupScript`, `pipSetupScript`,
  `isolatedVenvSetupScript` in `devpiInfo.py`, the drift helpers): copy them verbatim so they stay
  identical until they move to a shared module (AI-Outputs.org).
- **`pkill -f <pattern>` can kill your own shell** when the pattern also appears in the command
  line that runs it. Stop scratch servers by PID.
- **A generator that writes Python must not nest the same triple quotes** it is written in. Keep an
  embedded script as a plain module-level string with placeholders and `.replace()` them.
- **The scaffold needs no commits**: `cbmPkgScaffold.sh` falls back to the model's files on disk when
  the model package is not committed yet.
- **Removing what you put in a shared venv.** If a package you installed into `asc` must leave it,
  first check that no other distribution there requires it (walk `importlib.metadata` requirements),
  then `pip uninstall` exactly the packages your install added, then `pip check`, then confirm the
  other capabilities' units still run.
