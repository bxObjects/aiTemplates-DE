---
name: astro-site-authorship
description: Use when creating a new BISOS static site with Astro, or migrating one — from the astro-starter-bystar starter, a ByStar Plone 3 site's ContentTree, or an older Gatsby site — into the common structure (`astroProc.spcs`, `cbm/` with `<name>-cbs.pcs` / `-assemble.cs` / `-wvd.pcs` / `-here-dns.pcs`, `content/tree/`, `content/bin/`, `site/`), served by nginx as `http://<name>.here` with a CBM leaf. Also when adding pages to such a site — content tree nodes (folder, page, pageLcnt built from LaTeX by HeVeA, files, nodesOrdered, contentLang for RTL) or data-driven pages from `content/bin/` scripts writing `content/data/*.json` — or when a `.here` Astro site answers 404, shows stale content, or a right-to-left page does not mirror. Covers banna registrations, copying the starter, astroProc.spcs, the capability files, the leaf and walk order, build and verification, and pitfalls. A PALS site (`uri/here/value`, `cbm/pals-*` symlinks, a `127.0.55.x` name) takes its pages from here but its naming, serving and planting from bx-pals-web-site. Not for a CBM package that runs a program (that is cbm-package-authorship).
---

# Creating a BISOS Static Site (Astro, Content Tree)

The shape, before any step:

```
banna: <name> port + hereIp, <name>_dev port + hereIp
   │
<siteBase>/                    copied from astro-starter-bystar
   ├─ astroProc.spcs           bisos.webCap's astroProc seed: fqdn, dev port
   ├─ cbm/                     <name>-cbs.pcs (no sbom, no units, assemble only)
   │                           <name>-assemble.cs: siteBuild (./astroProc.spcs -i siteBuild) → hereDns → webVirtDom
   │                           <name>-wvd.pcs (root site/dist, 404), <name>-here-dns.pcs
   ├─ content/tree/            the pages: nodes with parameter files (the Plone 3 ContentTree model)
   ├─ content/bin/* ──write──> content/data/<x>.json          (optional: data-driven pages)
   └─ site/                    Astro: contentTree.mjs reader, Plone-like layout, [...slug].astro
   │
sys/cbm/<realm>/hereWeb/<name>/cbmProc.spcs ──points at──> <siteBase>/cbm/<name>-cbs.pcs
```

Orientation (the model, conventions, why a snapshot) is in the `astro-site` activity's
`AI-Activity.org`. The starter is `<starter>` = `/bisos/git/bxRepos/bisos-web/astro-starter-bystar`;
the example of data-driven pages is platform.here, `/bisos/platform/web/astro`.

## 0. Settle With the User First

- **banna or PALS.** A directory with `uri/here/value`, or a `cbm/` of `pals-*` symlinks (look with
  `ls -la`: `find -type f` skips symlinks), is a PALS: load `bx-pals-web-site` and follow it for naming,
  `astroProc.spcs`, serving and planting — **skip steps 1, 2's `cbm/` and `astroProc.spcs` bullets, and
  5 here**; steps 2's copy, 3, 4 and 4a apply as they are. Platform services are banna; a site someone
  owns (a foundation, a project) is a PALS. Ask when unsure.
- The name, so the fqdn (`<name>.here`), and where the site lives: its own repo (`initiate
  --activity=astro-site`) or a directory of a BXO (`initiateSub --activity=astro-site`).
- Where its pages come from: a new tree, a Plone 3 `ContentTree/` (which site), or data scripts.
- Its languages; whether some subtrees are right-to-left (`contentLang`).
- Its realm (usually `collective`) and its place in the walk.

## 1. banna Registrations (banna Sites Only)

Load `banna-lookup`. In `bisos-pip/banna/py3/bisos/banna/tcpPorts.py` add `<name>` (the next 240NN,
the next free `hereIp`) and `<name>_dev` (250NN, its own `hereIp`), as `astroStarter` /
`astroStarter_dev` are. Check: `python -c "from bisos.banna import tcpPorts as t; print(t.hereIpOf('<name>'))"`.
Note it in banna's `AI-DevStatus.org`.

## 2. Copy the Starter

```bash
mkdir -p <siteBase> && cd <starter>
cp -r .gitignore README.org astroProc.spcs cbm content site <siteBase>/
cd <siteBase> && rm -rf site/node_modules site/dist site/.astro site/public   # if present
```

Then, in `<siteBase>`:
- `astroProc.spcs`: `fqdn = "<name>.here"`, `bannaPortNu("<name>_dev")`, the docstring. (A PALS: no
  banna, no `devPortNu` — `bx-pals-web-site` step 2.)
