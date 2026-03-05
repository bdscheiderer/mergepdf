# MergePDF — Distribution Notes

## Status
- [x] Code ready (class-based, cross-platform icon loading)
- [x] `.spec` file has `hiddenimports=['pypdf']`
- [x] Windows `.ico` icon exists (`favicon.ico`)
- [ ] macOS `icon.png` needed
- [ ] macOS `icon.icns` needed
- [ ] `LICENSE.txt` file needed
- [ ] Windows installer (optional)
- [ ] macOS `.dmg` package (optional)

---

## Assets Still Needed

### icon.png (macOS/Linux)
- Minimum 512x512px, ideally 1024x1024px
- Used by `iconphoto()` on macOS/Linux at runtime
- Must be added to the `images/` folder (or root) and bundled in the spec

### icon.icns (macOS dock icon)
- Required for the app icon to display correctly in the macOS dock
- Convert from a high-res PNG using one of:
  - Free online: https://cloudconvert.com/png-to-icns
  - macOS built-in: use `iconutil` with an `.iconset` folder

### LICENSE.txt
Create a file `LICENSE.txt` in the project root:
```
MIT License

Copyright 2026 S2Legacy.com

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## Windows .exe Build

### Steps
1. Install PyInstaller: `pip install pyinstaller`
2. Build: `pyinstaller mergepdf.spec`
3. Output is in `dist/mergepdf.exe`

### Spec file is ready — no changes needed.

### Optional: Wrap in an installer
Use **Inno Setup** (free): https://jrsoftware.org/isinfo.php
- Creates a proper installer with Start Menu shortcut and uninstaller
- Standard for paid Windows desktop utilities

---

## macOS .app Build

### Steps
1. Add `icon.png` and `icon.icns` to the project folder
2. Update `mergepdf.spec` — add the macOS BUNDLE section and icon files:

```python
# Add icon.png to datas so it bundles at runtime
datas=[('favicon.ico', '.'), ('icon.png', '.')],

# Add icon to EXE section
icon=['favicon.ico'],  # Windows
```

Add a BUNDLE block after EXE in the spec for macOS:
```python
app = BUNDLE(
    exe,
    name='MergePDF.app',
    icon='icon.icns',
    bundle_identifier='com.s2legacy.mergepdf',
    info_plist={
        'NSHighResolutionCapable': True,
        'CFBundleShortVersionString': '1.1',
    },
)
```

3. Build on a Mac: `pyinstaller mergepdf.spec`
4. Output is `dist/MergePDF.app`

### Optional: Package as .dmg
Use **create-dmg** (free, Homebrew):
```bash
brew install create-dmg
create-dmg \
  --volname "MergePDF" \
  --window-size 500 300 \
  --icon-size 100 \
  --icon "MergePDF.app" 130 150 \
  --app-drop-link 370 150 \
  "MergePDF-1.1.dmg" \
  "dist/MergePDF.app"
```

### macOS Code Signing (to avoid Gatekeeper warnings)
- Requires Apple Developer account ($99/year)
- Without signing, users must right-click > Open the first time
- For paid distribution, signing is strongly recommended
- Sign with: `codesign --deep --force --sign "Developer ID Application: Your Name" dist/MergePDF.app`

---

## Both Platforms — Before Release Checklist
- [ ] Test on a clean Windows machine (no Python installed)
- [ ] Test on a clean macOS machine
- [ ] Verify merged PDF opens correctly with "Open merged PDF" button
- [ ] Verify file conflict/timestamp logic works
- [ ] Verify all three Help menu dialogs display correctly
- [ ] Update version string in `open_about_info()` if needed
