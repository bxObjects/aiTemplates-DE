---
name: lcnt-multimedia
description: Use when working on the multimedia side of an LCNT (Libre CoNtenT) presentation — choosing per frame whether Reveal shows the Beamer frame as an image or as native HTML (the `b:lcnt:pres:frame/*` dblocks, `disposition.gened`), recorded-talk projects that combine the slides with narration audio, assembled/captioned video, and `.vtt` subtitles. Also narration audio by text-to-speech (Piper) beside the author's recordings, with `audio/audioProc.spcs` (`ttsGenerate`, `audioSelect`, `ttsClean`), and Reveal frames that show broken images (`beamerDerivedFullBuild`). Covers the MmUnite flow (`lcntProc.sh -i mmUniteStart`, `mmUnite.sh`, the `audio/` and `video/` panels), aeneas-based `.vtt` subtitle sync from a `.narration` text, and the audio/video asset conventions. For building the slide deck itself see lcnt-build-and-release.
---

# LCNT Multimedia (MmUnite)

Beyond PDF/HTML/Reveal, an LCNT presentation can be a **multimedia** artifact: the slides plus
synchronized narration audio, an assembled/captioned video, and subtitle tracks. This machinery is
called **MmUnite** ("multimedia unite"). It is optional — only recorded-talk projects (e.g. an
EmacsConf presentation) carry `audio/`, `video/`, and `qAndA-video/` trees.

## Frame dispositions: Beamer image or native HTML, per frame

Beamer is the master. The Reveal deck serves two uses:

1. **Recorded talk.** Reveal auto-plays each frame with its voice-over (`\frameaudio`, the
   reveal.js audio-slideshow plugin) while OBS records the screen; the result is the video (YouTube
   etc.). Only the look of each slide matters, and no HTML is as good as Beamer, so these frames are
   images of the Beamer PDF.
2. **Reveal in a browser.** Each frame chooses image or native HTML (HeVeA from the same LaTeX).

The choice is the frame dblock in `body*.tex` (`%%%#+BEGIN: b:lcnt:pres:<type> ... :label "<name>"`):

| Dblock                      | In Reveal                                                        |
|-----------------------------|------------------------------------------------------------------|
| `frame/derivedImage`        | the Beamer frame's image                                         |
| `frame/derivedVideo`        | a video standing for the frame                                   |
| `frame:begin/{blank,plain,regular}` | native HTML of the frame (HeVeA)                         |
| `frame/insertDerivedImage`  | the image of the frame named by `:derivedLabel` (raw HTML)       |
| `frame/insertDerivedVideo`  | the video of the frame named by `:derivedLabel`                  |

**The image-then-HTML pair.** Where links must be clickable, an `insertDerivedImage` (or
`insertDerivedVideo`) frame shows the Beamer image of the next frame, and the next frame, a
`frame:begin/plain` with the same title and its `:label` equal to that `:derivedLabel`, gives the
same content as native HTML ("And here are the same links as a native Reveal slide"). The video keeps
Beamer's looks; the deck keeps working links. Example: `obtainingSourcesInsert` then
`obtainingSources` in the EmacsConf25 presentation.

So "slides as images" is a per-frame choice with HTML available, not a loss of links or text; do not
present it as a weakness of the model.

**How the images are made** (a build whose `results` include `disposition`, or
`lcntProc.sh -i beamerDerivedFullBuild`):
1. `beamerExternalExtensions.py -i latexSrcToDispositionUpdate ./presentationEnFa.pdf` (needs
   `PyPDF4`) reads the `.snm` and writes `disposition.gened/slideN/value` = the frame's label.
2. `beamerPdfPages.cs -i updatePages ./presentationEnFa.pdf` cuts each page (`pdftk`) into
   `disposition.gened/<label>/slide.pdf` and renders `slide-1.png` (`pdftoppm -r 600`), the file the
   Reveal frames reference.
The build runs step 2 with `lpDo`, so a failure there is silent: the deck then has broken images.
Check `ls disposition.gened/*/slide-1.png | wc -l` after a build.

**A Reveal build alone does not make them.** A `pres-reveal` build spec whose `results` is just
`html` only builds the HTML; `revealJsBase/` links `disposition.gened` from the document. The images
come from `lcntProc.sh -i beamerDerivedFullBuild` (clean, PDF, steps 1 and 2, then `lcntBuild cur`),
or from a build whose `results` lists `disposition` before `html`. `disposition.gened/` is not in git,
a fresh clone has none, and `lcntProc.sh -i fullClean ForGit` deletes it (a plain `fullClean` does not).
So when the Reveal deck shows broken images, run `beamerDerivedFullBuild`; also after editing frames,
since the images are of the last PDF. (Found 2026-11-17, EmacsConf26.)

## Narration audio: text-to-speech and recordings (`audio/audioProc.spcs`)

A frame's narration is its `\pnote`; Reveal plays `audio/<label>.mp3` (`\frameaudio` becomes
`data-audio-src`). For a new document, plant the bisos.lcnt tool in the document's `audio/` (the older
`audio/mmUniteAudio.sh` records straight into `<label>.wav` and is left for older documents):

```bash
lcntAudio-seed.cs -i audioPlant .      # audio/audioProc.spcs, .gitignore, ttsLexicon
cd audio
./audioProc.spcs -i narrationList      # frames, words, estimated time (140 words a minute)
./audioProc.spcs -i ttsGenerate        # tts-<label>.*, changed frames only; links frames playing nothing
./audioProc.spcs -i recordCmnds        # audacity commands for rec-<label>.wav; then -i recFinalize
./audioProc.spcs -i audioSelect rec    # recordings where there are some, tts elsewhere
./audioProc.spcs -i audioReport        # what plays per frame, stale recordings, total time
./audioProc.spcs -i ttsClean           # delete what ttsGenerate makes again; recordings are kept
```

- Two sources coexist: `tts-<label>.{mp3,length,textHash}` and `rec-<label>.{wav,mp3,length,textHash}`.
  What plays, `<label>.mp3` and `<label>.length`, are relative links to one of them: switching a frame
  is relinking, with no rebuild and no change to the player.
- `.textHash` begins with the hash of the narration the audio was made from: a recording older than
  its `\pnote` is reported stale. `.length` is milliseconds, no newline.
- `ttsLexicon` (`term = spoken`) fixes pronunciation, for the tts only.
- Piper and its voices (public-domain recordings only) come from `piperTts-sbom.pcs`; facts in
  `lcntTtsInfo.py`. A container has no sound device: generate there, listen elsewhere.
- The audio is not in git (`audio/.gitignore`). Publishing must copy the link targets (`cp -L`):
  the release step copies `revealJsBase/audio` as a link, so a release carries no audio yet.

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
- `disposition.gened/` — generated: `slide1`…`slideN` each name a frame label; each
  `<label>/` holds `slide.pdf` and `slide-1.png` (and parameters such as `transition`). See above.
- `audio/<label>.mp3` — a frame's voice-over, keyed by the frame's label (`\frameaudio`); with
  `audioProc.spcs`, a link to `tts-<label>.mp3` or `rec-<label>.mp3` (see above).

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
