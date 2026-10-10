param([string]$Version = '8.30.1')
$ErrorActionPreference = 'Stop'
if ($Version -notmatch '^\d+\.\d+\.\d+$') { throw 'Invalid release version' }
$tools = Join-Path $PSScriptRoot '../.tools'
New-Item -ItemType Directory -Path $tools -Force | Out-Null
$zipName = "gitleaks_${Version}_windows_x64.zip"
$zipPath = Join-Path $tools $zipName
$checksumPath = Join-Path $tools "gitleaks_${Version}_checksums.txt"
$baseUrl = "https://github.com/gitleaks/gitleaks/releases/download/v$Version"
if (Test-Path -LiteralPath (Join-Path $tools 'gitleaks.exe')) { throw 'Binary already exists; do not overwrite' }
Invoke-WebRequest -Uri "$baseUrl/$zipName" -OutFile $zipPath
Invoke-WebRequest -Uri "$baseUrl/gitleaks_${Version}_checksums.txt" -OutFile $checksumPath
$entry = Get-Content -LiteralPath $checksumPath | Where-Object { $_ -match "\s+$([regex]::Escape($zipName))$" }
if (@($entry).Count -ne 1) { throw 'Missing or ambiguous checksum' }
$expected = ($entry -split '\s+')[0]
$actual = (Get-FileHash -LiteralPath $zipPath -Algorithm SHA256).Hash
if ($actual -ne $expected) { throw 'Release SHA256 mismatch' }
Expand-Archive -LiteralPath $zipPath -DestinationPath $tools
& (Join-Path $tools 'gitleaks.exe') version
if ($LASTEXITCODE -ne 0) { throw 'Installed binary cannot run' }
[pscustomobject]@{ Version = $Version; SHA256 = $actual; Source = "$baseUrl/$zipName" }