- `cbm/`: rename `astroStarter-*` to `<name>-*`, and `astroStarter` / `astroStarter.here` / the path
  of the starter inside them; `cbm/<name>-wvd.pcs`'s `rootBaseDir` is the stable path of `site/dist`
  (`/bisos/platform/web/...` in bro_rawBisos, `/bisos/git/bxRepos/...` for a repo); `cbm/<name>-cbs.pcs`'s
  `assemble=` the stable path of `cbm/<name>-assemble.cs`; `cbm/<name>-here-dns.pcs`'s fqdn.
- `site/package.json`: `name`, `description`, `repository`. Keep `site/package-lock.json` (Astro pinned).
- `README.org`: rewrite for the site (`readme-authorship`).

## 3. The Content Tree

Either import a Plone 3 site:

```bash
mv content/tree content/tree.starter     # or remove it
./astroProc.spcs -i contentTreePloneImport <plone3Site>/ContentTree content/tree
```

The import copies the parameter files and bodies as they are, drops the per-node `plone3Proc.sh` /
`_treeProc_`, and turns each folder's `nodesOrdered=` into a `nodesOrdered` file. Then write the root's
`siteTitle`, `siteTagline`, `defaultPage` and `nodesOrdered` (the tabs; Plone ordered them by the order of
its update functions, not in a file), and `contentLang` where a subtree is Persian or French.

Or write nodes (the starter's tree shows each kind):

```
<node>/_tree_            node | leaf
<node>/objectType        folder | page | pageLcnt | files | custom
<node>/folderTitle       (folder)        <page>/pageTitle, pageDescription
<node>/pubState          publish         <node>/excludeFromNav   false | true
<folder>/index_html/     the folder's page (objectType page or pageLcnt)
<page>/contentBody.html  the body (HTML; a fragment or a whole document)
<pageLcnt>/webPageLcnt/bodyWebPage.tex   LaTeX; built into contentBody.html by HeVeA
<files>/filesList, siteFolder, and the files
<folder>/nodesOrdered    children in navigation order;  <folder>/contentLang  fa | fr | en ...
```

Check with `./astroProc.spcs -i contentTreeValidate content/tree` and `-i contentTreeList content/tree`.
Persian inside LaTeX: `\begin{fa}...\end{fa}` (inline) and `\begin{faPar}...\end{faPar}`; they come out as
`lang="fa" dir="rtl"`.

## 4. Data-Driven Pages (Optional)

An executable in `content/bin/` (`#!/usr/bin/env python`, read-only) writes
`content/data/<x>.json` with `generatedAt` and `host`; `contentBuild` runs every one, in name order.
Pages in `site/src/pages/` read the JSON at build time and win over the tree's catch-all page:

```js
// site/src/lib/content.mjs (as platform.here's)
const file = path.resolve(process.cwd(), "../content/data/<x>.json")
if (!fs.existsSync(file)) throw new Error(`${file} is missing: run content/bin/<x>.py first`)
export const data = JSON.parse(fs.readFileSync(file, "utf8"))
```

```astro
---
// site/src/pages/<section>/[id].astro
import { data } from "../../lib/content.mjs"
export function getStaticPaths() {
  return data.items.map((item) => ({ params: { id: item.id }, props: { item } }))
}
const { item } = Astro.props
---
```

Models: platform.here's `content/bin/platformCapabilities.py` (walks `sys/cbm`, joins banna, probes the
`.here` URLs) and `platformLayers.py` (`facter --json` plus checks).

## 4a. A React Application as an Island (Optional)

The worked example is `bisos-web/csPlayer-webUi` (webCliGui); its README lists each step. In short:

1. An `app` node in the tree for its tab: `_tree_` leaf, `objectType` `app`, `folderTitle`, `pageTitle`,
   `pubState`.
