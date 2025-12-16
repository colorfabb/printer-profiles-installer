
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

# Release build (aanrader)
# - bouwt de EXE
# - schrijft een SHA256 checksumbestand naast de EXE
# - (optioneel) signeert de EXE met jullie certificaat (PFX)
./build-release.ps1

# Download test (zonder installeren)
# Handig om te checken of HTTPS download + ZIP validatie werkt in de EXE.
# De EXE bestandsnaam bevat automatisch de VERSION uit main.py.
# Voorbeeld: colorFabbInstaller_v1.2.3.exe
$exe = Get-ChildItem .\dist\colorFabbInstaller_v*.exe | Select-Object -First 1
& $exe.FullName --check-download

# SHA256 checksum bestand
# Na ./build-release.ps1 krijg je:
#   dist\colorFabbInstaller_vX.Y.Z.sha256.txt

# Code signing (om Windows waarschuwingen te verminderen)
# Vereist: code signing certificaat (meestal PFX) + signtool.exe (Windows SDK)
# Voorbeeld:
#   $pw = Read-Host -AsSecureString "PFX password"
#   ./build-release.ps1 -Sign -PfxPath "C:\path\to\colorfabb.pfx" -PfxPassword $pw
# Of met PSCredential:
#   $cred = Get-Credential -Message "Enter PFX password" -UserName "ignored"
#   ./build-release.ps1 -Sign -PfxPath "C:\path\to\colorfabb.pfx" -PfxCredential $cred
