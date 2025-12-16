# Build / release (dev)

Deze repo bouwt een Windows **single-file** installer EXE (PyInstaller onefile).

## Build (lokaal)

```powershell
# Controleer of het logo bestaat
Test-Path .\logo\cF_Logo.png   # True

# Clean build (met logo meepakken)
taskkill /IM "colorFabbInstaller_v*.exe" /F 2>$null
Remove-Item -Recurse -Force .\dist, .\build -ErrorAction SilentlyContinue

# Build 1 EXE via de (aangepaste) .spec
# Dit houdt de output als één enkel bestand, maar laat ons ongebruikte Qt/PySide6
# componenten uitsluiten om het kleiner te maken.
# Ook de Windows "File version" / "Product version" wordt automatisch gezet op basis van VERSION in main.py.

# (Optioneel) UPX compressie: zet UPX_DIR naar de map waar upx.exe staat
# $env:UPX_DIR = "C:\Tools\upx"

# (Optioneel) Extra size-trims (blijft 1 EXE)
# - CF_EXCLUDE_QJPEG=1          -> verwijdert Qt JPEG plugin (alleen doen als je nooit JPG laadt)
# - CF_EXCLUDE_OPENGL_SW=1      -> verwijdert Qt software OpenGL fallback (grote winst, maar kan op
#                                 sommige pc's / remote desktop rendering issues geven)
# Voorbeeld:
# $env:CF_EXCLUDE_OPENGL_SW = "1"
# $env:CF_EXCLUDE_QJPEG = "1"

python -m PyInstaller --noconfirm --clean ".\colorFabb Filament Installer.spec"
```

## Release build (aanrader)

`build-release.ps1`:
- bouwt de EXE
- schrijft een SHA256 checksumbestand naast de EXE
- (optioneel) signeert de EXE met een PFX

```powershell
./build-release.ps1
```

### Download test (zonder installeren)

Handig om te checken of HTTPS download + ZIP validatie werkt in de EXE.

```powershell
$exe = Get-ChildItem .\dist\colorFabbInstaller_v*.exe | Select-Object -First 1
& $exe.FullName --check-download
```

## GitHub Releases (EXE als asset)

Push een tag om een release-build te triggeren:

```powershell
git tag v1.6.3
git push origin v1.6.3
```

De GitHub Actions workflow bouwt en uploadt:
- `dist\colorFabbInstaller_vX.Y.Z.exe`
- `dist\colorFabbInstaller_vX.Y.Z.sha256.txt`

## Code signing

Vereist: code signing certificaat (meestal PFX) + `signtool.exe` (Windows SDK).

```powershell
$pw = Read-Host -AsSecureString "PFX password"
./build-release.ps1 -Sign -PfxPath "C:\path\to\colorfabb.pfx" -PfxPassword $pw
```

Of met `PSCredential`:

```powershell
$cred = Get-Credential -Message "Enter PFX password" -UserName "ignored"
./build-release.ps1 -Sign -PfxPath "C:\path\to\colorfabb.pfx" -PfxCredential $cred
```

### Code signing in GitHub Actions (optioneel)

Zet deze repo secrets om signing in CI aan te zetten:
- `CODESIGN_PFX_BASE64` (base64 van jullie `.pfx`)
- `CODESIGN_PFX_PASSWORD` (wachtwoord)

Zonder deze secrets blijft de workflow gewoon unsigned builds maken.

## Verificatie checklist (na Release)

```powershell
# 1) Download de .exe en .sha256.txt van GitHub Releases.
# 2) Controleer de hash lokaal:
$sha = Get-Content .\colorFabbInstaller_vX.Y.Z.sha256.txt
$local = (Get-FileHash -Algorithm SHA256 .\colorFabbInstaller_vX.Y.Z.exe).Hash.ToLowerInvariant()
$sha -match $local
```