2. `site/package.json`: `@astrojs/react`, React (the application's major version), the application
   (`"<app>": "file:<its repo>"` while developed alongside; a pinned git reference later) and its runtime
   dependencies; Tailwind v4's `@tailwindcss/vite` if it uses Tailwind. `npm install` once.
3. `astro.config.mjs`: `integrations: [react()]`; `vite.plugins: [tailwindcss()]`; its path aliases;
   `resolve.preserveSymlinks: true` and `resolve.dedupe: ["react", "react-dom"]`; an alias adding `?url`
   to its image imports if it was built with webpack's file-loader.
4. `site/src/apps/<app>/<App>.tsx` (its root component, as its own `main.tsx` renders it) and a stylesheet
   importing its CSS plus `@source "<path to its src>"` (Tailwind skips `node_modules`).
5. `site/src/pages/<path>.astro`: `<TreeLayout node={nodeAt("/<path>/")}><App client:only="react" /></TreeLayout>`.
6. Build, then look at it with `--run-all-compositor-stages-before-draw --virtual-time-budget=20000`
   (transitions are otherwise caught half way). Its backend (e.g. `/api/`) is a separate step: an nginx
   `location` in `cbm/<name>-wvd.pcs` proxying to it.

## 5. Build, Serve, Plant (banna Sites; a PALS: `bx-pals-web-site` steps 3–4)

```bash
cd <siteBase>/site && npm install && cd ..      # only when package.json changed; commit the lock file
./astroProc.spcs -i siteBuild                   # pageLcnt bodies, files, content/bin, npm ci, astro build
(cd site && npx astro dev --host 127.0.0.1 --port <dev port>)   # while writing
./cbm/<name>-assemble.cs -i fullUpdate          # build, /etc/hosts entry, nginx vhost (sudo)
./astroProc.spcs -i siteVerify / /<page>/       # 200s, and the site's 404 for a missing page
```

Plant the leaf (load `cbm-authorship`): `sys/cbm/collective/hereWeb/<name>/cbmProc.spcs` with
`capabilityName="<name>"` and `cbsSpec="<stable>/cbm/<name>-cbs.pcs"`, `cbmProc.control` (`enabled`), an
empty `cbmProc.status`; add `<name>` to `branchesOrdered` after `nginx`, `reactPlus` and whatever the site
reports on. Then `./cbmProc.spcs -i cbm_materialize` there: `cbmProc.status` must end with
`ran: cbs_materialize ok`.

Look at it: `google-chrome --headless=new --no-sandbox --screenshot=<file>.png --window-size=1200,900
http://<name>.here/<page>/`, at desktop and phone (400px) widths, and an RTL page.

## 6. Document

`<siteBase>/README.org`: what the site shows, its tree or data, the structure, usage, known limits
(lines ≤105, tables included: `orgTableAlign.py --check` in `cbm-package-authorship/tools/`).
`content/README.org`: its content scripts. The site's AI files; banna's `AI-DevStatus.org`; the
rawBisosCBMs README's tables when the leaf is in the rawBisosCbm set.

## Pitfalls

- **`npm ci` fails with EUSAGE**: no `site/package-lock.json`; `npm install` once and commit it.
- **"See<a>Capabilities</a>" without a space**: `compressHTML` must be `false` in `astro.config.mjs`.
- **A page without its body** (an empty article): the body is not `contentBody.html` — the readers also
  take `content.html` and `contentPreface.html`; anything else is not read.
- **An RTL page does not mirror**: `contentLang` missing on its folder, or CSS with physical properties
  (`left`, `margin-left`) instead of logical ones; the site's English chrome on it needs `dir="ltr"`.
- **"This document was translated from LaTeX by HeVeA" on a page**: the body was built outside
  `contentTree_csu` (its `.hva` sets `\footerfalse`); rebuild with `contentBuild`.
- **The site answers 404 at `/`**: `site/dist/` not built, the vhost's `root` not the stable path to it,
  or the tree's root has no `defaultPage`.
- **`astroProc.spcs` lists Cmnds but they act on the wrong directory**: an old `siteProc.spcs` or a
  reactProc seed; astroProc works from the planted file's directory.
- **An island's image shows `[object Object]`**: an image import gives an object in Astro; alias `?url`.
- **An island's Tailwind classes are missing**: its source is under `node_modules`; add `@source`.
- **Two Reacts ("Invalid hook call")**: `resolve.dedupe` and `preserveSymlinks` in `astro.config.mjs`.
- **`cbm/` looks empty, or a site looks like it needs banna**: `find -type f` skips symlinks; a `cbm/`
  of `pals-*` symlinks is a PALS (`bx-pals-web-site`).
- **A copied `astroProc.spcs` names another site**: it keeps the source's fqdn, docstring and banna dev
  port; change all three (a PALS drops the banna lookup).
- **`contentTreeValidate tree: not a directory`**: the path is relative to the site's directory,
  `content/tree`.
- **The starter copied over an old site leaves stale files**: `site/public/` (placed by `files` nodes)
  and `site/dist/` are not cleared by `cp`; remove them before building.
- **Copying the Gatsby starter's CBS files**: its `hereDns` called `csPlayerUi-here-dns.pcs` and its dblock
  text said `siteRegistrars`; start from `astro-starter-bystar`.
