---
name: blee-pkg-authorship
description: Use when creating or changing a Blee package (blee-pkg) --- a git repo of elisp under `/bisos/git/bxRepos/blee/<pkg>/` (github `bx-blee/<pkg>`) with `b:<pkg>::pkg.el`, `b:<prefix>.el` modules, `b:<prefix>:menu.el` and `package.recipe` --- or its adoption into Blee (`blee/env3/plus/bnpa:<pkg>.el`, `plus-init.el`), or moving code into one from a `bcpg:<x>Plus.el`. Also when writing the elisp layer over a bisos-pip `.cs` program (`call-process`, `EH_Problem`), an easymenu menu or a transient for a blee-pkg, magit integration (keys in `magit-mode-map`, `magit-dispatch`), or when testing a blee-pkg (batch Emacs with stubs, or a fresh Blee started for the test), and when committing a change that spans the bisos-pip package, the blee-pkg and env3. Covers the structure, the elisp-over-CSXU layering and the shared runner, COMEEGA definitions written by hand, menus built once (not from menu-bar-update-hook), transients, bnpa adoption, the two kinds of test, and the commit order.
---

# Authoring a Blee Package

```
bisos-pip/<x>  py3/bin/<layer>.cs  ->  py3/bisos/<x>/<layer>_csu.py     the logic (Python first)
      ^ call-process, from ~/
blee/<pkg>     b:<layer>.el (one per CSXU)  b:<prefix>:menu.el  b:<pkg>::pkg.el   thin elisp
      ^ straight (:local-repo in dev mode, else github bx-blee/<pkg>)
blee/env3      plus/bnpa:<pkg>.el  (install|update, config|main)  <- plus/plus-init.el
```

