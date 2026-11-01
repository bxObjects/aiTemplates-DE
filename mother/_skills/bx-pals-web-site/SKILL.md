---
name: bx-pals-web-site
description: Use when a site is, or is to become, a BISOS PALS (Possession Assertable Libre Service) — a directory with `uri/here/value` and a `cbm/` of symlinks to bisos.pals's generic `pals-cbs.spcs` / `pals-assemble.cs` / `pals-here-dns.spcs` / `pals-wvd.spcs` — or when a `.here` name is on a `127.0.55.x` address, is in `/bisos/var/palsHere/uri.list` or the `palsHere` dblock of `/etc/hosts`, or is not in banna. Covers telling a PALS from a banna site, the site's files, serving it with `pals-assemble.cs -i fullUpdate`, verifying it, registering it with `palsOfSys.cs` so the CBM walk materializes it, and retiring a name. The Astro site itself (content tree, `site/`) is astro-site-authorship; a banna site is astro-site-authorship's banna steps.
---

# A PALS Site: Named, Served and Planted by bisos.pals

The shape, before any step:

```
<palsSite>/                       any directory, in any repo (the PALS-BXO)
   ├─ uri/here/value              the fqdn, e.g. libre-halaal.org.here — this file makes it a PALS
   ├─ cbm/pals-cbs.spcs        ─┐
   ├─ cbm/pals-assemble.cs      │ symlinks to /bisos/git/bxRepos/bisos-pip/pals/py3/bin/<same>;
   ├─ cbm/pals-here-dns.spcs    │ each finds its PALS as the nearest directory above it with uri/here/value
   ├─ cbm/pals-wvd.spcs        ─┘ (the path is never resolved)
   ├─ astroProc.spcs              fqdn = the same name; no banna, no devPortNu
   ├─ content/tree/, site/        the Astro site (astro-site-authorship)
   │
   pals-assemble.cs -i fullUpdate:  siteBuild → hereDns (palsHere: 127.0.55.x in uri.list, /etc/hosts)
                                              → webVirtDom (nginx vhost: root <palsSite>/site/dist)
   │
<palsBxo>/sys/cbm/<cbmName>/      declared by palsOfSys.cs palsCbmAdd (capabilityType, cbsSpec relative)
/bisos/platform/sys/cbm/pals/<palsBxo>/<cbmName>/cbmProc.spcs   planted by palsLeavesPlant; walked
```

The authority is the bisos.pals `README.org` (`/bisos/git/bxRepos/bisos-pip/pals/README.org`): read its
"PALS on a Platform", "PALS .here Names" and "A PALS Site's cbm/" sections before changing anything here.
The first PALS site is libre-halaal.org.here
(`bro_rawBisos/bro_rawBisosPals/bySmb/libreHalaalFoundation/web/astro`).

## 0. Is It a PALS? Settle With the User First

- **PALS or banna.** A PALS has `uri/here/value` or a `cbm/` of `pals-*` symlinks. Look with `ls -la`
  — `find -type f` skips symlinks and shows `cbm/` as empty. Platform services (Airflow, Grafana, Kafka,
  the starter) are banna; a site someone owns (a foundation, a project) is a PALS. **Never add a PALS to
  banna** and never look its name up in `/etc/hosts`'s banna block.
