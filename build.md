# Build / release (dev)

This repo builds a Windows **single-file** installer EXE (PyInstaller onefile).

## Build (local)

```powershell
# Check if the logo exists
Test-Path .\logo\cF_Logo.png   # True

# Clean build (include logo)
taskkill /IM "colorFabbInstaller_v*.exe" /F 2>$null
Remove-Item -Recurse -Force .\dist, .\build -ErrorAction SilentlyContinue

# Build a single EXE via the (custom) .spec
# This keeps the output as one file, while allowing us to exclude unused Qt/PySide6
# components to reduce size.
# Windows "File version" / "Product version" are set automatically based on VERSION in main.py.

# (Optional) UPX compression: set UPX_DIR to the folder containing upx.exe
# $env:UPX_DIR = "C:\Tools\upx"

# (Optional) Extra size trims (still 1 EXE)
# - CF_EXCLUDE_QJPEG=1          -> removes Qt JPEG plugin (only if you never need JPG)
# - CF_EXCLUDE_OPENGL_SW=1      -> removes Qt software OpenGL fallback (big win, but may cause
#                                 rendering issues on some PCs / remote desktop setups)
# Example:
# $env:CF_EXCLUDE_OPENGL_SW = "1"
# $env:CF_EXCLUDE_QJPEG = "1"

python -m PyInstaller --noconfirm --clean ".\colorFabb Filament Installer.spec"
```

## Release build (recommended)

`build-release.ps1`:
- builds the EXE
- writes a SHA256 checksum file next to the EXE
- (optional) code-signs the EXE with a PFX

```powershell
./build-release.ps1
```

### Download self-test (without installing)

Useful to verify HTTPS download + ZIP validation inside the packaged EXE.

```powershell
$exe = Get-ChildItem .\dist\colorFabbInstaller_v*.exe | Select-Object -First 1
& $exe.FullName --check-download
```

## GitHub Releases (EXE als asset)

Push a tag to trigger a release build:

```powershell
git tag v1.6.3
git push origin v1.6.3
```

De GitHub Actions workflow bouwt en uploadt:
The GitHub Actions workflow builds and uploads:
- `dist\colorFabbInstaller_vX.Y.Z.exe`
- `dist\colorFabbInstaller_vX.Y.Z.sha256.txt`

## Code signing

Requires: a code signing certificate (usually PFX) + `signtool.exe` (Windows SDK).

```powershell
$pw = Read-Host -AsSecureString "PFX password"
./build-release.ps1 -Sign -PfxPath "C:\path\to\colorfabb.pfx" -PfxPassword $pw
```

Or using `PSCredential`:

```powershell
$cred = Get-Credential -Message "Enter PFX password" -UserName "ignored"
./build-release.ps1 -Sign -PfxPath "C:\path\to\colorfabb.pfx" -PfxCredential $cred
```

### Code signing in GitHub Actions (optioneel)

Set these repo secrets to enable signing in CI:
- `CODESIGN_PFX_BASE64` (base64 of your `.pfx`)
- `CODESIGN_PFX_PASSWORD` (password)

Without these secrets the workflow will produce unsigned builds.

## Verification checklist (after release)

```powershell
# 1) Download the .exe and .sha256.txt from GitHub Releases.
# 2) Verify the hash locally:
$sha = Get-Content .\colorFabbInstaller_vX.Y.Z.sha256.txt
$local = (Get-FileHash -Algorithm SHA256 .\colorFabbInstaller_vX.Y.Z.exe).Hash.ToLowerInvariant()
$sha -match $local
```
