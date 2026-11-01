---
name: bs-pals-web-edit
description: Use when improving a PALS web site that already exists and is served — a directory with `uri/here/value`, `astroProc.spcs`, `content/tree/` and `site/` — by changing its look (header, site title, colours, fonts, alignment, the tabs, the footer) or its text and pages (the title or tagline, a page's body, adding or reordering a tab, a link tab). Also when the user asks "how do I change X on the site myself", or a CSS change does not show after a rebuild. Covers which file owns what (content tree parameters, `content/siteStyle/logo.html`, the site's own `site/src/styles/local.css` loaded after the starter's `site.css`, the layouts), the edit / rebuild / verify / look loop with `astroProc.spcs -i siteBuild`, and CSS recipes. Creating a site, a Plone 3 or Gatsby migration and banna sites are astro-site-authorship; naming, serving and registering a PALS are bx-pals-web-site.
---

# Editing a PALS Web Site: Look and Content

The site is already named and served (`bx-pals-web-site`). An edit is: change the one file that owns
the thing, rebuild, verify, look.

```
<palsSite>/
   content/tree/                  WHAT the site says: pages, tabs, titles (engine-neutral)
      siteTitle, siteTagline        the header's title and the line under it (root only)
      nodesOrdered                  the tabs, in order
      <node>/contentBody.html       a page's body;  <node>/pageTitle, pageDescription
   content/siteStyle/logo.html    optional: an HTML fragment that REPLACES the title block
   site/src/styles/site.css       the starter's look — leave as the starter has it
   site/src/styles/local.css      THIS site's look — overrides, loaded after site.css
   site/src/layouts/TreeLayout.astro   the page's structure (header, tabs, left tree, footer)
   site/dist/                     the build; nginx serves it as is (vhost root)
```

## 1. Find the File That Owns It

| To change                                      | Edit                                                  |
|------------------------------------------------|-------------------------------------------------------|
| The title or tagline text                      | `content/tree/siteTitle`, `content/tree/siteTagline`  |
| A page's text, heading, summary                | `content/tree/<node>/contentBody.html`, `pageTitle`, `pageDescription` |
| Which tabs, their order, a link tab            | `content/tree/nodesOrdered`; a node with `objectType` `link` and `linkUrl` (astro-site-authorship, "The Content Tree") |
| Colour, size, alignment, slant, spacing        | `site/src/styles/local.css`                           |
| A header that is more than a title (a logo, an image, a layout of its own) | `content/siteStyle/logo.html` (its `<style>` goes into the page) |
| What the header, tabs or footer contain        | `site/src/layouts/TreeLayout.astro`                   |

To find the rule behind something on the page, find its class in the layout and its rule in the CSS:

```bash
cd <palsSite>
grep -n 'class="' site/src/layouts/TreeLayout.astro
grep -n '\.siteTitle\|\.titleBlock' site/src/styles/*.css
```

## 2. Put the Look in local.css, Not in site.css

`site.css` is the starter's (astro-starter-bystar); keeping it unchanged keeps the site comparable with
the starter and lets a newer one be copied in. The site's own rules go into `site/src/styles/local.css`,
imported right after it, so with the same selector the later rule wins:

```js
// site/src/layouts/TreeLayout.astro, frontmatter
import "../styles/site.css"
import "../styles/local.css"                       // this site's own look; after site.css so it wins
```

If the site has no `local.css` yet (the starter does not ship one), create it and add that import line.
Use the same selectors as `site.css` and override only the properties that change. Add a variable of
your own rather than changing one of the starter's: `--navy` colours the title *and* every page heading.

## 3. Rebuild, Verify, Look

```bash
cd <palsSite> && ./astroProc.spcs -i siteBuild     # contentBuild, npm ci, astro build -> site/dist/
cd <palsSite> && ./astroProc.spcs -i siteVerify    # 200 at /, the site's 404 for a missing page
```

`siteBuild` is enough for content and look: nginx serves `site/dist/` directly, so a rebuild is live at
once. `cbm/pals-assemble.cs -i fullUpdate` (sudo inside) is only needed when the name, the address or
the vhost changes.

Check that the new rule is served (Astro bundles the CSS into `/_astro/*.css`, minified), then look:

```bash
curl -s http://<fqdn>/ | grep -o 'font-style:italic'          # any distinctive part of the new rule
google-chrome --headless=new --no-sandbox --window-size=1200,500 \
    --screenshot=/tmp/<fqdn>.png http://<fqdn>/
```

In a browser that had the page open, reload (Ctrl+Shift+R) if it looks unchanged.

## CSS Recipes for the Header

From `site.css`: `.siteHeader` > `.titleBlock` > `a.siteTitle` and the tagline `.titleBlock p`;
`.siteActions` (Site Map) is absolutely positioned, so centering the title block does not move it.

```css
:root { --titleBlue: #003399; --titleBg: #eef4fb; }     /* a dark blue and a pale blue of the site's own */

.titleBlock { text-align: center; }                     /* centers the title and the tagline */
.titleBlock { background: var(--titleBg); }             /* the title band's background, not the tabs' */
.siteTitle  { color: var(--titleBlue); font-style: italic; }   /* coloured and slanted */
.siteTitle  { font-size: 2.2rem; letter-spacing: 0.02em; }     /* bigger, a little spaced */
.titleBlock p { color: var(--titleBlue); }              /* the tagline in the same colour */
.siteHeader { border-block-end-color: var(--titleBlue); }      /* the rule under the tabs */
.tabs a.selected { background: var(--titleBlue); }      /* the selected tab */
```

Use logical properties (`inline-start`, `border-inline-end`, `text-align: start`), not left / right,
so a right-to-left page still mirrors. `text-align: center` is the same in both directions.

## The Tabs: Boxed (Folder) Tabs

Since 2026-10-21 the starter's `site.css` draws each top tab as its own box, so a label of several
words reads as one tab (chosen over divider lines, a separator character and underlines). A site
copied before then has flat tabs; bring it up with the same rule:

```css
:root { --tabBox: #c8d6df; }                      /* an unselected tab's box, on the --tabs bar */
.tabs { padding-block-start: 0.4rem; }
.tabGroup { gap: 0.3rem; }
.tabs a { white-space: nowrap; background: var(--tabBox); border-radius: 6px 6px 0 0; }
```

An older site with no `.tabGroup` (tabs directly in `.tabs`) puts the gap on `.tabs`. To recolour the
boxes for a site or an organization, override `.tabs a`, `.tabs a:hover` and `.tabs a.selected` in a
later stylesheet; keep `nowrap` so a two-word label never breaks.

## Removing a Part of the Page (the Footer, the Site Map Link)

Hide it in `local.css`; the layout stays the starter's, and deleting the rule brings it back:

```css
.siteFooter  { display: none; }     /* the footer ("Built with Astro ... astro-starter-bystar") */
.siteActions { display: none; }     /* the Site Map link at the header's top corner */
```

The markup is still in the page, only not shown. To have it out of the HTML as well, delete the element
from `site/src/layouts/TreeLayout.astro` instead; the site's layout then differs from the starter's.

## Adding a Tab of Generated Pages (Tables From a Script)

For pages whose numbers come from somewhere (a database, logs, a service), refreshed by rebuilding:

```
content/bin/<x>.py                 read-only; writes content/data/<x>.json (with a generatedAt stamp)
content/tree/<tab>/                app nodes: the tab, its titles, its left tree; no bodies
   objectType=app, _tree_=node, nodesOrdered    <tab>/<branch>/ (app, node), <tab>/<branch>/<leaf>/ (app, leaf)
site/src/lib/<x>.mjs               reads the JSON; throws, naming the script, when it is missing
site/src/pages/<tab>/[...sub].astro   ONE fixed page for every node under /<tab>/
```

- **`app` nodes may have children**, so a tab with branches and leaves is all `app` nodes, and
  `contentTreeValidate` accepts it. The tree's catch-all page skips `app` nodes, so the fixed page owns
  those paths with no route collision. Add `<tab>` to the root's `nodesOrdered` where the tab goes.
- **The fixed page** takes its paths from the tree and renders inside the site's layout; in `app` mode
  the layout shows only the slot, so the page writes its own `<h1>` and description:

  ```astro
  ---
  import TreeLayout from "../../layouts/TreeLayout.astro"
  import { nodeAt } from "../../lib/contentTree.mjs"
  export function getStaticPaths() {
    const top = nodeAt("/<tab>/")
    return [top, ...top.children, ...top.children.flatMap((c) => c.children)].map((node) => ({
      params: { sub: node.urlPath.replace(/^\/<tab>\/|\/$/g, "") || undefined }, props: { node } }))
  }
  const { node } = Astro.props
  ---
  <TreeLayout node={node}>
    <h1>{node.page.title}</h1>
    <p class="description">{node.page.description}</p>
    <!-- tables from the JSON, chosen by Astro.params.sub -->
  </TreeLayout>
  ```
- **The script runs on every build**: `siteBuild`'s contentBuild runs each executable in `content/bin/`
  (as the account that builds), so "refresh the pages" is just `./astroProc.spcs -i siteBuild`; a
  scheduler later runs that same command. Show the snapshot's `generatedAt` on the page.
- **Data only another account may read** (a service's database): have the script run that one query as
  the service account, `sudo -n -u <serviceUser> psql ...` (passwordless sudo, `-n` so it fails rather
  than prompts), and skip `sudo` when it already runs as that account. Keep the script standard-library
  only (`psql` output with `-A -t -F '|'`), so it needs no venv.
- **Code shared by several scripts** goes in a *non-executable* module beside them
  (`content/bin/<helper>.py`, mode 644): contentBuild runs only the executables, and a script imports
  the module from its own directory (`from <helper> import ...`). `__pycache__/` is git-ignored.
- **A second tab** of generated pages is the same again: its own script, JSON, loader, tree nodes and
  `site/src/pages/<tab2>/[...sub].astro`; each loader refuses to build without its own JSON.
- `content/data/*` is not under git (the starter's `.gitignore`): the JSON is per host and per build.
- Right-align number columns: `td.num { text-align: end; font-variant-numeric: tabular-nums; }`.

## Pitfalls

- **The change does not show**: `local.css` is not imported, or is imported before `site.css`; or
  `site.css` has a more specific selector for it; or the build was not rerun; or the browser cached it.
  The `curl | grep` above tells the build from the browser.
- **Every page heading changed colour too**: a starter variable (`--navy`, `--blue`) was redefined.
  Use a new variable.
- **`logo.html` hides the title**: when `content/siteStyle/logo.html` exists it replaces the whole title
  block, so title rules in CSS do nothing.
- **Hand edits in `site/dist/`** are lost at the next build; edit the sources.