The blee-pkg AI-Activity.org (always loaded in such a repo) has the naming rules and conventions;
this skill has the procedures. The worked example throughout is `blee/vscode-claude` (over
`bisos.vscodeClaude`'s `vscode.cs` and `vscodeClaude.cs`). Load `comeega-authorship` for the file
format and `writing-cs-commands` for the Python side.

## 1. Lay out the package

```
<pkg>/
  README.org  package.recipe  b:<pkg>::pkg.el  b:<prefix>.el ...  b:<prefix>:menu.el
  dblock-<pkg>.el (optional)  images/<pkg>-graphviz.pcs (optional)  AI-*.org CLAUDE.md .claude/
```

- `package.recipe`: `(<pkg> :fetcher github :repo "bx-blee/<pkg>" :files ("*.el"))`.
- `b:<pkg>::pkg.el`: `(require ...)` of each module, a `defgroup`, `(provide 'b:<pkg>::pkg)`.
- Start from a sibling (`aiplus`, `vscode-claude`), not from scratch: copy the file headers
  (`b:elisp:file/copyLeftPlus`, `…/authors`, `…/orgTopControls`, the folding sections, `…/provide`,
  `…/endOf`).

## 2. One elisp layer per CSXU, through one runner

Give each layer of the Python side its own small CSXU and each CSXU its own elisp module:
`b:vscode.el` over `vscode.cs`, `b:vscode:claude.el` over `vscodeClaude.cs` (which builds on the
first). Put the logic in Python; the elisp builds arguments, runs, shows.

One runner per package (vscode-claude's `b:vscode:program/run` and `…/runOrError`):

```elisp
(let ((default-directory (expand-file-name "~/"))   ; a local process, also from a TRAMP buffer
      $status)
  (with-current-buffer (get-buffer-create <outBuffer) (erase-buffer))
  (setq $status (apply #'call-process <program nil <outBuffer nil <args))
  ;; A refused PyCS Cmnd still exits 0: its usage error (EH_Problem) is in the output.
  (and (eql $status 0)
       (not (with-current-buffer <outBuffer
              (save-excursion (goto-char (point-min)) (search-forward "EH_Problem" nil t))))))
```

On failure, `display-buffer` the output and `user-error`. When parsing the output, drop the
framework's `ALERT:` lines. Pass data as arguments; for elisp that Python must evaluate in Emacs
(`emacsclient --eval`), quote strings with JSON's string syntax (`json.dumps(text,
ensure_ascii=True)`), which elisp reads.

## 2a. Keep the layers honest

A package of several layers (blee/vscode-claude has five: AI-Activity, VS Code, Emacs <-> VS Code,
Emacs <-> VS Code Claude, + AI-Activity) keeps each in its own file or CSU, and *a lower layer never
names an upper one*. Where the lower layer needs what only an upper one knows, invert it:

| The lower layer declares                | The upper layer supplies                           |
|-----------------------------------------+----------------------------------------------------|
| a function variable (=…-function=)      | its function (=setq= it), e.g. =…:baseDir-function= |
| an abnormal hook (=…:event-hook=)       | its handlers, with =add-hook=                      |
| a transient prefix                      | an entry: =(transient-append-suffix 'lower "e" …)= |
| a setting (=aiActivity.cs= userConfig)  | its value (=gitOpener=)                            |
| an argument in a command's prompt       | the name (=register=<function>=)                   |

Test it: batch-load the lower layer alone and check it defines nothing of the upper one.

## 3. Write definitions the COMEEGA way, by hand when Blee is not at hand

Every function is a `b:elisp:defs/cl-defun` dblock. Without Blee, write the generated part in its
exact shape and say that it needs regenerating (`F7 d b` in Blee):

```elisp
;;;#+BEGIN:  b:elisp:defs/cl-defun :defName "b:pkg:area/verb" :advice ()
(orgCmntBegin "
*  _[[elisp:(blee:menu-sel:outline:popupMenu)][±]]_ _[[elisp:(blee:menu-sel:navigation:popupMenu)][Ξ]]_ [[elisp:(outline-show-branches+toggle)][|=]] [[elisp:(bx:orgm:indirectBufOther)][|>]] *[[elisp:(blee:ppmm:org-mode-toggle)][|N]]*  cl-defun   [[elisp:(outline-show-subtree+toggle)][||]]  <<b:pkg:area/verb>>  --  -- One line on what it does.  [[elisp:(org-cycle)][| ]]
" orgCmntEnd)
(cl-defun b:pkg:area/verb (
;;;#+END:
                           <arg &optional <opt)
   " #+begin_org
** DocStr: One line on what it does.
#+end_org "
  ...)
```

Copy the heading line from a sibling file, not from memory. Group definitions under
`blee:bxPanel:foldingSection` dividers. `(interactive (list ...))` is fine in a `cl-defun`.

## 4. Menus: easymenu, built once

The Blee menu pattern (`b:<prefix>:menu.el`): `…:menu:plugin|install (<menuLabel <menuDelimiter)`
adds the package's menu into a parent menu at a delimiter; `…:menu|define` builds it with
`easy-menu-define` and `easy-menu-add-item` per submenu (`(s-- 3)`, `(s-- 4)` delimiters).

- *Build once.* Never call `…|define` from `menu-bar-update-hook`: that hook runs on nearly every
  redisplay of the menu bar. Rebuilding Blee's Acts and Apps menus there cost 1.26 s and 0.26 s per
  run and made Blee slow (2026-10-31). An update hook may only do cheap work, and may be empty.
- *Live state is lazy*: `:active`, `:visible`, `:selected` (with `:style toggle`), or `:filter` for a
  submenu computed when it is opened.
- Offer a `…|refresh` command that rebuilds on demand, and report a failed build rather than leave
  a half-built menu.

## 5. Transients and magit

```elisp
(with-eval-after-load 'transient
  (transient-define-prefix b:pkg/dispatch ()
    "What it is."
    [["Send" ("s" "Prompt" b:pkg/send) ...]
     ["Options" ("S" b:pkg/toggle :transient t
                 :description (lambda () (format "Submit (%s)" (if b:pkg:flag? "on" "off"))))]]))
```

- Every suffix is an ordinary interactive command, so `M-x` and the menu reach it too.
- `:transient t` keeps the menu open (toggles); a `:description` lambda shows live state.
- Magit: define the prefix inside `(with-eval-after-load 'magit ...)`; in a `…:magit|config` run from
  the adoption's `config|main` after magit, bind it (`(define-key magit-mode-map (kbd "x") …)`) and
  `(transient-append-suffix 'magit-dispatch "X" '("x" "Label" prefix))` inside `condition-case`.
- A global key for a prefix is the user's choice; do not take one unasked.

## 6. Adopt it into Blee (bnpa)

1. `blee/env3/plus/bnpa:<pkg>.el`, copied from a sibling (`bnpa:aiplus.el`) with the name
   replaced. `b:npa:<pkg>:install|update` installs with straight (`:local-repo
   /bisos/git/bxRepos/blee/<pkg>` when `b:g:dev:mode?`); `b:npa:<pkg>:config|main` does
   `(require 'b:<pkg>::pkg)` and setup that waits for another package (`with-eval-after-load`).
2. `plus/plus-init.el`: `(require 'bnpa:<pkg>)` and `(b:npa:<pkg>|fullUpdate)`.
3. Code moved from a `bcpg:<x>Plus.el` is removed there in the same change: one definition.

Keep setup that takes something over (a partner role, a server, a global key) out of
`config|main` unless asked: every Blee started, including a test one, runs it.

## 7. Test: batch, then a fresh Blee

*Batch* (fast, no side effects): load the package from the straight build directory and stub what
reaches outside with `cl-letf`.

```elisp
(dolist (d (directory-files "/var/bisos/blee/emacsVers/31.1/doom-run-blee3/.local/straight/build-31.1" t "^[^.]"))
  (add-to-list 'load-path d))
(add-to-list 'load-path "/bisos/git/bxRepos/blee/comment-block")   ; orgCmntBegin
(add-to-list 'load-path "/bisos/git/bxRepos/blee/<pkg>")
(require 'comment-block)
(provide 'blee-libs)                         ; stubs for what Blee itself provides
(defun s-- (n) (format "--- %d" n))
(require 'magit) (require 'b:<pkg>::pkg)
(cl-letf (((symbol-function 'b:pkg:program/run) (lambda (&rest args) (setq ran args) t)))
  ... assertions: the arguments built, the state recorded ...)
```

Run: `emacs-31.1 --batch -l test.el`. Timers need a `(sit-for 0.1)` to fire. Keep the test in the
scratchpad, or in the repo if the user wants it kept.

*A fresh Blee* (interactive behaviour, the real load path, `server`, hooks): skill
`bs-blee-emacs-server`, section 6. In dev mode it loads the package from the repo as it is on
disk. Never test in the user's Blee; anything acting on another program (VS Code, X focus, the
clipboard) needs the user watching.

## 8. Document and commit

- README.org: the frame of a sibling blee-pkg (`aiplus`): the panel-controls line, Overview,
  `:TOC:`, Blee and straight installation, the `blee:bxPanel:footer*` blocks; lines and tables
  within 105 characters (`readme-authorship`). Where the Python package's README has the command
  tables, link to it rather than copy them.
- A change usually spans three repos. Commit the bisos-pip package first (what the elisp runs),
  then the blee-pkg, then `blee/env3`; each message gets a `Requires:` trailer for the one before
  (`/bx-git-commit-msg`). The adoption installs from github outside dev mode: push the blee-pkg
  before env3's change reaches other machines.

## Pitfalls

- *A reload does not re-run `config|main`*: hooks and keys set there need it run again.
- *`with-eval-after-load` order*: a transient referring to magit's maps must wait for magit.
- *A function that errors in `menu-bar-update-hook` or `post-command-hook` is removed by Emacs*:
  the symptom is a feature that stops working silently (or a menu frozen half-built).
- *TRAMP buffers*: `default-directory` is remote; run programs from `~/` and refuse or map remote
  paths explicitly.
- *A new .el file is not loaded until straight rebuilds the package.* Blee sets
  `straight-check-for-modifications` to nil, so the build directory
  (`.local/straight/build-31.1/<pkg>/`, links to the repo's files) never picks up a new file on its
  own, and a `require` of it stops Blee's startup. After adding a file: `M-x straight-rebuild-package
  RET <pkg>` in Blee (or add the link the rebuild would make), and say so to the user before they
  restart. Edits to existing files need nothing: the links point at the repo. Found 2026-10-31.

## References

- `/bisos/git/bxRepos/blee/vscode-claude` (`b:vscode.el`, `b:vscode:claude.el`, `…:menu.el`;
  README.org), `/bisos/git/bxRepos/blee/aiplus` (the menu and README frame).
- `/bisos/blee/env3/plus/bnpa:aiplus.el`, `bnpa:vscode-claude.el`, `plus-init.el`.
- `/bisos/blee/env3/legacy/modes-menu.el`, `apps-menu.el` (menus built once, `…|refresh`).
- Skills `comeega-authorship`, `bs-blee-emacs-server`, `writing-cs-commands`, `readme-authorship`.
