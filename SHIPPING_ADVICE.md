# MergePDF — Shipping advice (v1.1)

Saved from a project review. Retrieve this later when you pick the work back up.

**Date:** 2026-09-16

---

## Purpose (this sets the bar)

This is **not** a product to sell. The point is to demonstrate that you created and shipped something useful.

It started as a real problem: merge a few PDFs without buying Adobe Acrobat or a subscription. At most, add a Buy Me a Coffee link on the download page, and maybe one quiet line in the in-app About dialog. No nag screen, no first-launch popup.

That means:

- You do **not** need Inno Setup polish, Apple code signing, a test suite, or a conversion funnel.
- You **do** need a stranger to understand the problem, run the tool, merge a few files, and see that you made it.

---

## Direct answers

| Question | Answer for *this* purpose |
|---|---|
| Ready to ship as v1.1? | Close. Working prototype. Short polish pass, then ship. |
| Secure? | Fine for a local desktop tool. Do not turn it into a public upload server. |
| Bad coding practice? | No. Typical beginner-good post-CS50 code, with a few real gaps. |
| Need a web app? | No. A clean page + desktop download already counts as shipped. A browser merger is an optional extra, not a requirement. |

---

## What “shipped something useful” actually needs

A stranger should be able to do this without asking you questions:

1. Land on a page or GitHub repo and understand the problem in one sentence.
2. Download or run it.
3. Merge a few PDFs.
4. See that you made it (About, license, contact).

The **app** mostly does step 3. The **story** is the weak part right now:

- README is two sentences.
- Packaging notes still read as an unfinished checklist.
- `dist/mergepdf.exe` is an old August 2025 build; the spec/installer expect `MergePDF.exe`.
- `build/`, `misc/`, and old EXEs look like homework leftovers if they are the public face of the repo.

Treat the public face as part of the project: README, one downloadable build that matches About (`MergePDF v1.1`), MIT license, and a quiet Coffee link.

---

## What the app already does well

Three-step flow in `mergepdf.py`:

1. Select a folder → find `*.pdf` (case-insensitive, sorted by name) → checklist (at least two files).
2. Name the output (default `merged_pdfs.pdf`). Invalid names rejected **if** the user clicks Submit. If the name already exists in the folder, a timestamp is prepended so nothing is overwritten.
3. Merge with `pypdf.PdfWriter`, write into the same folder, then offer **Open merged PDF**.

Also already in place: ttkbootstrap GUI, File/Help menus, Reset, About/Instructions/Contact, PyInstaller spec (Windows EXE + macOS `.app`), Inno Setup script, MIT license.

For a first post-CS50 project this is better than a throwaway script: class-based UI, helpers split out, modal file checklist, no-overwrite, icons via `resource_path()` for PyInstaller.

---

## Fix before calling it v1.1

These are the items that show up in a 10-minute demo or a reviewer poking at the repo.

### 1. Reorder files (highest product value)

Merge order is alphabetical (`get_pdfs` sorts by name). For a merge tool, order is the main feature. Up/down buttons are enough; drag-and-drop is nicer but not required.

### 2. Validate the output name on Merge

`pdf_merge()` → `_check_file_name()` never calls `is_valid_filename()`. Submit is optional. A user can type `../out.pdf` and click Merge, which can write **outside** the chosen folder.

Fix: run `is_valid_filename()` inside `_check_file_name()`, and reject names containing `..`. Even better: drop the required Submit click and validate when they hit Merge.

### 3. Busy cursor / “working…” state

Merge runs on the Tk main thread. Small files are fine; a larger scan looks crashed. A busy cursor or disabled Merge button is enough. You do not need a progress bar.

### 4. Public face of the repo

- Rewrite the README around the real problem (no Adobe / no subscription), how to run, a screenshot, MIT.
- One build that matches the version string in About.
- Keep `build/`, `misc/`, `.DS_Store`, and old EXEs out of the public story (`.gitignore` and/or GitHub Releases instead of committing `dist/`).

### 5. Packaging enough to hand to a stranger

- Generate `icon.icns` from `icon.png` (commands are in `REVIEW_NOTES.md`).
- Build on Mac → `dist/MergePDF.app`. Optional: wrap in a `.dmg`.
- Build on Windows → `dist/MergePDF.exe`. Optional: Inno Setup via `mergepdf.iss`.
- Unsigned binaries will warn on first open (SmartScreen / Gatekeeper). For a free personal utility, document “right-click → Open” on Mac and move on. Do not pay for signing just for the portfolio.

### 6. Pin the two dependencies

`requirements.txt` is currently unpinned (`pypdf`, `ttkbootstrap`). Pin versions so a rebuild in six months is the same app. Also note **Python 3.12+** (`Path.glob(..., case_sensitive=False)`).

---

## Okay to ship with (document, do not over-fix)

