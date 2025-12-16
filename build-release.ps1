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

function Find-SignTool {
    $cmd = Get-Command signtool.exe -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }

    $kits = @(
        "C:\Program Files (x86)\Windows Kits\10\bin",
        "C:\Program Files\Windows Kits\10\bin"
    )

    foreach ($base in $kits) {
        if (-not (Test-Path $base)) { continue }
        $found = Get-ChildItem -Path $base -Recurse -Filter signtool.exe -File -ErrorAction SilentlyContinue |
            Sort-Object FullName -Descending |
            Select-Object -First 1
        if ($found) { return $found.FullName }
    }

    return $null
}

# Build
if (Test-Path .\dist) { Remove-Item -Recurse -Force .\dist }
if (Test-Path .\build) { Remove-Item -Recurse -Force .\build }

$pythonExe = Join-Path $root ".venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    $pythonExe = (Get-Command python).Source
}

Write-Host "Building one-file EXE via spec..." -ForegroundColor Cyan
& $pythonExe -m PyInstaller --noconfirm --clean ".\colorFabb Filament Installer.spec"

$exe = Get-ChildItem .\dist\colorFabbInstaller_v*.exe | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if (-not $exe) { throw "Build produced no dist\\colorFabbInstaller_v*.exe" }

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

    $signtoolPath = Find-SignTool
    if (-not $signtoolPath) {
        throw "signtool.exe not found. Install Windows SDK (SignTool) or add it to PATH."
    }

    Write-Host "Signing EXE..." -ForegroundColor Cyan
    $bstr = [IntPtr]::Zero
    $plain = $null
    try {
        $bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($PfxPassword)
        $plain = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr)
        $signOut = & $signtoolPath sign /fd SHA256 /a /f $PfxPath /p $plain /tr $TimestampUrl /td SHA256 $exe.FullName 2>&1 | Out-String
        if ($LASTEXITCODE -ne 0) {
            throw "signtool sign failed (exit $LASTEXITCODE). Output:`n$signOut"
        }
    }
    finally {
        if ($bstr -ne [IntPtr]::Zero) {
            [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
        }
        $plain = $null
    }

    Write-Host "Verifying signature..." -ForegroundColor Cyan
    $verifyOut = & $signtoolPath verify /pa /v $exe.FullName 2>&1 | Out-String
    if ($LASTEXITCODE -ne 0) {
        throw "signtool verify failed (exit $LASTEXITCODE). Output:`n$verifyOut"
    }

    # Ensure the script doesn't exit with a non-zero code from a previous native command
    $global:LASTEXITCODE = 0

    Write-Host "Signed: $($exe.Name)" -ForegroundColor Green
}

# SHA256 (after optional signing, because signing changes the file hash)
$hash = (Get-FileHash -Algorithm SHA256 $exe.FullName).Hash.ToLowerInvariant()
$shaFile = Join-Path $exe.DirectoryName ($exe.BaseName + ".sha256.txt")
$shaLine = "$hash  $($exe.Name)"
Set-Content -Path $shaFile -Value $shaLine -Encoding ASCII
Write-Host "Wrote SHA256: $shaFile" -ForegroundColor Green

Write-Host "Done. Output: $($exe.FullName)" -ForegroundColor Green
