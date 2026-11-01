---
name: lcnt-multimedia
description: Use when working on the multimedia side of an LCNT (Libre CoNtenT) presentation — recorded-talk projects that combine the slides with narration audio, assembled/captioned video, and `.vtt` subtitles. Covers the MmUnite flow (`lcntProc.sh -i mmUniteStart`, `mmUnite.sh`, the `audio/` and `video/` panels), aeneas-based `.vtt` subtitle sync from a `.narration` text, and the audio/video asset conventions. For building the slide deck itself see lcnt-build-and-release.
---

# LCNT Multimedia (MmUnite)

Beyond PDF/HTML/Reveal, an LCNT presentation can be a **multimedia** artifact: the slides plus
synchronized narration audio, an assembled/captioned video, and subtitle tracks. This machinery is
called **MmUnite** ("multimedia unite"). It is optional — only recorded-talk projects (e.g. an
EmacsConf presentation) carry `audio/`, `video/`, and `qAndA-video/` trees.

## Entry points

```bash
lcntProc.sh -v -n showRun -i mmUniteStart     # start the MmUnite flow
mmUnite.sh                                    # the audio/video orchestrator
```

Each area has its own Blee panel: `MmUnitePanel.org` at the root, `audio/Panel.org`,
`video/` scripts (`mmUniteVideo.sh`), and `audio/mmUniteAudio.sh`. The root `Panel.org` has
clickable links for every step.

## Asset conventions

- `audio/` — one file per narration section as `<section>.wav` + `<section>.mp3`, with a
  `<section>.length` marker (duration). Section names track the slide/content structure
  (e.g. `titlePage`, `part_*`, `citation_*`).
- `video/` — the main rendering `plpc-<nu>-<date>.mp4` (and `.mkv`), a `-captioned.mp4` variant,
  intro/outro clips (`mbIntro.mp4`, `endVideo.mp4`), and `derived-*.mp4` excerpt clips.
- `<name>.narration` — plain-text narration script used to drive subtitle sync.
- `<name>.vtt` — WebVTT subtitles (the deliverable captions).
- `qAndA-video/` — Q&A session media and its `.vtt` files.
- `disposition.gened/` — generated per-slide disposition (`slide1`…`slideN`) tying slides to timing.

## Subtitle (.vtt) sync with aeneas

Subtitles are produced by force-aligning the `.narration` text to the media with the Python
**aeneas** tool:

```bash
python -m aeneas.tools.execute_task ./video/plpc-<nu>.mp4 plpc-<nu>.narration \
  "task_language=eng|os_task_file_format=vtt|is_text_type=plain" map.vtt
```

- `task_language` — `eng` / `fas` (Farsi) etc., matching the narration language.
- The output `.vtt` is then attached to the video (`-captioned.mp4`) or served alongside HTML/Reveal.
- aeneas binaries are prepared by `/bisos/core/lcnt/bin/lcaPy3AeneasBinsPrep.sh`; related media
  bin-prep scripts: `lcaAudioManage.sh`, `lcaAudioVideoBinsPrep.sh`, `mmBinsPrep.sh`,
  `seedAudioProc.sh`.

## Gotchas

- MmUnite assets are large (audio hundreds of MB, video can exceed a GB). Don't copy or `git add`
  the heavy media casually — check the project's `.gitignore`; derived media are often
  regenerated, not versioned.
- Narration-to-slide alignment depends on the `.narration` text matching the spoken content; a
  drifted narration yields mis-timed captions — re-run the aeneas task after editing narration.
- The slide deck build (Reveal/PDF) and the MmUnite assembly are separate steps — build the deck
  first (see `lcnt-build-and-release`), then run MmUnite.

## References

- MmUnite scripts: `/bisos/core/lcnt/bin/` (`seedMmUnite.sh`, `seedAudioProc.sh`,
  `lcaAudioManage.sh`, `lcaPy3AeneasBinsPrep.sh`).
- Per-project panels: `MmUnitePanel.org`, `audio/Panel.org`, `video/mmUniteVideo.sh`.
- Build the deck: `lcnt-build-and-release`.