- Encrypted / corrupt PDFs show a raw `Error merging files: ...` string.
- Output is written into the source folder, so the next Select can list `merged_pdfs.pdf` as an input. Users can uncheck it.
- Folder picker cannot preview the PDFs (already noted in code).
- No subfolder recursion; only `*.pdf` in the chosen folder.

---

## Not worth doing for this goal

- Paid Apple Developer account / code signing
- Polished Windows installer as a requirement (optional nicety)
- Splitting `mergepdf.py` into a package/framework
- Full test suite (a 20-line script that merges `files/test*.pdf` and checks page count is plenty if you want one)
- Special-casing every encrypted-PDF error
- Flask/FastAPI upload backend
- Anything that exists only to “look more professional” rather than help someone merge three files

---

## Security (calibrated)

As a local app that only touches files the user picked: **fine**.

- No network, no accounts, no `eval`, no `shell=True`.
- Opening the result uses `open` / `os.startfile` / `xdg-open` with a path, not a shell string.
- Residual risk of a malicious PDF is in the same class as opening it in a viewer. Keep `pypdf` updated.

The one real bug is output-name path traversal (`../`) if they skip Submit — fix that, then stop.

**Do not** put this behind a public upload form. Untrusted PDFs on a server are a different problem (huge files, CPU DoS, malware hosting, privacy of tax/medical docs). The whole point of this tool is that files never leave the machine.

---

## Code quality notes (for later you)

Beginner-typical, not “throw it away”:

- Submit-then-Merge is CS50-assignment flow. Desktop apps validate on the action that writes the file.
- UI and PDF I/O live in one class. Fine at this size.
- `except Exception as e` then show `e` in the window. Better: plain sentence for expected failures (permission, encrypted, missing file).
- Module docstring typo: `prgram`.
- `reset_form()` now clears `self.file_list` (uncommitted at review time — keep that).
- Windows reserved names (`CON`, `NUL`, …) are now checked on every OS (uncommitted at review time — keep that). That matters so a Mac user cannot create `CON.pdf` that later breaks on Windows.

---

## Buy Me a Coffee

- **Landing page:** button below the fold. Let it be discovered, not demanded.
- **In-app:** one sentence in About, e.g. *If MergePDF saved you a subscription, you can buy me a coffee at s2legacy.com.*
- Fill placeholders in the landing page (`YOURUSERNAME` for Coffee and GitHub) before you send anyone the link. Those notes live in `REVIEW_NOTES.md`.

---

## Web app (optional, later)

Do **not** run Tkinter in a browser. Reuse the product, not the widgets:

- pick 2+ PDFs
- choose order
- choose output name
- merge pages
- get the result

### Option A — all in the browser (only extra worth considering)

Static page + `pdf-lib`. Files stay on the device. No server, no privacy problem, fits Cloudflare Pages / `mergepdf.s2legacy.com`. Same story as the desktop app: no Adobe, no upload to a random merger site.

This would be the strongest *extra* because anyone can try it without installing. It is still optional.

### Option B — Flask/FastAPI uploads

Wrong extra for this project. Adds ops and privacy questions you do not want on a portfolio piece about avoiding subscription services. Skip it unless you specifically want server practice.

---

## Suggested v1.1 sequence

1. Fix reorder + filename-on-merge (including `..`) + busy cursor.
2. Generate `icon.icns`, build once on Mac and once on Windows, put those on GitHub Releases or the landing page.
3. Rewrite the README around the problem you actually had. Add a screenshot.
4. Add Buy Me a Coffee on the page; optional one-liner in About.
5. Use it yourself on real files, then stop.

That is a complete story: personal itch, working tool, public download, honest license. You do not need to sell it for it to count as shipped.

---

## Related files in this repo

| File | What it is |
|---|---|
| `mergepdf.py` | The app |
| `mergepdf.spec` | PyInstaller (Windows EXE / macOS `.app`) |
| `mergepdf.iss` | Optional Inno Setup installer |
| `requirements.txt` | `pypdf`, `ttkbootstrap` (unpinning is a later-you problem) |
| `DISTRIBUTION_NOTES.md` | Build/packaging checklist (icons, dmg, signing) |
| `REVIEW_NOTES.md` | Bugs already fixed, `iconutil` commands, landing-page placeholders |
| `LICENSE.txt` | MIT, S2 Legacy, LLC |
| `files/` | Sample PDFs for trying a merge |

`iconutil` commands (from `REVIEW_NOTES.md`) when you are on the Mac:

```bash
mkdir icon.iconset
sips -z 1024 1024 icon.png --out icon.iconset/icon_512x2.png
sips -z 512 512 icon.png --out icon.iconset/icon_512.png
sips -z 256 256 icon.png --out icon.iconset/icon_256.png
sips -z 128 128 icon.png --out icon.iconset/icon_128.png
iconutil -c icns icon.iconset -o icon.icns
rm -rf icon.iconset
```

Note: a complete `.icns` usually also includes 16/32/64/128/256/512 and their `@2x` sizes. The commands above are the ones already recorded in this repo; expand the set if the dock icon looks wrong.
