# MergePDF — Review Notes & Launch Checklist

## Code Fixes Applied

### Bug 1 — reset_form() stale file list (fixed)
`reset_form()` now clears `self.file_list = []`.
**Why it mattered:** Resetting and clicking Merge without re-selecting a folder would use stale files from the previous session and write the output to the current working directory instead of raising an error.

### Bug 2 — Windows reserved filename check (fixed)
`is_valid_filename()` now always checks Windows reserved names (CON, NUL, COM1, etc.) regardless of platform.
**Why it mattered:** A macOS user could create `CON.pdf`, which would cause problems if the file was ever shared with a Windows machine.

---

## macOS Icon — One Manual Step Remaining

`icon.png` (1024x1024) is already in the project root (copied from `images/mergepdf-white_bg.png`).
You still need `icon.icns` for the macOS dock. Run this on your Mac:

```bash
mkdir icon.iconset
sips -z 1024 1024 icon.png --out icon.iconset/icon_512x2.png
sips -z 512 512 icon.png --out icon.iconset/icon_512.png
sips -z 256 256 icon.png --out icon.iconset/icon_256.png
sips -z 128 128 icon.png --out icon.iconset/icon_128.png
iconutil -c icns icon.iconset -o icon.icns
rm -rf icon.iconset
```

---

## Files Created / Updated

| File | What changed |
|---|---|
| `mergepdf.py` | Bug fixes: reset clears file_list; reserved name check always runs |
| `mergepdf.spec` | Now cross-platform: produces EXE on Windows, BUNDLE (.app) on macOS |
| `mergepdf.iss` | New — Inno Setup installer script for Windows |
| `icon.png` | New — copied from images/, used by macOS build |
| `DISTRIBUTION_NOTES.md` | Updated status checkboxes to reflect current state |
| `s2legacy/mergepdf/index.html` | New — landing page for mergepdf.s2legacy.com |

---

## Inno Setup Installer (mergepdf.iss)

Produces `MergePDF-1.1-Setup.exe` in an `installer/` folder.
- Installs to `Program Files\MergePDF` (no admin required)
- Start Menu shortcut
- Optional Desktop shortcut (unchecked by default)
- Shows MIT license during install
- Includes uninstaller
- Offers to launch the app after install

---

## Landing Page (s2legacy/mergepdf/index.html)

Two placeholders to fill in before deploying:

1. **Buy Me a Coffee username** — replace `YOURUSERNAME` in this line:
   ```html
   <a href="https://www.buymeacoffee.com/YOURUSERNAME" ...>
   ```

2. **GitHub repo link** — replace `YOURUSERNAME/mergepdf` in this line:
   ```html
   <a href="https://github.com/YOURUSERNAME/mergepdf" ...>
   ```

3. **Download file paths** — currently set to `/downloads/MergePDF-1.1.dmg` and `/downloads/MergePDF-1.1-Setup.exe`. Adjust to wherever you host the files (Cloudflare Pages `downloads/` folder or GitHub Releases URLs).

---

## Donation / Showcase Strategy

- **In-app:** Add one line to the About dialog: *"If MergePDF saved you time, consider buying me a coffee at s2legacy.com."* One sentence, no nag screen, no first-launch popup.
- **On the page:** Coffee button is already below the fold — good. Let it be discovered, not demanded.
- **GitHub:** A pinned repo with a clean README and a working release is often more impressive to technical reviewers than the website. Consider publishing the source.
- **Portfolio:** `s2legacy/index.html` still has placeholder project cards. MergePDF would be a strong first real entry — a working, MIT-licensed desktop app is a concrete, verifiable portfolio claim.

---

## Final Launch Checklist

- [ ] Run `iconutil` commands above to generate `icon.icns`
- [ ] `pyinstaller mergepdf.spec` on Mac → produces `dist/MergePDF.app`
- [ ] `create-dmg` to wrap into `MergePDF-1.1.dmg` (see DISTRIBUTION_NOTES.md)
- [ ] `pyinstaller mergepdf.spec` on Windows → produces `dist/MergePDF.exe`
- [ ] Open `mergepdf.iss` in Inno Setup and compile → produces `installer/MergePDF-1.1-Setup.exe`
- [ ] Replace `YOURUSERNAME` placeholders in `s2legacy/mergepdf/index.html`
- [ ] Upload `.dmg` and installer `.exe` to Cloudflare Pages or GitHub Releases; update download URLs in `index.html`
- [ ] Test on a clean Mac (no Python installed)
- [ ] Test on a clean Windows machine (no Python installed)
- [ ] Add MergePDF card to `s2legacy/index.html` portfolio page
