param(
  [string]$Version = '5.0.2'
)

$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$dest = Join-Path $root 'upx'
New-Item -ItemType Directory -Force -Path $dest | Out-Null

$zip = Join-Path $dest 'upx.zip'
$url = "https://github.com/upx/upx/releases/download/v$Version/upx-$Version-win64.zip"

Write-Host "Downloading $url"
Invoke-WebRequest -Uri $url -OutFile $zip -UseBasicParsing

Write-Host "Extracting to $dest"
Expand-Archive -LiteralPath $zip -DestinationPath $dest -Force

$upxExe = Get-ChildItem $dest -Recurse -Filter upx.exe | Select-Object -First 1
if (-not $upxExe) {
  throw 'upx.exe not found after extraction'
}

Write-Host "UPX ready: $($upxExe.FullName)"
