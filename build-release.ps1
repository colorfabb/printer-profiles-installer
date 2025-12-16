param(
    [switch]$Sign,
    [string]$PfxPath,
    [securestring]$PfxPassword,
    [pscredential]$PfxCredential,
    [string]$TimestampUrl = "http://timestamp.digicert.com"
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

# Build
if (Test-Path .\dist) { Remove-Item -Recurse -Force .\dist }
if (Test-Path .\build) { Remove-Item -Recurse -Force .\build }

Write-Host "Building one-file EXE via spec..." -ForegroundColor Cyan
.\.venv\Scripts\python.exe -m PyInstaller --noconfirm --clean ".\colorFabb Filament Installer.spec"

$exe = Get-ChildItem .\dist\colorFabbInstaller_v*.exe | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if (-not $exe) { throw "Build produced no dist\\colorFabbInstaller_v*.exe" }

# SHA256
$hash = (Get-FileHash -Algorithm SHA256 $exe.FullName).Hash.ToLowerInvariant()
$shaFile = Join-Path $exe.DirectoryName ($exe.BaseName + ".sha256.txt")
$shaLine = "$hash  $($exe.Name)"
Set-Content -Path $shaFile -Value $shaLine -Encoding ASCII
Write-Host "Wrote SHA256: $shaFile" -ForegroundColor Green

# Optional signing (requires Windows SDK signtool + your code signing certificate)
if ($Sign) {
    if (-not $PfxPath) { throw "-PfxPath is required when -Sign is set" }
    if (-not (Test-Path $PfxPath)) { throw "PFX not found: $PfxPath" }

    # Prefer PSCredential or SecureString. Note: signtool.exe requires a plaintext password argument,
    # so we decrypt only immediately before calling signtool and free the BSTR afterwards.
    if (-not $PfxPassword -and -not $PfxCredential) {
        $PfxPassword = Read-Host -Prompt "Enter PFX password" -AsSecureString
    }

    if ($PfxCredential) {
        $PfxPassword = $PfxCredential.Password
    }

    if (-not $PfxPassword) { throw "PFX password was not provided" }

    $signtool = Get-Command signtool.exe -ErrorAction SilentlyContinue
    if (-not $signtool) {
        throw "signtool.exe not found on PATH. Install Windows SDK (App Certification Kit / SignTool) or add it to PATH."
    }

    Write-Host "Signing EXE..." -ForegroundColor Cyan
    $bstr = [IntPtr]::Zero
    $plain = $null
    try {
        $bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($PfxPassword)
        $plain = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr)
        & $signtool.Source sign /fd SHA256 /f $PfxPath /p $plain /tr $TimestampUrl /td SHA256 $exe.FullName
    }
    finally {
        if ($bstr -ne [IntPtr]::Zero) {
            [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
        }
        $plain = $null
    }

    Write-Host "Verifying signature..." -ForegroundColor Cyan
    & $signtool.Source verify /pa /v $exe.FullName

    Write-Host "Signed: $($exe.Name)" -ForegroundColor Green
}

Write-Host "Done. Output: $($exe.FullName)" -ForegroundColor Green