- **The fqdn.** It is `uri/here/value`, which may differ from the repo's or the directory's name (the
  user may write it in another case; `.here` names are case-insensitive, keep the file's).
- **The PALS-BXO** that owns it, for registration (step 4): the repository the site lives in. Its
  `sys/cbm/` is written into that repository, so ask before declaring.

## 1. The Site's Files

```bash
mkdir -p <palsSite>/uri/here <palsSite>/cbm
echo "<fqdn>" > <palsSite>/uri/here/value
cd <palsSite>/cbm
for f in pals-cbs.spcs pals-assemble.cs pals-here-dns.spcs pals-wvd.spcs; do
    ln -s /bisos/git/bxRepos/bisos-pip/pals/py3/bin/$f $f
done
```

No per-site cbm files: do not copy a banna site's `<name>-cbs.pcs` / `-wvd.pcs` / `-here-dns.pcs`.

## 2. astroProc.spcs Without banna

Copy the starter's, then remove the banna import and `bannaPortNu()`. `devPortNu` is optional
(`astro dev` falls back to 4321):

```python
fqdn = "<fqdn>"          # the same as uri/here/value

astroProc_seedInfo.setup(
    fqdn=fqdn,
)
```

Fix the docstring's site name too: a copied `astroProc.spcs` keeps the source site's name.

## 3. Serve It

```bash
cd <palsSite> && ./astroProc.spcs -i contentTreeValidate content/tree    # path relative to <palsSite>
cd <palsSite>/cbm && ./pals-assemble.cs -i fullUpdate    # siteBuild, hereDns, webVirtDom (sudo inside)
cd <palsSite> && ./astroProc.spcs -i siteVerify          # 200 at /, the site's 404 for a missing page
```

`fullUpdate` assigns the address (the next `127.0.55.x`, recorded in `/bisos/var/palsHere/uri.list`),
fills the `palsHere` dblock of `/etc/hosts` (backed up as `/etc/hosts.<date>`), writes
`/etc/nginx/sites-available/<fqdn>`, links it into `sites-enabled` and reloads nginx. Nothing else is
needed for the name: do not edit `/etc/hosts` or `uri.list` by hand.

Then look at it: `google-chrome --headless=new --no-sandbox --screenshot=<file>.png
--window-size=1200,900 http://<fqdn>/`, or ask the user to.

## 4. Register It, So the CBM Walk Rebuilds It

Until this step the site is served but unknown to the walk: rerun `fullUpdate` by hand after changes.

```bash
palsOfSys.cs -i palsAdd <palsBxoPath>                      # once per PALS-BXO; origin: its git remote
palsOfSys.cs -i palsCbmAdd <palsBxo> <cbmName> <cbsRelPath> # cbsRelPath: <palsSite>/cbm/pals-cbs.spcs,
                                                            # relative to the PALS-BXO; hereWeb default
palsOfSys.cs -i palsLeavesPlant                             # gate: available
palsOfSys.cs -i palsList
cd /bisos/platform/sys/cbm/pals/<palsBxo>/<cbmName> && ./cbmProc.spcs -i cbm_enable
cd /bisos/platform/sys/cbm/pals && ./ftoBranchProc.spcs -i fto_forwardToLeaves --cmndName=cbm_materialize
```

`palsCbmAdd` writes `<palsBxo>/sys/cbm/<cbmName>/` into the PALS-BXO's repository (declarations travel
with the repo); gates and statuses stay on the platform. Planting never overwrites a gate or a status.

## 5. Retire a Name

Comment its line out in `/bisos/var/palsHere/uri.list` — never delete it: an address is assigned once
and never reused. Then disable the vhost and the leaf (`cbm-authorship`).

## 6. Document

The site's `AI-DevStatus.org`: its fqdn and address, whether it is registered (step 4) or served by
hand, and the PALS-BXO. `README.org` (`readme-authorship`).

## Pitfalls

- **`cbm/` looks empty**: `find -type f` skips symlinks; use `ls -la`.
- **The leaf runs the generic file and finds no PALS**: a CBS path was resolved through its symlink
  (fixed 2026-10-19 in `bisos.capability`'s `resolveCbsSpec`, `.absolute()` not `.resolve()`). A
  `cbmProc.status` saying `ok` is not proof: the PyCS main exits 0 when a Cmnd fails; check the site.
- **`astroProc.spcs` asks banna for a port that does not exist**: it was copied from a banna site
  (libre-halaal.org.here's still is). Remove the banna lookup (step 2).
- **`contentTreeValidate tree: not a directory`**: the path is relative to the site's directory
  (`content/tree`), not to `content/`.
- **The name does not resolve**: `fullUpdate` not run, or the `palsHere` dblock missing from
  `/etc/hosts` (`palsHereInfo.cs -i palsForEtcHosts` shows what it should hold).
- **Stale pages or images from an earlier copy**: `site/public/` is placed by `files` nodes and is not
  rebuilt; clear it (and `site/dist/`) when replacing a site.
